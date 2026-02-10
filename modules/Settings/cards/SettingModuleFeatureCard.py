from __future__ import annotations

from typing import Callable, Optional, Tuple, TypeVar
from ....languages.language_manager import LanguageManager
from PyQt5.QtWidgets import QGroupBox, QHBoxLayout, QLabel, QVBoxLayout, QFrame, QWidget

WidgetT = TypeVar("WidgetT")



class SettingsModuleFeatureCard:

	@staticmethod
	def build_filter_group(
		*,
		parent: QWidget,
		title_text: str,
		lang_manager: Optional[LanguageManager] = None,
		widget_factory: Callable[[QWidget], WidgetT],
		description_text: Optional[str] = None,
		group_object_name: Optional[str] = None,
		container_object_name: Optional[str] = None,
		explanation_object_name: str = "GroupExplanation",
		description_min_width: int = 200,
		container_margins: Tuple[int, int, int, int] = (0, 0, 0, 0),
		container_spacing: int = 4,
	) -> Tuple[QGroupBox, WidgetT]:
		"""Construct a standardized filter block containing a widget and optional blurb."""

		group = QGroupBox(title_text, parent)
		if group_object_name:
			group.setObjectName(group_object_name)

		layout = QHBoxLayout(group)
		layout.setContentsMargins(4, 4, 4, 4)
		layout.setSpacing(6)

		container = QFrame(group)
		if container_object_name:
			container.setObjectName(container_object_name)
		container_layout = QVBoxLayout(container)
		container_layout.setContentsMargins(*container_margins)
		container_layout.setSpacing(container_spacing)


		widget = widget_factory(container)
		container_layout.addWidget(widget)
		layout.addWidget(container, 2)

		if description_text:
			label = QLabel(description_text, group)
			label.setObjectName(explanation_object_name)
			label.setWordWrap(True)
			label.setStyleSheet("color: #888; font-size: 11px; padding: 4px 0px;")
			label.setMinimumWidth(description_min_width)
			layout.addWidget(label, 1)

		return group, widget
