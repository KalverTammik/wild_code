from __future__ import annotations

import math
from functools import partial

from PyQt5.QtCore import QPoint, QPointF, QRectF, Qt
from PyQt5.QtGui import QColor, QFont, QPainter, QPen, QPixmap
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget, QSizePolicy

from ..constants.file_paths import QssPaths
from ..constants.module_icons import ModuleIconPaths
from ..languages.language_manager import LanguageManager
from ..languages.translation_keys import TranslationKeys
from ..python.workers import FunctionWorker, start_worker
from ..widgets.theme_manager import ThemeManager
from .module_kpi_service import ModuleKpiService


class ModuleKpiGauge(QWidget):
    ARC_START_ANGLE = 135.0
    ARC_SWEEP_TOTAL = 360.0-135.0+45.0
    ARC_EDGE_GAP = 0.0
    ARC_SEGMENT_GAP = 0.0

    def __init__(self, *, lang_manager: LanguageManager, parent: QWidget | None = None):
        super().__init__(parent)
        self.lang_manager = lang_manager
        self._total_count = 0
        self._center_value = "--"
        self._segments: list[dict[str, object]] = []
        self._hovered_segment: str | None = None
        self._track_color = QColor("#d7dee8")
        self._show_track = True
        self._detail_popup_enabled = True
        self._hover_popup_target_rect = QRectF()
        self.setMouseTracking(True)
        self.setFixedSize(208, 162)
        self._build_hover_popup()

    def _build_hover_popup(self) -> None:
        self._hover_popup = QFrame(self)
        self._hover_popup.setObjectName("ModuleKpiHoverPopup")
        self._hover_popup.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self._hover_popup.hide()
        self._hover_popup.setStyleSheet(
            "QFrame#ModuleKpiHoverPopup {"
            " background: rgba(255, 255, 255, 0.96);"
            " border: 1px solid rgba(133, 149, 181, 0.28);"
            " border-radius: 12px;"
            "}"
            "QLabel#ModuleKpiHoverPopupTitle {"
            " color: #22304f;"
            " font-size: 11px;"
            " font-weight: 600;"
            "}"
            "QLabel#ModuleKpiHoverPopupValue {"
            " color: #0f1833;"
            " font-size: 22px;"
            " font-weight: 700;"
            "}"
            "QLabel#ModuleKpiHoverPopupMeta {"
            " color: #7181a6;"
            " font-size: 10px;"
            "}"
        )

        popup_layout = QVBoxLayout(self._hover_popup)
        popup_layout.setContentsMargins(12, 10, 12, 10)
        popup_layout.setSpacing(2)

        self._hover_popup_title = QLabel("", self._hover_popup)
        self._hover_popup_title.setObjectName("ModuleKpiHoverPopupTitle")
        popup_layout.addWidget(self._hover_popup_title)

        self._hover_popup_value = QLabel("", self._hover_popup)
        self._hover_popup_value.setObjectName("ModuleKpiHoverPopupValue")
        popup_layout.addWidget(self._hover_popup_value)

        self._hover_popup_meta = QLabel("", self._hover_popup)
        self._hover_popup_meta.setObjectName("ModuleKpiHoverPopupMeta")
        popup_layout.addWidget(self._hover_popup_meta)

    def set_loading_state(self) -> None:
        self._total_count = 0
        self._center_value = "..."
        self._segments = []
        self._hovered_segment = None
        self._show_track = True
        self._hover_popup_target_rect = QRectF()
        self.update()

    def set_error_state(self) -> None:
        self._total_count = 0
        self._center_value = "--"
        self._segments = []
        self._hovered_segment = None
        self._show_track = True
        self._hover_popup_target_rect = QRectF()
        self.update()

    def set_detail_popup_enabled(self, enabled: bool) -> None:
        self._detail_popup_enabled = bool(enabled)
        if not self._detail_popup_enabled:
            self._hover_popup.hide()
        elif self._hovered_segment:
            for segment in self._segment_geometry():
                if segment.get("key") == self._hovered_segment:
                    self._show_hover_popup(segment)
                    break
        self.update()

    def set_counts(self, *, total_count: int, overdue_count: int, due_soon_count: int, include_breakdown: bool = True) -> None:
        total_value = max(0, int(total_count or 0))
        overdue_value = max(0, min(total_value, int(overdue_count or 0)))
        due_soon_value = max(0, min(max(0, total_value - overdue_value), int(due_soon_count or 0)))
        other_value = max(0, total_value - overdue_value - due_soon_value)

        self._total_count = total_value
        self._center_value = str(total_value)
        self._show_track = total_value <= 0
        if include_breakdown:
            self._segments = [
                self._build_segment(
                    key="other",
                    label=self.lang_manager.translate(TranslationKeys.HOME_KPI_OTHER_LABEL),
                    tooltip=self.lang_manager.translate(TranslationKeys.HOME_KPI_OTHER_TOOLTIP),
                    count=other_value,
                    color=QColor("#17b89f"),
                ),
                self._build_segment(
                    key="due_soon",
                    label=self.lang_manager.translate(TranslationKeys.HOME_KPI_DUE_SOON_LABEL),
                    tooltip=self.lang_manager.translate(TranslationKeys.HOME_KPI_DUE_SOON_TOOLTIP),
                    count=due_soon_value,
                    color=QColor("#f2b318"),
                ),
                self._build_segment(
                    key="overdue",
                    label=self.lang_manager.translate(TranslationKeys.HOME_KPI_OVERDUE_LABEL),
                    tooltip=self.lang_manager.translate(TranslationKeys.HOME_KPI_OVERDUE_TOOLTIP),
                    count=overdue_value,
                    color=QColor("#ff5757"),
                ),
            ]
        else:
            self._segments = [
                self._build_segment(
                    key="total",
                    label=self.lang_manager.translate(TranslationKeys.HOME_KPI_TOTAL_LABEL),
                    tooltip="",
                    count=total_value,
                    color=QColor("#4f6f9a"),
                ),
            ] if total_value > 0 else []
        self._hovered_segment = None
        self.update()

    def _build_segment(self, *, key: str, label: str, tooltip: str, count: int, color: QColor) -> dict[str, object]:
        return {
            "key": key,
            "label": label,
            "tooltip": tooltip,
            "count": max(0, int(count or 0)),
            "color": color,
        }

    def _normalize_angle(self, angle: float) -> float:
        normalized = float(angle) % 360.0
        if normalized < 0.0:
            normalized += 360.0
        return normalized

    def _segment_bounds(self, segment: dict[str, object]) -> tuple[float, float]:
        start = self._normalize_angle(float(segment.get("start") or 0.0))
        sweep = max(0.0, float(segment.get("sweep") or 0.0))
        end = self._normalize_angle(start + sweep)
        return start, end

    def _angle_in_segment(self, angle: float, segment: dict[str, object]) -> bool:
        start, end = self._segment_bounds(segment)
        probe = self._normalize_angle(angle)
        if start <= end:
            return start <= probe <= end
        return probe >= start or probe <= end

    def _arc_geometry(self) -> tuple[QRectF, QPointF, float, float]:
        margin_x = 18.0
        top = 8.0
        size = min(float(self.width()) - (margin_x * 2.0), 146.0)
        rect = QRectF((self.width() - size) / 2.0, top, size, size)
        center = rect.center()
        radius = rect.width() / 2.0
        return rect, center, radius, 13.0

    def _segment_geometry(self) -> list[dict[str, object]]:
        if self._total_count <= 0 or not self._segments:
            return []

        gap_degrees = self.ARC_SEGMENT_GAP
        start_angle = self.ARC_START_ANGLE
        sweep_total = self.ARC_SWEEP_TOTAL
        edge_gap = self.ARC_EDGE_GAP
        active_segments = [segment for segment in self._segments if int(segment.get("count") or 0) > 0]
        gap_count = max(0, len(active_segments) - 1)
        usable_sweep = max(0.0, sweep_total - (edge_gap * 2.0) - (gap_count * gap_degrees))
        current_angle = self._normalize_angle(start_angle + edge_gap)
        geometry: list[dict[str, object]] = []

        for segment in self._segments:
            count = int(segment.get("count") or 0)
            if count <= 0:
                continue
            sweep = usable_sweep * (count / self._total_count)
            if sweep <= 0:
                continue
            segment_copy = dict(segment)
            segment_copy["start"] = current_angle
            segment_copy["sweep"] = sweep
            geometry.append(segment_copy)
            current_angle = self._normalize_angle(current_angle + sweep + gap_degrees)
        return geometry

    def _tooltip_text(self, segment: dict[str, object]) -> str:
        count = int(segment.get("count") or 0)
        percent = 0.0 if self._total_count <= 0 else (count / self._total_count) * 100.0
        return (
            f"{segment.get('label')}: {count}\n"
            f"{percent:.1f}%\n"
            f"{segment.get('tooltip')}"
        )

    def _segment_anchor_point(self, segment: dict[str, object], *, radius_offset: float = 0.0) -> QPointF:
        _rect, center, radius, _thickness = self._arc_geometry()
        start = self._normalize_angle(float(segment.get("start") or 0.0))
        sweep = max(0.0, float(segment.get("sweep") or 0.0))
        midpoint_angle = self._normalize_angle(start + (sweep / 2.0))
        radians = math.radians(midpoint_angle)

        anchor_radius = radius + float(radius_offset)
        x = center.x() + (anchor_radius * math.cos(radians))
        y = center.y() - (anchor_radius * math.sin(radians))
        return QPointF(x, y)

    def _segment_midpoint(self, segment: dict[str, object]) -> QPointF:
        _rect, _center, _radius, thickness = self._arc_geometry()
        return self._segment_anchor_point(segment, radius_offset=(thickness / 2.0) + 1.5)

    def _show_hover_popup(self, segment: dict[str, object]) -> None:
        count = int(segment.get("count") or 0)
        percent = 0.0 if self._total_count <= 0 else (count / self._total_count) * 100.0
        segment_color = QColor(segment.get("color") or QColor("#8595b5"))
        border_rgba = f"rgba({segment_color.red()}, {segment_color.green()}, {segment_color.blue()}, 0.30)"
        self._hover_popup_title.setText(str(segment.get("label") or ""))
        self._hover_popup_value.setText(str(count))
        self._hover_popup_meta.setText(f"{percent:.1f}%  |  {segment.get('tooltip')}")
        self._hover_popup.setStyleSheet(
            "QFrame#ModuleKpiHoverPopup {"
            " background: rgba(255, 255, 255, 0.96);"
            f" border: 1px solid {border_rgba};"
            " border-radius: 12px;"
            "}"
            "QLabel#ModuleKpiHoverPopupTitle {"
            " color: #22304f;"
            " font-size: 11px;"
            " font-weight: 600;"
            "}"
            "QLabel#ModuleKpiHoverPopupValue {"
            f" color: {segment_color.name()};"
            " font-size: 22px;"
            " font-weight: 700;"
            "}"
            "QLabel#ModuleKpiHoverPopupMeta {"
            " color: #7181a6;"
            " font-size: 10px;"
            "}"
        )
        self._hover_popup.adjustSize()

        anchor = self._segment_midpoint(segment)
        popup_rect = self._compute_popup_rect(anchor, self._hover_popup.width(), self._hover_popup.height())
        self._hover_popup_target_rect = popup_rect

        self._hover_popup.move(int(popup_rect.x()), int(popup_rect.y()))
        if self._detail_popup_enabled:
            self._hover_popup.show()
            self._hover_popup.raise_()
        else:
            self._hover_popup.hide()

    def _compute_popup_rect(self, anchor: QPointF, popup_width: int, popup_height: int) -> QRectF:
        popup_x = float(anchor.x()) - (popup_width / 2.0)
        if float(anchor.x()) < (self.width() / 2.0):
            popup_x -= 18.0
        else:
            popup_x += 18.0

        popup_y = float(anchor.y()) - float(popup_height) - 10.0
        popup_x = max(6.0, min(float(self.width()) - float(popup_width) - 6.0, popup_x))
        popup_y = max(6.0, min(float(self.height()) - float(popup_height) - 6.0, popup_y))
        return QRectF(popup_x, popup_y, float(popup_width), float(popup_height))

    def _hide_hover_popup(self) -> None:
        self._hover_popup.hide()
        self._hover_popup_target_rect = QRectF()

    def _popup_connector_target(self, popup_rect: QRectF, anchor: QPointF) -> QPointF:
        popup_center = popup_rect.center()
        dx = anchor.x() - popup_center.x()
        dy = anchor.y() - popup_center.y()

        if abs(dy) > abs(dx):
            target_x = min(max(anchor.x(), popup_rect.left() + 14.0), popup_rect.right() - 14.0)
            target_y = popup_rect.bottom() if dy > 0 else popup_rect.top()
            return QPointF(target_x, target_y)

        target_x = popup_rect.right() if dx > 0 else popup_rect.left()
        target_y = min(max(anchor.y(), popup_rect.top() + 14.0), popup_rect.bottom() - 14.0)
        return QPointF(target_x, target_y)

    def _draw_hover_connector(self, painter: QPainter, segment: dict[str, object]) -> None:
        if self._hover_popup_target_rect.isNull():
            return

        anchor = self._segment_midpoint(segment)
        popup_rect = QRectF(self._hover_popup_target_rect)
        target = self._popup_connector_target(popup_rect, anchor)
        line_color = QColor(segment.get("color") or QColor("#8595b5"))

        pen = QPen(line_color, 1.6, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)

        if abs(target.x() - anchor.x()) > abs(target.y() - anchor.y()):
            elbow = QPointF((anchor.x() + target.x()) / 2.0, anchor.y())
            elbow_2 = QPointF(elbow.x(), target.y())
        else:
            elbow = QPointF(anchor.x(), (anchor.y() + target.y()) / 2.0)
            elbow_2 = QPointF(target.x(), elbow.y())

        painter.drawLine(anchor, elbow)
        painter.drawLine(elbow, elbow_2)
        painter.drawLine(elbow_2, target)

        painter.setPen(QPen(line_color, 1.2))
        painter.setBrush(QColor("#ffffff"))
        painter.drawEllipse(anchor, 4.2, 4.2)
        painter.drawEllipse(target, 3.6, 3.6)

    def _segment_at(self, pos: QPoint) -> dict[str, object] | None:
        rect, center, radius, thickness = self._arc_geometry()
        dx = float(pos.x()) - center.x()
        dy = center.y() - float(pos.y())
        distance = math.hypot(dx, dy)
        if distance < radius - thickness or distance > radius + thickness:
            return None

        angle = math.degrees(math.atan2(dy, dx))
        angle = self._normalize_angle(angle)

        for segment in self._segment_geometry():
            if self._angle_in_segment(angle, segment):
                return segment
        return None

    def mouseMoveEvent(self, event) -> None:
        segment = self._segment_at(event.pos())
        segment_key = str(segment.get("key") or "") if segment else None
        if segment_key != self._hovered_segment:
            self._hovered_segment = segment_key
            if segment is not None:
                self._show_hover_popup(segment)
            else:
                self._hide_hover_popup()
            self.update()
        super().mouseMoveEvent(event)

    def leaveEvent(self, event) -> None:
        self._hovered_segment = None
        self._hide_hover_popup()
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect, center, radius, thickness = self._arc_geometry()
        if self._show_track:
            base_pen = QPen(self._track_color, thickness, Qt.SolidLine, Qt.RoundCap)
            painter.setPen(base_pen)
            track_start = int((360.0 - self.ARC_START_ANGLE) * 16)
            track_sweep = int(-self.ARC_SWEEP_TOTAL * 16)
            painter.drawArc(rect, track_start, track_sweep)

        for segment in self._segment_geometry():
            color = QColor(segment["color"])
            if segment.get("key") == self._hovered_segment:
                color = color.lighter(120)
            pen = QPen(color, thickness, Qt.SolidLine, Qt.RoundCap)
            painter.setPen(pen)
            start_angle = int((360.0 - float(segment["start"])) * 16)
            sweep_angle = int(-float(segment["sweep"]) * 16)
            painter.drawArc(rect, start_angle, sweep_angle)

        hovered_segment = None
        for segment in self._segment_geometry():
            if segment.get("key") == self._hovered_segment:
                hovered_segment = segment
                break
        if hovered_segment is not None:
            self._draw_hover_connector(painter, hovered_segment)

        painter.setPen(QColor("#0f1833"))
        value_font = QFont(self.font())
        value_font.setPointSize(29)
        value_font.setBold(True)
        painter.setFont(value_font)
        value_rect = QRectF(0.0, center.y() - 20.0, float(self.width()), 42.0)
        painter.drawText(value_rect, Qt.AlignHCenter | Qt.AlignVCenter, self._center_value)

        painter.setPen(QColor("#7181a6"))
        label_font = QFont(self.font())
        label_font.setPointSize(10)
        painter.setFont(label_font)
        subtitle_rect = QRectF(0.0, center.y() + 20.0, float(self.width()), 20.0)
        painter.drawText(
            subtitle_rect,
            Qt.AlignHCenter | Qt.AlignVCenter,
            self.lang_manager.translate(TranslationKeys.HOME_KPI_TOTAL_LABEL),
        )


