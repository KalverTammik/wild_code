class TokenMixin:
    """Explicit token lifecycle contract for modules."""

    def __init__(self) -> None:
        self._active_token = 0
        self._activated = False

    def mark_activated(self, token: int | None = None) -> int:
        if token is None:
            self._active_token += 1
        else:
            self._active_token = token
        self._activated = True
        return self._active_token

    def prepare_activation(self, token: int) -> int:
        self._active_token = token
        self._activated = False
        return self._active_token

    def mark_deactivated(self, *, bump_token: bool = True) -> int:
        if bump_token:
            self._active_token = (self._active_token or 0) + 1
        self._activated = False
        return self._active_token

    def bump_token(self) -> int:
        self._active_token = (self._active_token or 0) + 1
        return self._active_token

    def is_token_active(self, token: int | None) -> bool:
        if token is None:
            return bool(self._activated)
        return bool(self._activated) and token == self._active_token
