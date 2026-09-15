"""Exercise reviewed property writes through the real HTTP retry boundary."""

import os
import sys
import threading
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
if os.environ.get('QGIS_PREFIX_PATH'):
    sys.path.append(str(Path(os.environ['QGIS_PREFIX_PATH']) / 'python' / 'plugins'))

from PyQt5.QtGui import QFont, QFontDatabase
from qgis.core import QgsApplication

from Kavitro_dev.modules.Property.FlowControllers import AddBatchRunner as property_flow
from Kavitro_dev.python import api_client, api_rate_limit


class FakeResponse:
    def __init__(self, status_code, data=None, headers=None, errors=None):
        self.status_code = status_code
        self.headers = headers or {}
        self._body = {'errors': errors} if errors is not None else {'data': data or {}}
        self.text = 'Response body must not enter a user-facing error.'

    def json(self):
        return self._body


class FakeClock:
    def __init__(self):
        self.seconds = 1000.0

    def now(self):
        return self.seconds

    def sleep(self, delay):
        self.seconds += delay


class PropertyRateRetryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QgsApplication.instance() or QgsApplication([], False)
        QgsApplication.initQgis()
        if not QFontDatabase().families():
            QFontDatabase.addApplicationFont('C:/Windows/Fonts/segoeui.ttf')
            cls.app.setFont(QFont('Segoe UI', 9))

    def setUp(self):
        self.data = {
            'cadastralUnit': {'number': '34202:001:0091'},
            'address': {'street': 'Test property'},
        }
        self.uses = [{'type': 'RESIDENTIAL', 'percentage': 100}]
        self.lookup = self.enterContext(patch.object(
            property_flow.BackendPropertyVerifier,
            'verify_properties_by_cadastral_number',
            return_value={'exists': False},
        ))
        session = Mock()
        session.get_token.return_value = 'offline-integration-test-token'
        self.enterContext(patch.object(api_client, 'SessionManager', return_value=session))
        self.enterContext(patch.object(
            api_client.GraphQLSettings, 'graphql_endpoint',
            return_value='https://offline.example.invalid/graphql',
        ))
        self.enterContext(patch.object(api_client.QThread, 'currentThread', return_value=object()))
        self.log = self.enterContext(patch.object(property_flow.PythonFailLogger, 'log_exception'))
        self.post = self.enterContext(patch.object(api_client.requests, 'post'))
        self.waits = []
        self.clock = FakeClock()
        self.enterContext(patch.object(
            api_rate_limit, 'PROCESS_RATE_LIMITER',
            api_rate_limit.RateLimitCoordinator(
                clock=self.clock.now, wall_clock=self.clock.now, sleep=self.clock.sleep,
            ),
        ))

    def run_reviewed(self, responses):
        responses = iter(responses)
        self.sent_at = []

        def send(*_args, **_kwargs):
            self.sent_at.append(self.clock.now())
            return next(responses)

        self.post.side_effect = send
        with api_rate_limit.api_request_context(
            on_wait=lambda remaining, reason: self.waits.append((remaining, reason)),
            retry_rate_limits=True,
        ):
            result = property_flow.apply_reviewed_backend(self.data, self.uses, None, None)
        self.assertIsNone(result)
        return [call.kwargs['json'] for call in self.post.call_args_list]

    @staticmethod
    def saved(field, record_id='backend-1'):
        return FakeResponse(200, {field: {'id': record_id}})

    @staticmethod
    def throttled():
        return FakeResponse(429, headers={'Retry-After': '3'},
                            errors=[{'message': 'Mutation request limit reached'}])

    def assert_only_intended_uses_retried(self, calls, expected_attempts):
        self.assertEqual(len(calls), expected_attempts + 1)
        self.assertIn('createProperty', calls[0]['query'])
        self.assertEqual(calls[0]['variables'], {'input': self.data})
        intended = calls[1:]
        self.assertTrue(all('updatePropertyIntendedUses' in call['query'] for call in intended))
        self.assertTrue(all(call == intended[0] for call in intended))
        self.assertEqual(intended[0]['variables'], {
            'input': {'id': 'backend-1', 'uses': self.uses},
        })
        self.lookup.assert_called_once_with(self.data['cadastralUnit']['number'])

    def test_intended_uses_429_retries_that_stage_without_recreating_property(self):
        calls = self.run_reviewed([
            self.saved('createProperty'), self.throttled(),
            self.saved('updatePropertyIntendedUses'),
        ])
        self.assert_only_intended_uses_retried(calls, 2)
        self.assertTrue(any(remaining > 0 and reason == 'rate_limit'
                            for remaining, reason in self.waits))
        self.assertGreaterEqual(self.sent_at[2] - self.sent_at[1], 3.0)

    def test_fifty_properties_complete_across_multiple_rate_windows(self):
        created, uses_saved, attempts = [], [], []
        rejected = set()
        def send(*args, **kwargs):
            payload = kwargs['json']
            field = 'updatePropertyIntendedUses' if 'updatePropertyIntendedUses' in payload['query'] else 'createProperty'
            data = payload['variables']['input']
            identifier = data['id'] if field == 'updatePropertyIntendedUses' else data['cadastralUnit']['number']
            key = (field, identifier)
            attempts.append(self.clock.now())
            if int(identifier) % 7 == 0 and key not in rejected:
                rejected.add(key)
                return self.throttled()
            (created if field == 'createProperty' else uses_saved).append(identifier)
            return self.saved(field, identifier)
        self.post.side_effect = send
        for index in range(50):
            data = {**self.data, 'cadastralUnit': {'number': str(index)}}
            property_flow.apply_reviewed_backend(data, self.uses, None, None)
        self.assertEqual(created, [str(index) for index in range(50)])
        self.assertEqual(uses_saved, created)
        self.assertEqual(len(attempts), 116)
        self.assertTrue(all(b - a >= 1.999 for a, b in zip(attempts, attempts[1:])))

    def test_six_rate_rejections_keep_current_property_until_server_accepts_it(self):
        calls = self.run_reviewed([
            self.saved('createProperty'),
            *[self.throttled() for _ in range(6)],
            self.saved('updatePropertyIntendedUses'),
        ])
        self.assert_only_intended_uses_retried(calls, 7)
        self.assertTrue(all(later - earlier >= 3.0
                            for earlier, later in zip(self.sent_at[1:], self.sent_at[2:])))

    def test_create_429_retries_despite_network_retries_being_disabled(self):
        calls = self.run_reviewed([
            self.throttled(), self.saved('createProperty'),
            self.saved('updatePropertyIntendedUses'),
        ])
        self.assertEqual(len(calls), 3)
        self.assertEqual(calls[0], calls[1])
        self.assertIn('createProperty', calls[0]['query'])
        self.assertIn('updatePropertyIntendedUses', calls[2]['query'])

    def test_update_intended_uses_429_does_not_repeat_property_update(self):
        self.lookup.return_value = {
            'exists': True,
            'property': {
                'id': 'backend-1', 'cadastralUnitNumber': self.data['cadastralUnit']['number'],
                'displayAddress': self.data['address']['street'],
            },
        }
        calls = self.run_reviewed([
            self.saved('updateProperty'), self.throttled(),
            self.saved('updatePropertyIntendedUses'),
        ])
        self.assertEqual(len(calls), 3)
        self.assertIn('updateProperty(', calls[0]['query'])
        self.assertEqual(calls[1], calls[2])
        self.assertIn('updatePropertyIntendedUses', calls[1]['query'])
        self.assertFalse(any('createProperty' in call['query'] for call in calls))

    def test_permanent_mutation_429_without_retry_after_is_not_looped(self):
        self.post.return_value = FakeResponse(429, errors=[{'message': 'Mutation allowance exceeded'}])
        with api_rate_limit.api_request_context(retry_rate_limits=True):
            with self.assertRaises(RuntimeError) as raised:
                property_flow.apply_reviewed_backend(self.data, self.uses, None, None)
        self.assertEqual(self.post.call_count, 1)
        self.assertIsInstance(raised.exception.__cause__, api_rate_limit.ApiRateLimitError)
        self.assertFalse(raised.exception.__cause__.retryable)
        self.assertNotIn(self.post.return_value.text, str(raised.exception))

    def test_cancel_during_intended_uses_cooldown_does_not_resend_or_claim_success(self):
        cancel = threading.Event()
        self.post.side_effect = [self.saved('createProperty'), self.throttled()]

        def on_wait(remaining, reason):
            self.waits.append((remaining, reason))
            if remaining > 0 and reason == 'rate_limit':
                cancel.set()

        with api_rate_limit.api_request_context(cancel_event=cancel, on_wait=on_wait):
            with self.assertRaises(api_rate_limit.RequestCancelled):
                property_flow.apply_reviewed_backend(self.data, self.uses, None, None)
        self.assertTrue(cancel.is_set())
        self.assertEqual(self.post.call_count, 2)
        self.assertIn('createProperty', self.post.call_args_list[0].kwargs['json']['query'])
        self.assertIn('updatePropertyIntendedUses', self.post.call_args_list[1].kwargs['json']['query'])
        self.assertIn((0.0, 'rate_limit'), self.waits)

    def test_lost_create_response_is_reported_without_blind_creation_retry(self):
        self.post.side_effect = api_client.requests_exceptions.Timeout('Response was lost')
        with api_rate_limit.api_request_context(retry_rate_limits=True):
            with self.assertRaises(RuntimeError):
                property_flow.apply_reviewed_backend(self.data, self.uses, None, None)
        self.assertEqual(self.post.call_count, 1)
        self.assertEqual(self.log.call_args.kwargs['extra']['stage'], 'createProperty')

    def test_missing_create_id_never_starts_intended_uses(self):
        self.post.return_value = FakeResponse(200, {'createProperty': {}})
        with api_rate_limit.api_request_context(retry_rate_limits=True):
            with self.assertRaises(RuntimeError):
                property_flow.apply_reviewed_backend(self.data, self.uses, None, None)
        self.assertEqual(self.post.call_count, 1)

    def test_missing_or_wrong_intended_uses_id_is_not_success(self):
        for intended in ({}, {'id': 'different-property'}):
            with self.subTest(intended=intended):
                self.post.reset_mock()
                self.post.side_effect = [
                    self.saved('createProperty'),
                    FakeResponse(200, {'updatePropertyIntendedUses': intended}),
                ]
                with api_rate_limit.api_request_context(retry_rate_limits=True):
                    with self.assertRaises(RuntimeError):
                        property_flow.apply_reviewed_backend(self.data, self.uses, None, None)
                self.assertEqual(self.post.call_count, 2)
                self.assertEqual(self.log.call_args.kwargs['extra']['stage'], 'updatePropertyIntendedUses')
                self.assertEqual(self.log.call_args.kwargs['extra']['item_id'], 'backend-1')

    def test_missing_or_wrong_update_id_stops_before_intended_uses(self):
        self.lookup.return_value = {
            'exists': True,
            'property': {
                'id': 'backend-1', 'cadastralUnitNumber': self.data['cadastralUnit']['number'],
                'displayAddress': self.data['address']['street'],
            },
        }
        for updated in ({}, {'id': 'different-property'}):
            with self.subTest(updated=updated):
                self.post.reset_mock()
                self.post.return_value = FakeResponse(200, {'updateProperty': updated})
                with api_rate_limit.api_request_context(retry_rate_limits=True):
                    with self.assertRaises(RuntimeError):
                        property_flow.apply_reviewed_backend(self.data, self.uses, None, None)
                self.assertEqual(self.post.call_count, 1)
                self.assertEqual(self.log.call_args.kwargs['extra']['stage'], 'updateProperty')


if __name__ == '__main__':
    unittest.main()
