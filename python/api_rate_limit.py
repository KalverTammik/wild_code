"""Shared, cancellable admission and HTTP 429 retries for Kavitro requests.

The maintenance application's rolling-window and mutation pacing rules live at
the transport boundary here so every APIClient instance shares the same budget.
"""

from contextlib import contextmanager
from dataclasses import dataclass, field
from collections import deque
from datetime import timezone
from email.utils import parsedate_to_datetime
import hashlib
import math
import re
import threading
import time
from ..languages.language_manager import LanguageManager
from ..languages.translation_keys import TranslationKeys


class RequestCancelled(Exception):
    """Cancellation before a physical request was sent, never during a write."""

    def __init__(self, message=None):
        super().__init__(message or LanguageManager().translate(TranslationKeys.API_REQUEST_CANCELLED))


class ApiRateLimitError(Exception):
    def __init__(self, delay=0.0, *, retryable=True, reason='rate_limit'):
        self.delay = max(0.0, float(delay))
        self.retryable = bool(retryable)
        self.reason = reason
        key = (TranslationKeys.API_RATE_LIMIT_WAIT if retryable else
               TranslationKeys.API_RATE_LIMIT_REQUEST_TOO_LARGE)
        message = LanguageManager().translate(key)
        super().__init__(message)


_REQUEST_CONTEXT = threading.local()


@contextmanager
def api_request_context(*, cancel_event=None, on_wait=None, retry_rate_limits=True):
    """Keep temporary rejections on the same worker until success/cancellation.

    on_wait(remaining_seconds, reason) executes on the calling worker, at most
    once per second, with a final zero when waiting ends. It must not touch UI.
    """
    previous = getattr(_REQUEST_CONTEXT, 'current', None)
    _REQUEST_CONTEXT.current = (cancel_event, on_wait, retry_rate_limits)
    try:
        yield
    finally:
        _REQUEST_CONTEXT.current = previous


def mutation_cost(document):
    """Count root fields, including aliases and fragments, without a dependency."""
    tokens = re.findall(r'"""[\s\S]*?"""|"(?:\\.|[^"\\])*"|#[^\r\n]*|\.\.\.|[A-Za-z_]\w*|[^\s,]', document or '')
    tokens = [token for token in tokens if token != '\ufeff' and not token.startswith('#')]
    fragments, operations = {}, []

    def skip_balanced(index, opening, closing):
        depth = 0
        while index < len(tokens):
            token = tokens[index]
            index += 1
            depth += (token == opening) - (token == closing)
            if depth == 0:
                break
        return index

    def selection(index):
        fields = []
        index += 1
        while index < len(tokens) and tokens[index] != '}':
            token = tokens[index]
            index += 1
            if token == '...':
                if index < len(tokens) and tokens[index] not in ('on', '@', '{'):
                    fields.append(tokens[index])
                    index += 1
                else:
                    while index < len(tokens) and tokens[index] != '{':
                        if tokens[index] == '(':
                            index = skip_balanced(index, '(', ')')
                        else:
                            index += 1
                    nested, index = selection(index)
                    fields.extend(nested)
            else:
                fields.append(1)
                if index < len(tokens) and tokens[index] == ':':
                    index += 2
            while index < len(tokens) and tokens[index] in ('(', '@'):
                if tokens[index] == '(':
                    index = skip_balanced(index, '(', ')')
                else:
                    index += 2
            if index < len(tokens) and tokens[index] == '{':
                index = skip_balanced(index, '{', '}')
        return fields, index + 1

    index = 0
    while index < len(tokens):
        operation = tokens[index]
        fragment_name = tokens[index + 1] if operation == 'fragment' and index + 1 < len(tokens) else None
        while index < len(tokens) and tokens[index] != '{':
            if tokens[index] == '(':
                index = skip_balanced(index, '(', ')')
            else:
                index += 1
        if index >= len(tokens):
            break
        fields, index = selection(index)
        if operation == 'fragment':
            fragments[fragment_name] = fields
        elif operation == 'mutation':
            operations.extend(fields)

    def count(fields, visited):
        total = 0
        for item in fields:
            if item == 1:
                total += 1
            elif item not in visited:
                total += count(fragments.get(item, []), visited | {item})
        return total

    return count(operations, set())


def _headers(response):
    return {str(key).lower(): str(value).strip() for key, value in response.headers.items()}


def _retry_after(headers, wall_clock):
    raw = headers.get('retry-after')
    if raw is None:
        return None
    try:
        seconds = float(raw)
        return max(0.0, seconds) if math.isfinite(seconds) else None
    except ValueError:
        try:
            when = parsedate_to_datetime(raw)
            if when.tzinfo is None:
                when = when.replace(tzinfo=timezone.utc)
            return max(0.0, when.timestamp() - wall_clock())
        except (ValueError, TypeError, OverflowError):
            return None


@dataclass
class _Budget:
    limit: int
    ceiling: int | None = None
    recent: deque = field(default_factory=deque)
    remaining: int | None = None
    remaining_until: float = 0.0
    blocked_until: float = 0.0
    next_at: float = 0.0
    reserved: int = 0
    last_response_reserved: int = -1


