from __future__ import annotations
from typing import Iterable
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import (
    QDialog,
    QFrame,
    QLabel,
    QVBoxLayout,
    QWidget,
)
from ....constants.cadastral_fields import AreaUnit
from ....constants.cadastral_fields import Katastriyksus
from ....languages.translation_keys import TranslationKeys
from ....utils.api_error_handling import user_message
from ....python.api_actions import APIModuleActions
from ....utils.MapTools.MapHelpers import ActiveLayersHelper, MapHelpers
from ....utils.MapTools.MapSelectionOrchestrator import MapSelectionOrchestrator
from ....utils.layers.field_value_problems import field_value_problems_note
from ....utils.layers.module_layer_service_base import FieldValueProblem
from ....Logs.python_fail_logger import PythonFailLogger
from ....ui.messages_helper import ModernMessageDialog
from ....constants.module_names import Module
from ....widgets.DataDisplayWidgets.LinkReviewDialog import PropertyLinkReviewDialog
from ....widgets.EasementPropertyAreaCalculationWidget import EasementPropertyAreaCalculationWidget
from ..easement_property_edges import (
    DEFAULT_CURRENCY, calculate_total_amount, format_area_display, format_property_label,
    format_total_amount, normalize_property_edge,
)


class EasementPropertyEditorMixin:
    """The easement's properties: one editor row per property, their areas and prices, map
    selection of more properties and saving them to the backend. Mixed into
    EasementPreviewDialog, whose __init__ creates the widgets and state used here.
    """

    @staticmethod
    def _clear_layout(layout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            child_layout = item.layout()
            if widget is not None:
                widget.deleteLater()
            elif child_layout is not None:
                EasementPropertyEditorMixin._clear_layout(child_layout)

    def _first_property_feature(self):
        layer = self._property_layer
        if layer is None or not layer.isValid():
            return None

        try:
            selected_features = list(layer.getSelectedFeatures())
        except (AttributeError, RuntimeError):
            selected_features = []
        if selected_features:
            return selected_features[0]

        try:
            for feature in layer.getFeatures():
                return feature
        except (AttributeError, RuntimeError):
            return None
        return None

    def _refresh_property_summary_card(self) -> None:
        try:
            self._property_summary_card.set_feature(self._first_property_feature())
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.EASEMENT.value,
                event="easement_property_summary_refresh_failed",
            )
            self._property_summary_card.clear()

    def _update_property_row_total(self, row_key: str) -> None:
        editors = self._property_row_widgets.get(row_key) or {}
        editor_widget = editors.get("editor_widget")
        if editor_widget is None:
            return

        unit_value = str(editor_widget.current_unit() or AreaUnit.M)
        square_meters = float(self._calculated_property_area_sqm.get(row_key, 0.0) or 0.0)
        area_value = square_meters / 10000.0 if unit_value == AreaUnit.H else square_meters
        total = calculate_total_amount(float(area_value), float(editor_widget.price_value()))
        editor_widget.set_total_display(
            format_total_amount(total, str(editor_widget.currency_code() or DEFAULT_CURRENCY))
        )

    def _refresh_property_area_label(self, row_key: str) -> None:
        editors = self._property_row_widgets.get(row_key) or {}
        editor_widget = editors.get("editor_widget")
        if editor_widget is None:
            return

        unit_value = str(editor_widget.current_unit() or AreaUnit.M)
        square_meters = float(self._calculated_property_area_sqm.get(row_key, 0.0) or 0.0)
        editor_widget.set_area_display(format_area_display(square_meters, unit_value))
        self._update_property_row_total(row_key)

    def _reset_area_calculations(self) -> None:
        self._calculated_property_area_sqm = {}
        self._final_area_sqm = 0.0
        for row_key in list(self._property_row_widgets.keys()):
            self._refresh_property_area_label(row_key)

    def _build_property_editor_row(self, edge: dict[str, object], *, show_title: bool = True) -> QWidget:
        row_key = str(edge.get("cadastralUnitNumber") or edge.get("id") or "")
        row = QFrame(self._property_rows_container)
        row.setProperty("easementPropertyRow", True)

        layout = QVBoxLayout(row)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        if show_title:
            title = QLabel(str(edge.get("display") or row_key or "-"), row)
            title.setWordWrap(True)
            layout.addWidget(title)

        editor_widget = EasementPropertyAreaCalculationWidget(
            lang_manager=self._lang,
            edge=edge,
            area_unit_labels=self._AREA_UNIT_LABELS,
            default_currency=DEFAULT_CURRENCY,
            parent=row,
        )
        layout.addWidget(editor_widget)

        self._property_row_widgets[row_key] = {
            "row": row,
            "edge": edge,
            "editor_widget": editor_widget,
        }

        editor_widget.totalsChanged.connect(lambda key=row_key: self._update_property_row_total(key))
        editor_widget.unitChanged.connect(lambda key=row_key: self._refresh_property_area_label(key))

        self._update_property_row_total(row_key)
        self._refresh_property_area_label(row_key)
        return row

    def _set_property_edges(self, edges: list[dict[str, object]]) -> None:
        self._property_edges = [normalize_property_edge(edge) for edge in (edges or [])]
        self._connected_property_numbers = [
            str(edge.get("cadastralUnitNumber") or "")
            for edge in self._property_edges
            if str(edge.get("cadastralUnitNumber") or "").strip()
        ]
        self._property_row_widgets.clear()
        self._clear_layout(self._property_rows_layout)

        if not self._property_edges:
            self._property_summary_card.clear()
            empty_label = QLabel(
                self._lang.translate(TranslationKeys.EASEMENT_PREVIEW_DEFINE_PROPERTIES_HINT),
                self._property_rows_container,
            )
            empty_label.setWordWrap(True)
            empty_label.setObjectName("SetupCardDescription")
            self._property_rows_layout.addWidget(empty_label)
            self._save_properties_button.setEnabled(False)
            return

        show_titles = len(self._property_edges) > 1
        for edge in self._property_edges:
            self._property_rows_layout.addWidget(self._build_property_editor_row(edge, show_title=show_titles))

        self._property_rows_layout.addStretch(1)
        self._save_properties_button.setEnabled(True)
        self._reset_area_calculations()

    def _existing_property_display(self, main_layer) -> dict[str, str]:
        existing_display: dict[str, str] = {}
        existing_numbers = set(self._connected_property_numbers or [])
        if existing_numbers and main_layer is not None:
            existing_feats = MapHelpers.find_features_by_fields_and_values(
                main_layer,
                Katastriyksus.tunnus,
                list(existing_numbers),
            )
            for feat in existing_feats or []:
                try:
                    num = feat[Katastriyksus.tunnus]
                except KeyError:
                    num = None
                if num and num in existing_numbers:
                    existing_display[num] = format_property_label(num, feat)
        for num in existing_numbers:
            existing_display.setdefault(num, format_property_label(num))
        return existing_display

    def _merge_selected_properties_into_editor(self, selected_numbers: list[str], selected_features: list) -> None:
        feature_by_number: dict[str, object] = {}
        for feature in selected_features or []:
            try:
                number = str(feature[Katastriyksus.tunnus] or "").strip()
            except KeyError:
                number = ""
            if number:
                feature_by_number[number] = feature

        merged: list[dict[str, object]] = [dict(edge) for edge in self._property_edges]
        existing_numbers = {
            str(edge.get("cadastralUnitNumber") or "").strip()
            for edge in merged
            if str(edge.get("cadastralUnitNumber") or "").strip()
        }

        for number in selected_numbers:
            clean_number = str(number or "").strip()
            if not clean_number or clean_number in existing_numbers:
                continue
            feature = feature_by_number.get(clean_number)
            display = format_property_label(clean_number, feature)
            merged.append(
                normalize_property_edge(
                    {
                        "id": "",
                        "cadastralUnitNumber": clean_number,
                        "displayAddress": display.split(" — ", 1)[0] if " — " in display else "",
                        "isPayable": False,
                    }
                )
            )
            existing_numbers.add(clean_number)

        self._set_property_edges(merged)

    def _collect_property_payloads(self) -> tuple[list[dict[str, object]], list[str]]:
        payloads: list[dict[str, object]] = []
        invalid_dates: list[str] = []

        for row_key, editors in self._property_row_widgets.items():
            edge = editors.get("edge") or {}
            number = str(edge.get("cadastralUnitNumber") or row_key or "").strip()
            property_id = str(edge.get("id") or "").strip()
            editor_widget = editors.get("editor_widget")

            unit_value = str(editor_widget.current_unit() or AreaUnit.M) if editor_widget is not None else AreaUnit.M
            square_meters = float(self._calculated_property_area_sqm.get(row_key, 0.0) or 0.0)
            area_value = square_meters / 10000.0 if unit_value == AreaUnit.H else square_meters
            price_value = float(editor_widget.price_value()) if editor_widget is not None else 0.0
            currency_value = (
                str(editor_widget.currency_code() or DEFAULT_CURRENCY)
                if editor_widget is not None
                else DEFAULT_CURRENCY
            )
            is_payable = bool(editor_widget.is_payable()) if editor_widget is not None else False
            date_text = str(editor_widget.next_payment_text() or "") if editor_widget is not None else ""
            next_payment_date = self._date_helper.date_to_iso_string(date_text) if date_text else ""
            if date_text and not next_payment_date:
                invalid_dates.append(str(edge.get("display") or number or row_key))
                continue

            payload: dict[str, object] = {
                "id": property_id,
                "cadastralUnitNumber": number,
                "isPayable": is_payable,
            }
            if area_value > 0:
                payload["area"] = {
                    "size": round(area_value, 2),
                    "unit": unit_value,
                }
            if price_value > 0:
                payload["pricePerAreaUnit"] = {
                    "amount": round(price_value, 2),
                    "currencyCode": currency_value,
                }
            if next_payment_date:
                payload["nextPaymentDate"] = next_payment_date
            payloads.append(payload)

        return payloads, invalid_dates

    def _save_property_details(self) -> None:
        if not self._item_id:
            return

        payloads, invalid_dates = self._collect_property_payloads()
        if invalid_dates:
            ModernMessageDialog.show_warning(
                self._lang.translate(TranslationKeys.ERROR),
                self._lang.translate(TranslationKeys.EASEMENT_PREVIEW_PROPERTY_INVALID_DATE).format(
                    property=invalid_dates[0]
                ),
            )
            return

        unresolved_numbers = [
            str(payload.get("cadastralUnitNumber") or "").strip()
            for payload in payloads
            if not str(payload.get("id") or "").strip() and str(payload.get("cadastralUnitNumber") or "").strip()
        ]
        try:
            resolved_map, missing = APIModuleActions.resolve_property_map_by_cadastral(unresolved_numbers)
            save_payloads: list[dict[str, object]] = []
            for payload in payloads:
                property_id = str(payload.get("id") or "").strip()
                number = str(payload.get("cadastralUnitNumber") or "").strip()
                if not property_id and number:
                    property_id = resolved_map.get(number, "")
                    if property_id:
                        payload["id"] = property_id
                if property_id:
                    save_payload = dict(payload)
                    save_payload.pop("cadastralUnitNumber", None)
                    save_payloads.append(save_payload)

            if not save_payloads:
                raise_message = ", ".join(missing[:5]) or ", ".join(unresolved_numbers[:5]) or "-"
                ModernMessageDialog.show_warning(
                    self._lang.translate(TranslationKeys.ERROR),
                    self._lang.translate(TranslationKeys.EASEMENT_PREVIEW_PROPERTY_SAVE_FAILED).format(
                        pid=self._item_id,
                        count=len(payloads),
                        preview=raise_message,
                        err=self._lang.translate(TranslationKeys.EASEMENT_PREVIEW_PROPERTY_NONE_RESOLVED),
                    ),
                )
                return

            APIModuleActions.associate_easement_properties(self._item_id, save_payloads)
            refreshed_edges = APIModuleActions.get_easement_property_edges(self._item_id) or []
            self._set_property_edges(refreshed_edges)
            value_problems: list[FieldValueProblem] = []
            layer_saved, layer_message = self._save_final_cut_to_main_layer(refreshed_edges, value_problems)

            preview_numbers = [
                str(edge.get("cadastralUnitNumber") or "")
                for edge in self._property_edges
                if str(edge.get("cadastralUnitNumber") or "").strip()
            ]
            preview_text = ", ".join(preview_numbers[:5])
            extra_note = ""
            if missing:
                missing_preview = ", ".join(missing[:5])
                extra_note = "\n\n" + self._lang.translate(TranslationKeys.LINK_PROPERTIES_MISSING_NOTE).format(
                    missing=missing_preview
                )
                if len(missing) > 5:
                    extra_note += self._lang.translate(TranslationKeys.MORE_COUNT_SUFFIX).format(
                        count=len(missing) - 5
                    )
            if len(preview_numbers) > 5:
                preview_text += self._lang.translate(TranslationKeys.MORE_COUNT_SUFFIX).format(
                    count=len(preview_numbers) - 5
                )
            if layer_message:
                extra_note += ("\n\n" if extra_note else "\n\n") + layer_message
            problems_note = field_value_problems_note(value_problems, self._lang)
            if problems_note:
                extra_note += "\n\n" + problems_note

            success_message = self._lang.translate(TranslationKeys.EASEMENT_PREVIEW_PROPERTY_SAVE_SUCCESS).format(
                pid=self._item_id,
                count=len(preview_numbers),
                preview=preview_text,
                extra=extra_note,
            )
            if layer_saved and problems_note:
                ModernMessageDialog.show_warning(
                    self._lang.translate(TranslationKeys.FIELD_VALUE_PROBLEMS_TITLE),
                    success_message,
                )
            elif layer_saved:
                ModernMessageDialog.show_info(
                    self._lang.translate(TranslationKeys.SUCCESS),
                    success_message,
                )
            else:
                ModernMessageDialog.show_warning(
                    self._lang.translate(TranslationKeys.ERROR),
                    success_message,
                )
            self._rerun_automation()
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.EASEMENT.value,
                event="easement_preview_property_save_failed",
                extra={"item_id": self._item_id},
            )
            preview = ", ".join(
                str(payload.get("cadastralUnitNumber") or "")
                for payload in payloads[:5]
                if str(payload.get("cadastralUnitNumber") or "").strip()
            ) or "-"
            ModernMessageDialog.show_warning(
                self._lang.translate(TranslationKeys.ERROR),
                self._lang.translate(TranslationKeys.EASEMENT_PREVIEW_PROPERTY_SAVE_FAILED).format(
                    pid=self._item_id,
                    count=len(payloads),
                    preview=preview,
                    err=user_message(exc),
                ),
            )

    def _finish_property_selection(self) -> None:
        try:
            if self._property_selection_orchestrator is not None:
                self._property_selection_orchestrator.cancel()
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.EASEMENT.value,
                event="easement_property_selection_cancel_failed",
            )
        self._property_selection_orchestrator = None

    def _open_property_link_review_dialog(self, selected_numbers: list[str], selected_features: list, main_layer) -> None:
        existing_display = self._existing_property_display(main_layer)
        selected_display: dict[str, str] = {}
        for feat in selected_features or []:
            try:
                num = feat[Katastriyksus.tunnus]
            except KeyError:
                num = None
            if num:
                selected_display[str(num)] = format_property_label(str(num), feat)
        for num in selected_numbers:
            selected_display.setdefault(num, format_property_label(num))

        dialog = PropertyLinkReviewDialog(existing_display, selected_display, self._lang)
        result = dialog.exec_()
        if dialog.reselect_requested:
            QTimer.singleShot(0, self._start_define_properties_flow)
            return
        if result != QDialog.Accepted:
            self._finish_property_selection()
            return

        try:
            self._merge_selected_properties_into_editor(selected_numbers, selected_features)
            self._define_properties_button.setVisible(False)
            self._status_label.setText(
                self._lang.translate(TranslationKeys.EASEMENT_PREVIEW_PROPERTY_SECTION_HINT)
            )
            QTimer.singleShot(0, lambda: self._initialize_connected_property_flow(refresh_from_backend=False))
            return
        except Exception as exc:
            PythonFailLogger.log_exception(
                exc,
                module=Module.EASEMENT.value,
                event="easement_preview_property_link_failed",
                extra={"item_id": self._item_id},
            )
            summary = ", ".join(selected_numbers[:5])
            if len(selected_numbers) > 5:
                summary += self._lang.translate(TranslationKeys.MORE_COUNT_SUFFIX).format(
                    count=len(selected_numbers) - 5
                )
            ModernMessageDialog.show_warning(
                self._lang.translate(TranslationKeys.ERROR),
                self._lang.translate(TranslationKeys.EASEMENT_PREVIEW_LINK_FAILED).format(
                    pid=self._item_id,
                    count=len(selected_numbers),
                    preview=summary,
                    err=user_message(exc),
                ),
            )
        finally:
            self._finish_property_selection()

    def _start_define_properties_flow(self) -> None:
        if not self._item_id:
            return

        main_layer = ActiveLayersHelper.resolve_main_property_layer(dialogs=ModernMessageDialog)
        if main_layer is None:
            ModernMessageDialog.show_warning(
                self._lang.translate(TranslationKeys.ERROR),
                self._lang.translate(TranslationKeys.EASEMENT_PREVIEW_LAYER_MISSING),
            )
            return

        try:
            main_layer.removeSelection()
        except RuntimeError:
            pass

        if self._property_selection_orchestrator is not None:
            self._finish_property_selection()

        self._property_selection_orchestrator = MapSelectionOrchestrator(parent=self)

        def _on_selected(_layer, features: Iterable):
            self._exit_property_selection_mode()
            cadastral_numbers: list[str] = []
            selected_features = list(features or [])
            for feature in selected_features:
                try:
                    tunnus = feature[Katastriyksus.tunnus]
                except KeyError:
                    tunnus = None
                if tunnus:
                    cadastral_numbers.append(str(tunnus))

            if not cadastral_numbers:
                ModernMessageDialog.show_warning(
                    self._lang.translate(TranslationKeys.ERROR),
                    self._lang.translate(TranslationKeys.MAP_SELECTION_NONE),
                )
                self._finish_property_selection()
                return

            self._open_property_link_review_dialog(cadastral_numbers, selected_features, main_layer)

        started = self._property_selection_orchestrator.start_selection_for_layer(
            main_layer,
            on_selected=_on_selected,
            selection_tool="rectangle",
            restore_pan=True,
            min_selected=1,
            max_selected=None,
            clear_filter=False,
            keep_existing_selection=bool(self._connected_property_numbers),
            before_start=self._enter_property_selection_mode,
        )
        if not started:
            self._exit_property_selection_mode()
            self._finish_property_selection()
            ModernMessageDialog.show_warning(
                self._lang.translate(TranslationKeys.ERROR),
                self._lang.translate(TranslationKeys.MAP_SELECTION_START_FAILED),
            )
