# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import List, Optional

from PyQt5.QtWidgets import QWidget

from ..task_shared.task_module_base_ui import TaskModuleBaseUI
from ...languages.translation_keys import TranslationKeys
from ...utils.url_manager import Module


class AsBuiltModule(TaskModuleBaseUI):
    def __init__(
        self,
        name: Optional[str] = None,
        lang_manager: Optional[object] = None,
        parent: Optional[QWidget] = None,
        qss_files: Optional[List[str]] = None,
    ) -> None:
        super().__init__(
            module_enum=Module.ASBUILT,
            empty_state_key=TranslationKeys.NO_ASBUILT_FOUND,
            lang_manager=lang_manager,
            parent=parent,
            qss_files=qss_files,
        )
