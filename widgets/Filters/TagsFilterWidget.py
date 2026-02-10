# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Optional, Union

from PyQt5.QtWidgets import QWidget

from ...languages.language_manager import LanguageManager
from ...languages.translation_keys import TranslationKeys
from ...modules.Settings.SettinsUtils.SettingsLogic import SettingsLogic
from ...utils.url_manager import ModuleSupports
from .BaseSingleFilterWidget import BaseSingleFilterWidget


class TagsFilterWidget(BaseSingleFilterWidget):
    """Tags filter backed by BaseSingleFilterWidget."""

    def __init__(
        self,
        module_name: Union[str, object],
        lang_manager: Optional[LanguageManager] = None,
        parent: Optional[QWidget] = None,
        *,
        auto_load: bool = True,
        settings_logic: Optional[SettingsLogic] = None,
    ) -> None:
        translator = lang_manager or LanguageManager()
        label_text = translator.translate(TranslationKeys.TAGS_FILTER)
        super().__init__(
            module_name,
            label_text,
            "TagsFilterCombo",
            ModuleSupports.TAGS.value,
            parent=parent,
            auto_load=auto_load,
            variant="tags-filter",
            settings_logic=settings_logic,
            lang_manager=lang_manager,
        )
