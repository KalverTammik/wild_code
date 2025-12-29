from __future__ import annotations

from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot

from .MainAddProperties import BackendPropertyVerifier, MainAddPropertiesFlow


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
        backend_last_updated_override_by_tunnus: dict[str, str] | None = None,
    ):
        super().__init__()
        self._rows = rows
        self._source = source
        self._backend_last_updated_override_by_tunnus = backend_last_updated_override_by_tunnus or {}
        self._stop = False

    def stop(self) -> None:
        self._stop = True

    @pyqtSlot()
    def run(self) -> None:
        ok_fresh: list[str] = []
        missing_backend: list[str] = []
        archived_only_backend: list[str] = []
        outdated_backend: list[str] = []
        errors: list[dict] = []

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

            exists_backend_any = False
            archived_only_val = None
            backend_last_updated = ""

            if isinstance(backend_info, dict):
                exists_val = backend_info.get("exists")
                archived_only_val = backend_info.get("archived_only")
                backend_last_updated = str(backend_info.get("LastUpdated") or "")

                active_count = backend_info.get("active_count")
                archived_count = backend_info.get("archived_count")
                prop = backend_info.get("property")

                if exists_val is not None:
                    exists_backend_any = bool(exists_val or archived_only_val)
                else:
                    try:
                        exists_backend_any = bool((int(active_count or 0) + int(archived_count or 0)) > 0)
                    except Exception:
                        exists_backend_any = bool(prop)

            attention = False
            attention_causes: list[str] = []

            if isinstance(backend_info, dict) and backend_info.get("exists") is None:
                attention = True
                attention_causes.append("backend lookup failed")
            elif not exists_backend_any:
                attention = True
                missing_backend.append(tunnus)
                attention_causes.append("missing in backend")
            elif archived_only_val:
                attention = True
                archived_only_backend.append(tunnus)
                attention_causes.append("archived only")
            else:
                import_newer = False
                try:
                    effective_backend_last_updated = self._backend_last_updated_override_by_tunnus.get(tunnus, "") or backend_last_updated
                    import_newer = bool(
                        MainAddPropertiesFlow._is_import_newer(import_muudet, effective_backend_last_updated, None)
                    )
                except Exception:
                    import_newer = False

                if import_newer:
                    attention = True
                    outdated_backend.append(tunnus)
                    attention_causes.append("import newer")
                else:
                    ok_fresh.append(tunnus)

            self.rowResult.emit(
                row,
                tunnus,
                {
                    "attention": attention,
                    "causes": attention_causes,
                    "backend_info": backend_info if isinstance(backend_info, dict) else None,
                },
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
