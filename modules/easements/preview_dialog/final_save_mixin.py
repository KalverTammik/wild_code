from __future__ import annotations
import os
from typing import Optional
from ....languages.translation_keys import TranslationKeys
from ....modules.easements.easement_layer_service import EasementLayerService
from ....modules.easements.easement_pdf_service import EasementPdfService
from ....python.api_actions import APIModuleActions
from ....utils.layers.module_layer_service_base import FieldValueProblem
from ....Logs.python_fail_logger import PythonFailLogger
from ....ui.messages_helper import ModernMessageDialog
from ....ui.map_tools.kavitro_sync_retry import offer_kavitro_sync_retry
from ....constants.module_names import Module
from ....widgets.DataDisplayWidgets.TaskFilePreviewDialog import TaskFilePreviewDialog
from ..easement_geometry_form_dialog import EasementGeometryFormDialog


class EasementFinalSaveMixin:
    """Saving the final cut: into the easement main layer and its geometry to the backend,
    and the PDF drawing (preview, publish, cleanup). Mixed into EasementPreviewDialog.
    """

    def _save_final_cut_to_main_layer(
        self,
        property_edges: Optional[list[dict]] = None,
        value_problems: Optional[list[FieldValueProblem]] = None,
    ) -> tuple[bool, str]:
        """`value_problems` gets the fields left empty, only when the area really reached the layer."""
        final_layer, final_status = self._ensure_final_cut_layer()
        if final_layer is None:
            return False, final_status or self._lang.translate(TranslationKeys.EASEMENT_PREVIEW_FINAL_FAILED)

        target_layer = EasementLayerService.resolve_main_layer(dialogs=None)
        if target_layer is None:
            return False, self._lang.translate(TranslationKeys.EASEMENT_LAYER_MISSING)
        if target_layer.isEditable():
            # The cut would stay in the user's session unsaved, and Kavitro would get a shape the layer lacks.
            return False, self._lang.translate(TranslationKeys.LAYER_ALREADY_EDITING).format(layer=target_layer.name())

        form_values = EasementGeometryFormDialog.prompt(
            item_data=self._item,
            initial_values=self._easement_form_initial_values(property_edges or []),
            layer=target_layer,
            parent=self,
            on_status_changed=self._on_status_changed,
        )
        if form_values is None:
            return False, self._lang.translate(TranslationKeys.EASEMENT_FORM_CANCELLED)

        saved_problems: list[FieldValueProblem] = []
        ok, message = EasementLayerService.upsert_final_cut_feature(
            layer=target_layer,
            final_layer=final_layer,
            item_id=self._item_id,
            item_data=self._item,
            property_edges=property_edges,
            form_values=form_values,
            value_problems=saved_problems,
        )
        if ok:
            if value_problems is not None:
                value_problems.extend(saved_problems)
            # The layer is saved first; a failed Kavitro update can be tried again before the dialog goes on.
            sync_failed = self._lang.translate(TranslationKeys.EASEMENT_FINAL_GEOMETRY_SYNC_FAILED)
            geometry_synced = self._sync_saved_easement_geometry_to_backend(target_layer) or offer_kavitro_sync_retry(
                lambda: (self._sync_saved_easement_geometry_to_backend(target_layer), ""),
                failure_message=lambda _detail: sync_failed,
                title=self._lang.translate(TranslationKeys.ERROR),
                log_module=Module.EASEMENT.value,
                parent=self,
                extra={"item_id": str(self._item_id or "")},
                dialog_class=ModernMessageDialog,
            )
            if not geometry_synced:
                return False, sync_failed
            return True, self._lang.translate(TranslationKeys.EASEMENT_LAYER_SAVE_SUCCESS).format(layer=message)
        return False, self._lang.translate(TranslationKeys.EASEMENT_LAYER_SAVE_FAILED).format(error=message)

    def _sync_saved_easement_geometry_to_backend(self, layer) -> bool:
        item_id = str(self._item_id or "").strip()
        if not item_id:
            return False
        try:
            feature = EasementLayerService.find_feature(
                layer,
                item_id=item_id,
                item_number=str(self._item_number or "").strip(),
            )
            geometry = feature.geometry() if feature is not None else None
            geometry_payload = EasementLayerService.backend_geometry_payload_from_geometry(geometry)
            if geometry_payload is None:
                PythonFailLogger.log(
                    "easement_final_geometry_backend_sync_skipped_no_geometry",
                    module="easement",
                    extra={"item_id": item_id},
                )
                return False

            if APIModuleActions.update_easement_geometry(item_id, geometry_payload):
                PythonFailLogger.log(
                    "easement_final_geometry_backend_sync_success",
                    module="easement",
                    extra={"item_id": item_id, "geometry_type": str(geometry_payload.get("type") or "")},
                )
                return True
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module="easement",
                event="easement_final_geometry_backend_sync_failed",
                extra={"item_id": item_id},
            )
            return False

        PythonFailLogger.log_exception(
            RuntimeError("Could not update final easement geometry in backend"),
            module="easement",
            event="easement_final_geometry_backend_update_failed",
            extra={"item_id": item_id},
        )
        return False

    def _easement_form_initial_values(self, property_edges: list[dict]) -> dict[str, object]:
        edges = property_edges or self._property_edges or []
        cadastral_numbers = [
            str(edge.get("cadastralUnitNumber") or "").strip()
            for edge in edges
            if str(edge.get("cadastralUnitNumber") or "").strip()
        ]

        total_compensation = 0.0
        has_compensation = False
        for edge in edges:
            total_price = edge.get("totalPrice") if isinstance(edge.get("totalPrice"), dict) else {}
            amount = total_price.get("amount")
            try:
                if amount not in (None, ""):
                    total_compensation += float(amount)
                    has_compensation = True
            except (TypeError, ValueError, OverflowError):
                continue

        values: dict[str, object] = {}
        if cadastral_numbers:
            values[EasementGeometryFormDialog.FIELD_CADASTRAL] = ", ".join(cadastral_numbers)
        if self._final_area_sqm > 0:
            values["Kaitsevööndi pindala"] = round(float(self._final_area_sqm), 2)
        if has_compensation:
            values[EasementGeometryFormDialog.FIELD_COMPENSATION] = round(total_compensation, 2)
        return values

    def _cleanup_generated_pdf(self) -> None:
        path = str(self._generated_pdf_path or "").strip()
        self._generated_pdf_path = ""
        if not path:
            return
        try:
            EasementPdfService.cleanup_output_pdf(path)
        except Exception as exc:
            # Runs from reject()/closeEvent(), so nothing may escape; pathlib errors vary by platform.
            PythonFailLogger.log_exception(
                exc,
                module=Module.EASEMENT.value,
                event="easement_pdf_cleanup_failed",
            )

    def _drawing_preview_title(self) -> str:
        return f"{self._item_number or self._item_id or 'easement'}_drawing.pdf"

    def _ensure_generated_pdf(self) -> tuple[str, str]:
        final_layer, final_status = self._ensure_final_cut_layer()
        if final_layer is None:
            return "", final_status or self._lang.translate(TranslationKeys.EASEMENT_PREVIEW_FINAL_FAILED)

        self._cleanup_generated_pdf()
        ok, payload = EasementPdfService.export_final_cut_pdf(
            item_data=self._item,
            item_id=self._item_id,
            item_number=self._item_number,
            item_name=self._item_name,
            final_layer=final_layer,
            property_layer=self._property_layer,
        )
        if not ok:
            return "", self._lang.translate(TranslationKeys.EASEMENT_PREVIEW_DRAWING_EXPORT_FAILED).format(
                error=str(payload or "-")
            )

        self._generated_pdf_path = str(payload or "").strip()
        return self._generated_pdf_path, ""

    def _preview_pdf_drawing(self) -> None:
        pdf_path, error = self._ensure_generated_pdf()
        if not pdf_path:
            ModernMessageDialog.show_error(
                self._lang.translate(TranslationKeys.ERROR),
                error or self._lang.translate(TranslationKeys.EASEMENT_PREVIEW_DRAWING_PREVIEW_FAILED),
            )
            return

        dialog = TaskFilePreviewDialog.open_preview(
            local_file_path=pdf_path,
            local_title=self._drawing_preview_title(),
            parent=self,
        )
        if dialog is not None:
            dialog.exec_()

    def _publish_pdf_drawing(self) -> None:
        """Button slot: one publish at a time, the button stays disabled until it ends."""
        if self._publish_in_progress:
            return
        self._publish_in_progress = True
        self._publish_drawing_button.setEnabled(False)
        try:
            self._publish_pdf_drawing_steps()
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.EASEMENT.value,
                event="easement_pdf_publish_failed",
                extra={"item_id": str(self._item_id or "")},
            )
            ModernMessageDialog.show_error(
                self._lang.translate(TranslationKeys.ERROR),
                self._lang.translate(TranslationKeys.EASEMENT_PREVIEW_DRAWING_PUBLISH_FAILED),
            )
        finally:
            self._publish_in_progress = False
            try:
                self._publish_drawing_button.setEnabled(True)
            except RuntimeError:
                pass  # the dialog was closed while a message was open

    @staticmethod
    def _next_version_name(file_name: str, taken_names: set[str]) -> str:
        """`S-1.pdf` -> `S-1_v2.pdf`, or the first `_vN` that is not among `taken_names` (lower case)."""
        stem, ext = os.path.splitext(file_name)
        version = 2
        while f"{stem}_v{version}{ext}".casefold() in taken_names:
            version += 1
        return f"{stem}_v{version}{ext}"

    def _publish_pdf_drawing_steps(self) -> None:
        pdf_path, error = self._ensure_generated_pdf()
        if not pdf_path:
            ModernMessageDialog.show_error(
                self._lang.translate(TranslationKeys.ERROR),
                error or self._lang.translate(TranslationKeys.EASEMENT_PREVIEW_DRAWING_PUBLISH_FAILED),
            )
            return

        file_name = os.path.basename(pdf_path)
        existing_files = APIModuleActions.get_module_files(Module.EASEMENT.value, self._item_id)
        same_name: list[dict] = []
        if existing_files is None:
            # The list could not be read: publishing now might add a duplicate, so the user decides.
            if not ModernMessageDialog.show_warning(
                self._lang.translate(TranslationKeys.EASEMENT_PREVIEW_DRAWING_PUBLISH),
                self._lang.translate(TranslationKeys.EASEMENT_PREVIEW_DRAWING_FILES_CHECK_FAILED).format(
                    name=file_name
                ),
                with_cancel=True,
                parent=self,
            ):
                return
        else:
            taken_names = {
                str(entry.get("fileName") or "").strip().casefold()
                for entry in existing_files
                if isinstance(entry, dict) and not entry.get("deletedAt")
            }
            same_name = [
                entry for entry in existing_files
                if isinstance(entry, dict)
                and not entry.get("deletedAt")
                and str(entry.get("fileName") or "").strip().casefold() == file_name.casefold()
            ]

        if same_name:
            new_name = self._next_version_name(file_name, taken_names)
            replace_label = self._lang.translate(TranslationKeys.EASEMENT_PREVIEW_DRAWING_REPLACE)
            version_label = self._lang.translate(TranslationKeys.EASEMENT_PREVIEW_DRAWING_NEW_VERSION)
            cancel_label = self._lang.translate(TranslationKeys.CANCEL_BUTTON)
            choice = ModernMessageDialog.ask_choice_modern(
                self._lang.translate(TranslationKeys.EASEMENT_PREVIEW_DRAWING_EXISTS_TITLE),
                self._lang.translate(TranslationKeys.EASEMENT_PREVIEW_DRAWING_EXISTS_MESSAGE).format(
                    name=file_name, new_name=new_name
                ),
                buttons=[replace_label, version_label, cancel_label],
                parent=self,
                default=cancel_label,
                cancel=cancel_label,
            )
            if choice == version_label:
                renamed = EasementPdfService.rename_output_pdf(pdf_path, os.path.splitext(new_name)[0])
                if not renamed:
                    ModernMessageDialog.show_error(
                        self._lang.translate(TranslationKeys.ERROR),
                        self._lang.translate(TranslationKeys.EASEMENT_PREVIEW_DRAWING_PUBLISH_FAILED),
                    )
                    return
                self._generated_pdf_path = renamed
                pdf_path, file_name = renamed, os.path.basename(renamed)
                same_name = []
            elif choice != replace_label:
                return

        uploaded = APIModuleActions.upload_module_file(Module.EASEMENT.value, self._item_id, pdf_path)
        if not (isinstance(uploaded, dict) and str(uploaded.get("uuid") or "").strip()):
            ModernMessageDialog.show_error(
                self._lang.translate(TranslationKeys.ERROR),
                self._lang.translate(TranslationKeys.EASEMENT_PREVIEW_DRAWING_PUBLISH_FAILED),
            )
            return

        # Replace = the new file first, then the old one goes; a failed delete never loses the drawing.
        new_uuid = str(uploaded.get("uuid") or "").strip()
        not_removed = [
            entry for entry in same_name
            if str(entry.get("uuid") or "").strip() != new_uuid
            and not APIModuleActions.delete_file(str(entry.get("uuid") or ""))
        ]
        message = "\n\n".join([
            self._lang.translate(TranslationKeys.EASEMENT_PREVIEW_DRAWING_PUBLISH_SUCCESS),
            self._lang.translate(TranslationKeys.EASEMENT_PREVIEW_DRAWING_FILE_NAME).format(name=file_name),
        ])
        if not_removed:
            ModernMessageDialog.show_warning(
                self._lang.translate(TranslationKeys.ERROR),
                message + "\n\n" + self._lang.translate(TranslationKeys.EASEMENT_PREVIEW_DRAWING_OLD_NOT_REMOVED).format(
                    name=file_name
                ),
                parent=self,
            )
            return
        ModernMessageDialog.show_info(self._lang.translate(TranslationKeys.SUCCESS), message)