class RateLimitCoordinator:
    """Serialize budget reservations, but never hold the lock across IO/waits.

    Requests are token-specific. Mutation budgets are shared per endpoint, a
    conservative bound even if this process uses different tokens/users/accounts.
    The server's user/account remaining headers also account for other clients.
    """
    def __init__(self, *, clock=time.monotonic, wall_clock=time.time, sleep=time.sleep):
        self._clock, self._wall_clock, self._sleep = clock, wall_clock, sleep
        self._lock = threading.Lock()
        self._budgets = {}

    def _states(self, endpoint, authorization, cost):
        identity = hashlib.sha256((authorization or '').encode('utf-8')).hexdigest()
        request_key = (endpoint, 'request', identity)
        specs = [(request_key, 500 if authorization else 60, None, 1)]
        if cost:
            specs.append(((endpoint, 'mutation'), 30, 40, cost))
            if authorization:
                specs.append(((endpoint, 'account'), 285, 300, cost))
        return [(self._budgets.setdefault(key, _Budget(limit, ceiling)), amount, key[1])
                for key, limit, ceiling, amount in specs]

    def _wait(self, delay, reason):
        context = getattr(_REQUEST_CONTEXT, 'current', None)
        cancel, callback, _ = context or (None, None, False)
        deadline = self._clock() + delay
        reported_at = None
        try:
            while self._clock() < deadline:
                if cancel is not None and cancel.is_set():
                    raise RequestCancelled()
                remaining = deadline - self._clock()
                if callback and (reported_at is None or self._clock() - reported_at >= 1.0):
                    callback(remaining, reason)
                    reported_at = self._clock()
                step = min(0.2, remaining)
                self._sleep(step)
        finally:
            if callback and reported_at is not None:
                callback(0.0, reason)

    def _acquire(self, endpoint, authorization, cost):
        while True:
            context = getattr(_REQUEST_CONTEXT, 'current', None)
            if context and context[0] is not None and context[0].is_set():
                raise RequestCancelled()
            with self._lock:
                now = self._clock()
                states = self._states(endpoint, authorization, cost)
                delay, reason = 0.0, 'pacing'
                for state, amount, kind in states:
                    while state.recent and state.recent[0][0] <= now - 60:
                        state.recent.popleft()
                    if state.remaining_until <= now:
                        state.remaining = None
                    if state.ceiling is not None and amount > state.ceiling:
                        raise ApiRateLimitError(retryable=False)
                    # A single large request can spend its whole server allowance.
                    capacity = max(state.limit, amount)
                    window_used = sum(count for _, count in state.recent)
                    wait = max(0.0, state.blocked_until - now, state.next_at - now)
                    if window_used + amount > capacity and state.recent:
                        wait = max(wait, state.recent[0][0] + 60 - now)
                    if state.remaining is not None and state.remaining < amount:
                        wait = max(wait, state.remaining_until - now)
                    if wait > delay:
                        delay = wait
                    if state.blocked_until > now:
                        reason = 'rate_limit'
                if delay <= 0:
                    permit = []
                    for state, amount, kind in states:
                        state.recent.append((now, amount))
                        state.reserved += amount
                        permit.append((state, kind, state.reserved))
                        if state.remaining is not None:
                            state.remaining = max(0, state.remaining - amount)
                        if kind == 'mutation':
                            state.next_at = now + 60.0 * amount / state.limit
                    return permit
            self._wait(delay, reason)

    def _record(self, permit, headers, block_for=None, mutation_rejection=False):
        prefixes = {'request': 'x-ratelimit', 'mutation': 'x-ratelimit-mutation',
                    'account': 'x-ratelimit-mutation-account'}
        with self._lock:
            now = self._clock()
            for state, kind, reserved in permit:
                prefix = prefixes[kind]
                if reserved >= state.last_response_reserved:
                    try:
                        ceiling = int(headers[prefix + '-limit'])
                        if ceiling > 0:
                            reserve = min(ceiling - 1, max(1, math.ceil(ceiling * 0.05)))
                            state.limit = min(30, ceiling - reserve) if kind == 'mutation' else ceiling - reserve
                            state.ceiling = ceiling
                    except (KeyError, ValueError):
                        pass
                    ceiling = state.ceiling or state.limit
                    reserve = min(ceiling - 1, max(1, math.ceil(ceiling * 0.05)))
                    try:
                        # Permit order rejects stale responses; subtract requests
                        # admitted since this one before accepting a fresh window.
                        later_reserved = state.reserved - reserved
                        state.remaining = max(0, int(headers[prefix + '-remaining']) - reserve - later_reserved)
                        state.remaining_until = now + 60
                    except (KeyError, ValueError):
                        pass
                    state.last_response_reserved = reserved
                affected = kind != 'request' if mutation_rejection else kind == 'request'
                if block_for is not None and affected:
                    state.blocked_until = max(state.blocked_until, now + block_for)
                    # Retry-After is more precise than the conservative header window.
                    state.remaining_until = state.blocked_until

    def send(self, send_request, *, endpoint, authorization, cost):
        rejected = 0
        while True:
            permit = self._acquire(endpoint, authorization, cost)
            response = send_request()
            headers = _headers(response)
            if response.status_code != 429:
                self._record(permit, headers)
                return response
            try:
                body = response.json()
            except (ValueError, TypeError):
                body = {}
            mutation_rejection = isinstance(body, dict) and bool(body.get('errors'))
            retry_after = _retry_after(headers, self._wall_clock)
            if mutation_rejection and retry_after is None:
                self._record(permit, headers)
                raise ApiRateLimitError(retryable=False)
            delay = max(0.1, retry_after if retry_after is not None else min(60.0, 2.0 ** min(rejected + 1, 6)))
            self._record(permit, headers, block_for=delay,
                         mutation_rejection=mutation_rejection)
            rejected += 1
            context = getattr(_REQUEST_CONTEXT, 'current', None)
            if context and not context[2]:
                raise ApiRateLimitError(delay)
            # The rejected request was never executed. Retrying it is independent
            # of retry_network=False, which protects writes with uncertain results.
            self._wait(delay, 'rate_limit')


PROCESS_RATE_LIMITER = RateLimitCoordinator()
