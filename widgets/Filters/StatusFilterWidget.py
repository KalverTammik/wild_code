# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Optional, Union

from PyQt5.QtWidgets import QWidget

from ...languages.translation_keys import TranslationKeys
from ...languages.language_manager import LanguageManager
from ...modules.Settings.SettinsUtils.SettingsLogic import SettingsLogic
from ...utils.url_manager import ModuleSupports
from .BaseSingleFilterWidget import BaseSingleFilterWidget


class StatusFilterWidget(BaseSingleFilterWidget):
    """Status filter backed by BaseSingleFilterWidget."""

    def __init__(
        self,
        module_name: Union[str, object],
        parent: Optional[QWidget] = None,
        *,
        auto_load: bool = True,
        settings_logic: Optional[SettingsLogic] = None,
    ) -> None:
        label_text = LanguageManager().translate(TranslationKeys.STATUS_FILTER)
        super().__init__(
            module_name,
            label_text,
            "StatusFilterCombo",
            ModuleSupports.STATUSES.value,
            parent=parent,
            auto_load=auto_load,
            variant="status-filter",
            settings_logic=settings_logic,
        )