class ModuleKpiCard(QFrame):
    CARD_WIDTH = 260

    def __init__(
        self,
        *,
        module_key: str,
        query_name: str,
        lang_manager=None,
        parent: QWidget | None = None,
        title_override: str | None = None,
        snapshot_override: dict[str, int] | None = None,
        root_field: str | None = None,
        show_breakdown: bool = True,
    ):
        super().__init__(parent)
        self.module_key = str(module_key or "").strip().lower()
        self.query_name = query_name
        self.lang_manager = lang_manager or LanguageManager()
        self.title_override = str(title_override or "").strip()
        self.snapshot_override = dict(snapshot_override or {}) if snapshot_override else None
        self.root_field = str(root_field or "").strip() or None
        self.show_breakdown = bool(show_breakdown)
        self._worker = None
        self._worker_thread = None
        self._request_id = 0

        self.setObjectName("SetupCard")
        self.setProperty("cardTone", self.module_key)
        self.setFixedWidth(self.CARD_WIDTH)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Minimum)

        self._build()
        self.retheme()
        self._set_loading_state()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(10)

        header = QFrame(self)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)

        self._icon = QLabel(header)
        icon_path = ModuleIconPaths.get_module_icon(self.module_key)
        if icon_path:
            self._icon.setPixmap(QPixmap(icon_path).scaled(18, 18, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        header_layout.addWidget(self._icon, 0, Qt.AlignTop)

        title_column = QVBoxLayout()
        title_column.setContentsMargins(0, 0, 0, 0)
        title_column.setSpacing(2)

        translated_module = self.lang_manager.translate_module_name(self.module_key)
        self._title = QLabel(self.title_override or translated_module, header)
        self._title.setObjectName("SetupCardTitle")
        title_column.addWidget(self._title)

        header_layout.addLayout(title_column, 1)

        root.addWidget(header)

        self._gauge = ModuleKpiGauge(lang_manager=self.lang_manager, parent=self)
        self._gauge.set_detail_popup_enabled(self.show_breakdown)
        root.addWidget(self._gauge, 0, Qt.AlignHCenter)

    def _apply_snapshot(self, snapshot) -> None:
        payload = snapshot or {}
        count = int(payload.get("count") or 0)
        overdue_count = int(payload.get("overdue_count") or 0)
        due_soon_count = int(payload.get("due_soon_count") or 0)
        self._gauge.set_counts(
            total_count=count,
            overdue_count=overdue_count,
            due_soon_count=due_soon_count,
            include_breakdown=self.show_breakdown,
        )

    def refresh(self) -> None:
        if self.snapshot_override is not None:
            self._cancel_worker()
            self._apply_snapshot(self.snapshot_override)
            return

        self._request_id += 1
        request_id = self._request_id
        self._cancel_worker()
        self._set_loading_state()

        worker = FunctionWorker(
            partial(
                ModuleKpiService.fetch_snapshot,
                self.module_key,
                self.query_name,
                self.lang_manager,
                root_field=self.root_field,
                include_due_counts=self.show_breakdown,
            )
        )
        worker.request_id = request_id
        worker.finished.connect(self._handle_success)
        worker.error.connect(self._handle_error)

        self._worker = worker
        self._worker_thread = start_worker(worker, on_thread_finished=self._clear_worker_refs)

    def deactivate(self) -> None:
        self._cancel_worker()

    def _clear_worker_refs(self) -> None:
        self._worker = None
        self._worker_thread = None

    def _cancel_worker(self) -> None:
        worker = self._worker
        thread = self._worker_thread
        if worker is not None:
            try:
                worker.finished.disconnect(self._handle_success)
            except Exception:
                pass
            try:
                worker.error.disconnect(self._handle_error)
            except Exception:
                pass
        if thread is not None and thread.isRunning():
            thread.quit()
            thread.wait(200)
        self._worker = None
        self._worker_thread = None

    def _handle_success(self, payload) -> None:
        worker = self._worker
        if worker is None or getattr(worker, "request_id", None) != self._request_id:
            return
        self._apply_snapshot(payload)

    def _handle_error(self, message: str) -> None:
        worker = self._worker
        if worker is None or getattr(worker, "request_id", None) != self._request_id:
            return
        self._gauge.set_error_state()

    def _set_loading_state(self) -> None:
        self._gauge.set_loading_state()

    def retheme(self) -> None:
        ThemeManager.apply_module_style(self, [QssPaths.SETUP_CARD])