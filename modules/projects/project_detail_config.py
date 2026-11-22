"""Detail view of a project card: the project board, loaded in the background.

Registered with ModuleConfigFactory in ui/modules_registry.py.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from PyQt5.QtWidgets import QLabel, QVBoxLayout, QWidget

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
    *,
    lang_manager: Optional[LanguageManager] = None,
) -> ModuleConfig:
    """Create configuration for project modules."""
    lm = lang_manager or LanguageManager()
    config = ModuleConfig()

    def _project_detail_widget(board_data, lang=lm):
        wrapper = QWidget()
        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        intro = QLabel(
            lang.translate(TranslationKeys.PROJECT_BOARD_DETAILS_LOAD_HINT),
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
            lambda: ProjectBoardOverviewService.build_project_board_data(item_id, lang_manager=lm),
            _project_detail_widget,
            lang_manager=lm,
        )
    )
    config.set_show_detail_handle(True)

    return config
