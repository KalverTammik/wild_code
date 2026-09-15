from __future__ import annotations

import time

from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot

from .MainAddProperties import BackendPropertyVerifier
from .property_import_decisions import classify_property_import
from ....languages.translation_keys import TranslationKeys as K
from ....Logs.python_fail_logger import PythonFailLogger


class BackendVerifyWorker(QObject):
    """Background worker for verifying backend state per cadastral tunnus.

    Emits row-by-row results so UI can update progressively.
    """

    rowResult = pyqtSignal(int, str, dict)
    finished = pyqtSignal(dict)

    def __init__(
        self,
        rows: list[tuple[int, str, str]],
        *,
        source: str,
        import_context_by_tunnus: dict,
    ):
        super().__init__()
        self._rows = rows
        self._source = source
        self._import_context_by_tunnus = import_context_by_tunnus
        self._stop = False

        total = len(rows or [])
        if total <= 50:
            self._sleep_every = 0
            self._sleep_secs = 0.0
        elif total <= 150:
            self._sleep_every = 20
            self._sleep_secs = 0.03
        else:
            self._sleep_every = 25
            self._sleep_secs = 0.05
        self._no_sleep_until = 50  # process first chunk quickly

    def stop(self) -> None:
        self._stop = True

    @pyqtSlot()
    def run(self) -> None:
        ok_fresh: list[str] = []
        missing_backend: list[str] = []
        archived_only_backend: list[str] = []
        outdated_backend: list[str] = []
        errors: list[dict] = []

        call_count = 0

        for row, tunnus, import_muudet in self._rows:
            if self._stop:
                break

            try:
                backend_info = BackendPropertyVerifier.verify_properties_by_cadastral_number(tunnus)
            except Exception as e:
                errors.append({"tunnus": tunnus, "error": str(e)})
                self.rowResult.emit(
                    row,
                    tunnus,
                    {
                        "attention": True,
                        "causes": ["backend lookup failed"],
                        "backend_info": None,
                    },
                )
                continue

            context = self._import_context_by_tunnus[tunnus]
            decision = classify_property_import(context['data'], import_muudet, context['main_date'],
                                                backend_info or {})
            attention_causes: list[str] = []
            if decision['action'] == 'error':
                attention_causes.append(K.ATTENTION_CAUSE_BACKEND_LOOKUP_FAILED)
            elif decision['action'] == 'needs_decision':
                attention_causes.append(decision['reason'])
                if backend_info.get('archived_only'):
                    archived_only_backend.append(tunnus)
            elif decision['action'] == 'create':
                missing_backend.append(tunnus)
                attention_causes.append(K.ATTENTION_CAUSE_MISSING_BACKEND)
            elif decision['import_newer']:
                outdated_backend.append(tunnus)
                attention_causes.append(K.ATTENTION_CAUSE_IMPORT_NEWER)
            else:
                ok_fresh.append(tunnus)

            self.rowResult.emit(
                row,
                tunnus,
                {
                    "attention": bool(attention_causes),
                    "causes": attention_causes,
                    "decision": decision,
                    "backend_info": backend_info if isinstance(backend_info, dict) else None,
                },
            )

            call_count += 1
            if (
                not self._stop
                and self._sleep_every
                and call_count > self._no_sleep_until
                and call_count % self._sleep_every == 0
            ):
                try:
                    time.sleep(self._sleep_secs)
                except Exception as exc:
                    PythonFailLogger.log_exception(
                        exc,
                        module="property",
                        event="backend_verify_sleep_failed",
                    )

        self.finished.emit(
            {
                "source": self._source,
                "ok_fresh": ok_fresh,
                "missing_backend": missing_backend,
                "archived_only": archived_only_backend,
                "outdated_backend": outdated_backend,
                "errors": errors,
                "stopped": bool(self._stop),
            }
        )
