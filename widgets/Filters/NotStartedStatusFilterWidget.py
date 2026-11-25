from __future__ import annotations

from typing import Optional, Union

from PyQt5.QtWidgets import QWidget

from ...languages.language_manager import LanguageManager
from ...languages.translation_keys import TranslationKeys
from ...utils.settings_logic import SettingsLogic
from ...utils.project_board_status_rules import ProjectBoardStatusRules
from .StatusFilterWidget import StatusFilterWidget


class NotStartedStatusFilterWidget(StatusFilterWidget):
    def __init__(
        self,
        module_name: Union[str, object],
        parent: Optional[QWidget] = None,
        *,
        auto_load: bool = True,
        settings_logic: Optional[SettingsLogic] = None,
    ) -> None:
        normalized_module = getattr(module_name, "value", module_name)
        lang = LanguageManager()
        label_text = lang.translate(TranslationKeys.PROJECT_BOARD_NOT_STARTED_STATUS_TITLE)
        super().__init__(
            module_name,
            parent=parent,
            auto_load=auto_load,
            settings_logic=settings_logic,
            label_text=label_text,
            object_name="NotStartedStatusFilterCombo",
            selected_ids_loader=lambda: list(ProjectBoardStatusRules.load_not_started_status_ids(normalized_module)),
        )
