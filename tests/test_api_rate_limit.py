import os
import sys
import threading
import unittest
from email.utils import formatdate
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from qgis.core import QgsApplication
from Kavitro_dev.python import api_client, api_rate_limit as module


class FakeClock:
    def __init__(self):
        self.value = 100.0
        self.waits = []

    def now(self):
        return self.value

    def wall(self):
        return 1700000000.0 + self.value

    def sleep(self, delay):
        self.waits.append(delay)
        self.value += delay


class FakeResponse:
    def __init__(self, status=200, headers=None, body=None):
        self.status_code = status
        self.headers = headers or {}
        self.body = {'data': {'id': 'saved'}} if body is None else body

    def json(self):
        return self.body


class ApiRateLimitTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QgsApplication.instance() or QgsApplication([], False)

    def setUp(self):
        self.clock = FakeClock()
        self.limiter = module.RateLimitCoordinator(
            clock=self.clock.now, wall_clock=self.clock.wall, sleep=self.clock.sleep)
        self.enterContext(patch.object(module, 'PROCESS_RATE_LIMITER', self.limiter))
        self.client = api_client.APIClient(session_manager=Mock(get_token=Mock(return_value='private-token')))
        self.worker = self.enterContext(patch.object(api_client.QThread, 'currentThread', return_value=object()))

    def send(self, response=None, *, cost=1, authorization='Bearer private-token', is_main_thread=False):
        return self.limiter.send(lambda: response or FakeResponse(), endpoint='https://example.test/graphql',
            authorization=authorization, cost=cost, is_main_thread=is_main_thread)

    def test_counts_root_aliases_fragments_and_multiple_operations(self):
        query = '''
        # mutation { ignored }
        fragment Changes on Mutation { first: update(input: {x: "mutation { fake }"}) { id } }
        mutation Save($input: Input = {nested: {x: 1}}) {
          ...Changes
          second: update(input: $input) { id nested { name } }
          ... on Mutation { third: update(input: $input) { id } }
        }
        query { properties { id } }
        mutation Another { fourth: update { id } }
        '''
        self.assertEqual(module.mutation_cost(query), 4)
        self.assertEqual(module.mutation_cost('query { mutation { id } }'), 0)
        self.assertEqual(module.mutation_cost('{ properties { id } }'), 0)
        self.assertEqual(module.mutation_cost('\ufeffmutation { update { id } }'), 1)

    def test_mutations_are_paced_at_thirty_per_minute_across_clients(self):
        starts = []
        def respond(*args, **kwargs):
            starts.append(self.clock.now())
            return FakeResponse()
        other = api_client.APIClient(session_manager=Mock(get_token=Mock(return_value='private-token')))
        with patch.object(api_client.requests, 'post', side_effect=respond):
            for index in range(32):
                (self.client if index % 2 else other).send_query('mutation { update { id } }')
        self.assertEqual(len(starts), 32)
        self.assertTrue(all(later - earlier >= 1.999 for earlier, later in zip(starts, starts[1:])))
        self.assertGreaterEqual(starts[30] - starts[0], 60.0)
        self.assertNotIn('private-token', repr(self.limiter._budgets))

    def test_multi_field_mutation_spends_all_fields(self):
        self.send(cost=3)
        self.send(cost=1)
        self.assertAlmostEqual(self.clock.now(), 106.0)

    def test_lower_server_mutation_ceiling_changes_capacity_and_pacing(self):
        response = FakeResponse(headers={'X-RateLimit-Mutation-Limit': '10',
                                         'X-RateLimit-Mutation-Remaining': '9'})
        self.send(response)
        self.send()
        before = self.clock.now()
        self.send()
        self.assertAlmostEqual(self.clock.now() - before, 60 / 9)

    def test_server_window_replenishment_is_accepted(self):
        self.send(FakeResponse(headers={'X-RateLimit-Limit': '500', 'X-RateLimit-Remaining': '27'}), cost=0)
        self.send(FakeResponse(headers={'X-RateLimit-Limit': '500', 'X-RateLimit-Remaining': '499'}), cost=0)
        self.send(cost=0)
        self.send(cost=0)
        self.assertEqual(self.clock.now(), 100.0)

    def test_out_of_order_responses_cannot_replenish_newer_reservations(self):
        entered, release = threading.Event(), threading.Event()
        errors = []
        def first_request():
            entered.set()
            if not release.wait(2):
                raise RuntimeError('second request did not complete')
            return FakeResponse(headers={'X-RateLimit-Limit': '500', 'X-RateLimit-Remaining': '499'})
        def first_thread():
            try:
                self.limiter.send(first_request, endpoint='test', authorization='token', cost=0, is_main_thread=False)
            except Exception as exc:
                errors.append(exc)
        thread = threading.Thread(target=first_thread)
        thread.start()
        try:
            self.assertTrue(entered.wait(2))
            self.limiter.send(lambda: FakeResponse(headers={
                'X-RateLimit-Limit': '500', 'X-RateLimit-Remaining': '480'}),
                endpoint='test', authorization='token', cost=0, is_main_thread=False)
        finally:
            release.set()
            thread.join(2)
        self.assertFalse(thread.is_alive())
        self.assertFalse(errors)
        state = next(state for key, state in self.limiter._budgets.items() if key[1] == 'request')
        self.assertEqual(state.remaining, 455)

    def test_mutation_allowance_is_shared_across_concurrent_threads(self):
        ready = threading.Barrier(3)
        timestamps, errors = [], []
        def send_request():
            timestamps.append(self.clock.now())
            ready.wait(2)
            return FakeResponse()
        def run():
            try:
                self.limiter.send(send_request, endpoint='test', authorization='token', cost=1, is_main_thread=False)
            except Exception as exc:
                errors.append(exc)
        threads = [threading.Thread(target=run) for _ in range(3)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(3)
        self.assertFalse(any(thread.is_alive() for thread in threads))
        self.assertFalse(errors)
        self.assertEqual(sorted(timestamps), [100.0, 102.0, 104.0])

    def test_large_valid_request_can_exceed_local_thirty_field_safety_budget(self):
        self.send(cost=31)
        self.send()
        self.assertAlmostEqual(self.clock.now(), 162.0)

    def test_request_over_known_mutation_ceiling_is_rejected_without_wait(self):
        with self.assertRaises(module.ApiRateLimitError) as raised:
            self.send(cost=41)
        self.assertFalse(raised.exception.retryable)
        self.assertFalse(self.clock.waits)

    def test_lower_account_ceiling_rejects_oversized_request(self):
        self.send(FakeResponse(headers={'X-RateLimit-Mutation-Account-Limit': '2',
                                       'X-RateLimit-Mutation-Account-Remaining': '1'}))
        with self.assertRaises(module.ApiRateLimitError) as raised:
            self.send(cost=3)
        self.assertFalse(raised.exception.retryable)

    def test_mutation_cooldown_does_not_block_read_queries(self):
        self.worker.return_value = self.app.thread()
        responses = [FakeResponse(429, {'Retry-After': '37'},
            {'errors': [{'extensions': {'category': 'TOO_MANY_MUTATIONS'}}]}), FakeResponse()]
        with patch.object(api_client.requests, 'post', side_effect=responses) as post:
            with self.assertRaises(module.ApiRateLimitError):
                self.client.send_query('mutation { update { id } }')
            self.client.send_query('query { properties { id } }')
        self.assertEqual(post.call_count, 2)
        self.assertFalse(self.clock.waits)

    def test_request_cooldown_is_not_shared_across_different_tokens(self):
        self.worker.return_value = self.app.thread()
        other = api_client.APIClient(session_manager=Mock(get_token=Mock(return_value='another-token')))
        with patch.object(api_client.requests, 'post', side_effect=[
                FakeResponse(429, {'Retry-After': '37'}, {}), FakeResponse()]) as post:
            with self.assertRaises(module.ApiRateLimitError):
                self.client.send_query('query { properties { id } }')
            other.send_query('mutation { update { id } }')
        self.assertEqual(post.call_count, 2)
        self.assertFalse(self.clock.waits)

    def test_unexpected_mutation_rejection_on_query_still_waits(self):
        responses = [FakeResponse(429, {'Retry-After': '7'}, {
            'errors': [{'extensions': {'category': 'TOO_MANY_MUTATIONS'}}]}), FakeResponse()]
        with patch.object(api_client.requests, 'post', side_effect=responses):
            self.client.send_query('query { properties { id } }')
        self.assertAlmostEqual(self.clock.now(), 107.0)

    def test_request_header_reserve_waits_then_recovers(self):
        self.send(FakeResponse(headers={'X-RateLimit-Limit': '20', 'X-RateLimit-Remaining': '1'}), cost=0)
        self.send(cost=0)
        self.assertAlmostEqual(self.clock.now(), 160.0)

    def test_account_budget_is_shared_but_request_token_budgets_are_separate(self):
        self.send(FakeResponse(headers={'X-RateLimit-Mutation-Account-Limit': '300',
                                       'X-RateLimit-Mutation-Account-Remaining': '0'}))
        self.send(cost=0, authorization='Bearer second-token')
        self.assertEqual(self.clock.now(), 100.0)
        self.send(authorization='Bearer second-token')
        self.assertAlmostEqual(self.clock.now(), 160.0)

    def test_429_retries_same_create_even_when_network_retry_disabled(self):
        body = {'query': 'mutation { createProperty { id } }', 'variables': {'input': {'name': 'one'}}}
        responses = [FakeResponse(429, {'Retry-After': '7'}, {'message': 'Too Many Requests.'}), FakeResponse()]
        with patch.object(api_client.requests, 'post', side_effect=responses) as post:
            result = self.client.send_query(body['query'], body['variables'], retry_network=False)
        self.assertEqual(result, {'id': 'saved'})
        self.assertEqual(post.call_count, 2)
        self.assertEqual([call.kwargs['json'] for call in post.call_args_list], [body, body])
        self.assertAlmostEqual(self.clock.now(), 107.0)

    def test_mutation_429_uses_retry_after_and_does_not_replay_earlier_write(self):
        responses = [FakeResponse(), FakeResponse(429, {'Retry-After': '4'},
            {'errors': [{'extensions': {'category': 'TOO_MANY_MUTATIONS'}}]}), FakeResponse()]
        with patch.object(api_client.requests, 'post', side_effect=responses) as post:
            self.client.send_query('mutation { createProperty { id } }', retry_network=False)
            self.client.send_query('mutation { updatePropertyIntendedUses { id } }')
        queries = [call.kwargs['json']['query'] for call in post.call_args_list]
        self.assertEqual(queries[0], 'mutation { createProperty { id } }')
        self.assertEqual(queries[1:], ['mutation { updatePropertyIntendedUses { id } }'] * 2)
        self.assertAlmostEqual(self.clock.now(), 106.0)

    def test_retry_after_http_date_is_honoured_case_insensitively(self):
        retry_date = formatdate(self.clock.wall() + 12, usegmt=True)
        send = Mock(side_effect=[FakeResponse(429, {'rEtRy-AfTeR': retry_date}, {}), FakeResponse()])
        self.limiter.send(send, endpoint='test', authorization=None, cost=0, is_main_thread=False)
        self.assertAlmostEqual(self.clock.now(), 112.0)

    def test_plain_429_without_retry_after_uses_backoff(self):
        send = Mock(side_effect=[FakeResponse(429, body={}), FakeResponse(429, body={}), FakeResponse()])
        self.limiter.send(send, endpoint='test', authorization=None, cost=0, is_main_thread=False)
        self.assertAlmostEqual(self.clock.now(), 106.0)

    def test_permanent_oversized_mutation_is_not_retried(self):
        response = FakeResponse(429, body={'errors': [{'message': 'must-not-appear-in-exception',
            'extensions': {'category': 'TOO_MANY_MUTATIONS'}}]})
        with patch.object(api_client.requests, 'post', return_value=response) as post:
            with self.assertRaises(module.ApiRateLimitError) as raised:
                self.client.send_query('mutation { update { id } }')
        self.assertFalse(raised.exception.retryable)
        self.assertNotIn('must-not-appear', str(raised.exception))
        self.assertEqual(post.call_count, 1)
        self.assertFalse(self.clock.waits)

    def test_main_thread_never_waits_on_429(self):
        self.worker.return_value = self.app.thread()
        with patch.object(api_client.requests, 'post', return_value=FakeResponse(429, {'Retry-After': '37'}, {})) as post:
            with self.assertRaises(module.ApiRateLimitError) as raised:
                self.client.send_query('mutation { update { id } }')
        self.assertEqual(raised.exception.delay, 37.0)
        self.assertEqual(post.call_count, 1)
        self.assertFalse(self.clock.waits)

    def test_legacy_main_thread_writes_do_not_fail_due_to_proactive_pacing(self):
        self.worker.return_value = self.app.thread()
        with patch.object(api_client.requests, 'post', return_value=FakeResponse()) as post:
            self.client.send_query('mutation { createProperty { id } }')
            self.client.send_query('mutation { updatePropertyIntendedUses { id } }')
        self.assertEqual(post.call_count, 2)
        self.assertFalse(self.clock.waits)

    def test_context_retries_more_than_five_rejections_until_success(self):
        response = FakeResponse(429, {'Retry-After': '1'}, {})
        waiting = []
        with module.api_request_context(on_wait=lambda seconds, reason: waiting.append((seconds, reason))):
            with patch.object(api_client.requests, 'post', side_effect=[response] * 6 + [FakeResponse()]) as post:
                self.client.send_query('mutation { createProperty { id } }', retry_network=False)
        self.assertEqual(post.call_count, 7)
        self.assertTrue(any(reason == 'rate_limit' for seconds, reason in waiting))
        self.assertEqual(waiting[-1][0], 0)

    def test_without_context_repeated_429_is_bounded(self):
        with patch.object(api_client.requests, 'post', return_value=FakeResponse(429, {'Retry-After': '1'}, {})) as post:
            with self.assertRaises(module.ApiRateLimitError):
                self.client.send_query('query { properties { id } }')
        self.assertEqual(post.call_count, 5)

    def test_cancellation_during_wait_sends_no_retry(self):
        cancelled = threading.Event()
        waits = []
        def waiting(seconds, reason):
            waits.append(seconds)
            if seconds > 0:
                cancelled.set()
        with module.api_request_context(cancel_event=cancelled, on_wait=waiting):
            with patch.object(api_client.requests, 'post', return_value=FakeResponse(429, {'Retry-After': '37'}, {})) as post:
                with self.assertRaises(module.RequestCancelled):
                    self.client.send_query('mutation { createProperty { id } }', retry_network=False)
        self.assertEqual(post.call_count, 1)
        self.assertEqual(waits[-1], 0)
        self.assertLessEqual(self.clock.now(), 100.21)

    def test_timeout_and_500_do_not_retry_uncertain_create(self):
        for failure in (api_client.requests_exceptions.Timeout('lost'), FakeResponse(503)):
            with self.subTest(failure=type(failure).__name__):
                with patch.object(api_client.requests, 'post', side_effect=[failure]) as post:
                    with self.assertRaises(Exception):
                        self.client.send_query('mutation { createProperty { id } }', retry_network=False)
                self.assertEqual(post.call_count, 1)

    def test_graphql_validation_error_is_not_retried(self):
        with patch.object(api_client.requests, 'post', return_value=FakeResponse(body={
                'errors': [{'message': 'Invalid value'}]})) as post:
            with self.assertRaisesRegex(Exception, 'Invalid value'):
                self.client.send_query('mutation { update { id } }')
        self.assertEqual(post.call_count, 1)

    def test_multipart_retries_same_complete_file_with_shared_budget(self):
        contents = []
        def post(*args, **kwargs):
            contents.append(kwargs['files']['0'][1].read())
            return FakeResponse(429, {'Retry-After': '3'}, {}) if len(contents) == 1 else FakeResponse()
        with TemporaryDirectory() as directory:
            path = Path(directory) / 'upload.txt'
            path.write_bytes(b'complete upload contents')
            with patch.object(api_client.requests, 'post', side_effect=post):
                self.client.send_multipart_query('mutation Upload($file: Upload!) { upload(file: $file) { id } }',
                    file_variables={'file': str(path)})
            before = self.clock.now()
        self.assertEqual(contents, [b'complete upload contents'] * 2)
        with patch.object(api_client.requests, 'post', return_value=FakeResponse()):
            self.client.send_query('mutation { update { id } }')
        self.assertGreaterEqual(self.clock.now() - before, 2.0)

    def test_context_is_nested_and_thread_local(self):
        calls = []
        outer = lambda *args: calls.append('outer')
        with module.api_request_context(on_wait=outer):
            with module.api_request_context(on_wait=lambda *args: calls.append('inner')):
                self.send()
                self.send()
            self.send()
        self.assertEqual(calls[:2], ['inner', 'inner'])
        self.assertEqual(calls[-1], 'outer')
        self.assertIsNone(getattr(module._REQUEST_CONTEXT, 'current', None))


if __name__ == '__main__':
    unittest.main()
