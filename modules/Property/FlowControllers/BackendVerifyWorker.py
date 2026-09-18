from __future__ import annotations

from threading import Event

from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot

from .MainAddProperties import BackendPropertyVerifier
from .property_import_decisions import classify_property_import
from ....languages.translation_keys import TranslationKeys as K
from ....Logs.python_fail_logger import PythonFailLogger
from ....python.api_rate_limit import RequestCancelled, api_request_context


class BackendVerifyWorker(QObject):
    """Background worker for verifying backend state per cadastral tunnus.

    Emits row-by-row results so UI can update progressively. Requests are paced by
    the shared process rate limiter; stop() also interrupts its waits, so a cancelled
    run releases the request budget at once instead of after the pause.

    ``finished`` is the only signal the UI uses to leave its busy state, so it is
    emitted for every run, including one that ends in an unexpected error.

    Two modes share the same paced request loop:

    ``MODE_VERIFY``
        The import check. Every row is compared against its import context and gets a
        decision.
    ``MODE_LOOKUP``
        The archive plan. It only needs to know what the backend holds for a cadastral
        number, so no decision is computed and no import context is required.
    """

    MODE_VERIFY = "verify"
    MODE_LOOKUP = "lookup"

    rowResult = pyqtSignal(int, str, dict)
    waiting = pyqtSignal(float, str)
    finished = pyqtSignal(dict)

    def __init__(
        self,
        rows: list[tuple[int, str, str]],
        *,
        source: str,
        import_context_by_tunnus: dict | None = None,
        mode: str = MODE_VERIFY,
    ):
        super().__init__()
        if mode not in (self.MODE_VERIFY, self.MODE_LOOKUP):
            raise ValueError(f"unknown verify mode: {mode}")
        if mode == self.MODE_VERIFY and import_context_by_tunnus is None:
            raise ValueError("verify mode needs the import context of every row")

        self._rows = rows
        self._source = source
        self._mode = mode
        self._import_context_by_tunnus = import_context_by_tunnus or {}
        self._cancel = Event()

    def stop(self) -> None:
        self._cancel.set()

    @pyqtSlot()
    def run(self) -> None:
        ok_fresh: list[str] = []
        missing_backend: list[str] = []
        archived_only_backend: list[str] = []
        outdated_backend: list[str] = []
        errors: list[dict] = []

        try:
            with api_request_context(cancel_event=self._cancel, on_wait=self.waiting.emit):
                for row, tunnus, import_muudet in self._rows:
                    if self._cancel.is_set():
                        break

                    try:
                        backend_info = BackendPropertyVerifier.verify_properties_by_cadastral_number(tunnus)
                    except RequestCancelled:
                        # The row was never checked; it is unfinished, not a failed lookup.
                        break
                    except Exception as e:
                        errors.append({"tunnus": tunnus, "error": str(e)})
                        self.rowResult.emit(
                            row,
                            tunnus,
                            {
                                "attention": True,
                                "causes": [K.ATTENTION_CAUSE_BACKEND_LOOKUP_FAILED],
                                "backend_info": None,
                            },
                        )
                        continue

                    # A response that arrives after stop() belongs to a discarded run.
                    if self._cancel.is_set():
                        break

                    if self._mode == self.MODE_LOOKUP:
                        self.rowResult.emit(
                            row,
                            tunnus,
                            {
                                "attention": False,
                                "causes": [],
                                "backend_info": backend_info if isinstance(backend_info, dict) else None,
                            },
                        )
                        continue

                    # A row that cannot be decided is one row's problem. Reading its
                    # verdict must not end the run, or the caller never hears `finished`.
                    try:
                        decision, attention_causes = self._decide(
                            tunnus,
                            import_muudet,
                            backend_info,
                            ok_fresh=ok_fresh,
                            missing_backend=missing_backend,
                            archived_only_backend=archived_only_backend,
                            outdated_backend=outdated_backend,
                        )
                    except Exception as e:
                        PythonFailLogger.log_exception(
                            e,
                            module="property",
                            event="backend_verify_decision_failed",
                            extra={"tunnus": tunnus, "source": self._source},
                        )
                        errors.append({"tunnus": tunnus, "error": str(e)})
                        self.rowResult.emit(
                            row,
                            tunnus,
                            {
                                "attention": True,
                                "causes": [K.ATTENTION_CAUSE_BACKEND_LOOKUP_FAILED],
                                "backend_info": backend_info if isinstance(backend_info, dict) else None,
                            },
                        )
                        continue

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
        except Exception as e:
            PythonFailLogger.log_exception(
                e,
                module="property",
                event="backend_verify_run_failed",
                extra={"source": self._source},
            )
            errors.append({"tunnus": "", "error": str(e)})
        finally:
            self.finished.emit(
                {
                    "source": self._source,
                    "ok_fresh": ok_fresh,
                    "missing_backend": missing_backend,
                    "archived_only": archived_only_backend,
                    "outdated_backend": outdated_backend,
                    "errors": errors,
                    "stopped": self._cancel.is_set(),
                }
            )

    def _decide(
        self,
        tunnus: str,
        import_muudet,
        backend_info,
        *,
        ok_fresh: list[str],
        missing_backend: list[str],
        archived_only_backend: list[str],
        outdated_backend: list[str],
    ) -> tuple[dict, list[str]]:
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
        return decision, attention_causes
