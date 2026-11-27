"""Detail view of a project card: the project board, loaded in the background.

Registered with ModuleConfigFactory in ui/modules_registry.py.
"""
from __future__ import annotations

from typing import Any, Dict

from qgis.PyQt.QtWidgets import QLabel, QVBoxLayout, QWidget

from ...constants.file_paths import QssPaths
from ...languages.language_manager import LanguageManager
from ...languages.translation_keys import TranslationKeys
from ...ui.theme_manager import ThemeManager
from ...widgets.DataDisplayWidgets.AsyncContentWidget import AsyncContentWidget
from ...widgets.DataDisplayWidgets.ModuleConfig import ModuleConfig
from .project_board_overview_service import ProjectBoardOverviewService
from .project_board_widgets import ProjectBoardOverviewWidget


def create_project_config(
    item_id: Dict[str, Any],
) -> ModuleConfig:
    """Create configuration for project modules."""
    lm = LanguageManager()
    config = ModuleConfig()

    def _project_detail_widget(board_data):
        wrapper = QWidget()
        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        intro = QLabel(
            lm.translate(TranslationKeys.PROJECT_BOARD_DETAILS_LOAD_HINT),
            wrapper,
        )
        intro.setWordWrap(True)
        intro.setObjectName("ProjectBoardDetailIntro")
        layout.addWidget(intro)

        board_widget = ProjectBoardOverviewWidget(board_data, wrapper)
        layout.addWidget(board_widget)

        ThemeManager.apply_module_style(wrapper, [QssPaths.MODULE_INFO])
        return wrapper

    config.set_detail_loader(
        lambda: AsyncContentWidget(
            lambda: ProjectBoardOverviewService.build_project_board_data(item_id),
            _project_detail_widget,
        )
    )
    config.set_show_detail_handle(True)

    return config
