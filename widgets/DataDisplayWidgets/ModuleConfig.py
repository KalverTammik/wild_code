"""
Module-specific configurations for ExtraInfoWidget.
Each module type can define its own status columns and activities.
"""

from typing import List, Tuple, Dict, Any, Optional
from ...utils.url_manager import Module
from ...languages.language_manager import LanguageManager
from ...languages.translation_keys import TranslationKeys
from ...modules.projects.project_board_overview_service import ProjectBoardOverviewService
from ...modules.projects.project_board_widgets import ProjectBoardOverviewWidget


class ModuleConfig:
    """Configuration class for different module types."""

    def __init__(self, module_type: str, *, title: str):
        self.module_type = module_type
        self.title = title
        self.columns: List[Dict[str, Any]] = []
        self.summary_text = ""
        self.detailed_content = ""
        self.detailed_widget = None
        self.detail_loader = None

    def add_column(self, title: str, color: str, activities: List[Tuple[str, str]]):
        """Add a status column to the configuration."""
        self.columns.append({
            'title': title,
            'color': color,
            'activities': activities
        })

    def set_title(self, title: str):
        """Set the widget title."""
        self.title = title

    def set_detailed_content(self, content: str):
        """Set the detailed overview content."""
        self.detailed_content = content

    def set_summary_text(self, text: str):
        self.summary_text = str(text or "")

    def set_detail_loader(self, loader):
        self.detail_loader = loader

    def load_detailed_content(self):
        if callable(self.detail_loader):
            loaded = self.detail_loader()
            if loaded is not None:
                self.detailed_widget = loaded if hasattr(loaded, "setParent") else None
            if isinstance(loaded, str) and loaded.strip():
                self.detailed_content = loaded
        return self.detailed_widget or self.detailed_content


class ModuleConfigFactory:
    """Factory for creating module-specific configurations."""

    @staticmethod
    def create_config(
        module_type: str,
        item_id: Dict[str, Any] = None,
        *,
        lang_manager: Optional[LanguageManager] = None,
    ) -> ModuleConfig:
        """Create configuration based on module type."""
        if module_type == Module.PROJECT.value:
            return ModuleConfigFactory._create_project_config(item_id, lang_manager=lang_manager)
        if module_type == Module.CONTRACT.value:
            return ModuleConfigFactory._create_contract_config(item_id, lang_manager=lang_manager)
        if module_type == Module.EASEMENT.value:
            return ModuleConfigFactory._create_easement_config(item_id, lang_manager=lang_manager)
        if module_type == Module.WORKS.value:
            return ModuleConfigFactory._create_works_config(item_id, lang_manager=lang_manager)
        if module_type == Module.ASBUILT.value:
            return ModuleConfigFactory._create_asbuilt_config(item_id, lang_manager=lang_manager)
        return ModuleConfigFactory._create_contract_config(item_id, lang_manager=lang_manager)

    @staticmethod
    def _create_project_config(
        item_id: Dict[str, Any],
        *,
        lang_manager: Optional[LanguageManager] = None,
    ) -> ModuleConfig:
        """Create configuration for project modules."""
        lm = lang_manager or LanguageManager()
        config = ModuleConfig(
            Module.PROJECT.value,
            title=lm.translate(
                TranslationKeys.DATA_DISPLAY_WIDGETS_PROJECT_OVERVIEW_TITLE,
            ),
        )

        config.set_summary_text(
            lm.translate(TranslationKeys.PROJECT_BOARD_DETAILS_LOAD_HINT)
        )
        config.set_detail_loader(
            lambda payload=item_id, lang=lm: ProjectBoardOverviewWidget(
                ProjectBoardOverviewService.build_project_board_data(
                    payload,
                    lang_manager=lang,
                )
            )
        )

        return config

    @staticmethod
    def _create_contract_config(
        item_id: Dict[str, Any],
        *,
        lang_manager: Optional[LanguageManager] = None,
    ) -> ModuleConfig:
        """Create configuration for contract modules."""
        lm = lang_manager or LanguageManager()
        config = ModuleConfig(
            Module.CONTRACT.value,
            title=lm.translate(
                TranslationKeys.DATA_DISPLAY_WIDGETS_CONTRACT_OVERVIEW_TITLE,
            ),
        )

        # Lepingu staatused
        config.add_column(lm.translate(TranslationKeys.DATA_DISPLAY_WIDGETS_COLUMN_SIGNED), "#4CAF50", [
            (lm.translate(TranslationKeys.DATA_DISPLAY_WIDGETS_ACTIVITY_CONTRACT_DRAFTING), "✓"),
            (lm.translate(TranslationKeys.DATA_DISPLAY_WIDGETS_ACTIVITY_PARTY_CONSENT), "✓"),
            (lm.translate(TranslationKeys.DATA_DISPLAY_WIDGETS_ACTIVITY_NOTARIAL_CONFIRM), "✓"),
        ])

        config.add_column(lm.translate(TranslationKeys.DATA_DISPLAY_WIDGETS_COLUMN_PROCESSING), "#FF9800", [
            (lm.translate(TranslationKeys.DATA_DISPLAY_WIDGETS_ACTIVITY_LEGAL_REVIEW), "⟳"),
            (lm.translate(TranslationKeys.DATA_DISPLAY_WIDGETS_ACTIVITY_FINANCIAL_CHECK), "⟳"),
        ])

        config.add_column(lm.translate(TranslationKeys.DATA_DISPLAY_WIDGETS_COLUMN_PENDING), "#F44336", [
            (lm.translate(TranslationKeys.DATA_DISPLAY_WIDGETS_ACTIVITY_SIGNATURES), "○"),
            (lm.translate(TranslationKeys.DATA_DISPLAY_WIDGETS_ACTIVITY_COMPLETION_CHECK), "○"),
        ])

        config.set_detailed_content(
            lm.translate(TranslationKeys.DATA_DISPLAY_WIDGETS_CONTRACT_DETAIL_CONTENT)
        )

        return config

    @staticmethod
    def _create_works_config(
        item_id: Dict[str, Any],
        *,
        lang_manager: Optional[LanguageManager] = None,
    ) -> ModuleConfig:
        """Create configuration for works modules."""
        lm = lang_manager or LanguageManager()
        config = ModuleConfig(
            Module.WORKS.value,
            title=lm.translate(
                TranslationKeys.DATA_DISPLAY_WIDGETS_WORKS_OVERVIEW_TITLE,
            ),
        )
        config.set_detailed_content(
            lm.translate(TranslationKeys.DATA_DISPLAY_WIDGETS_WORKS_DETAIL_CONTENT)
        )
        return config

    @staticmethod
    def _create_easement_config(
        item_id: Dict[str, Any],
        *,
        lang_manager: Optional[LanguageManager] = None,
    ) -> ModuleConfig:
        lm = lang_manager or LanguageManager()
        config = ModuleConfig(
            Module.EASEMENT.value,
            title=lm.translate(
                TranslationKeys.DATA_DISPLAY_WIDGETS_EASEMENT_OVERVIEW_TITLE,
            ),
        )
        config.set_detailed_content(
            lm.translate(TranslationKeys.DATA_DISPLAY_WIDGETS_EASEMENT_DETAIL_CONTENT)
        )
        return config

    @staticmethod
    def _create_asbuilt_config(
        item_id: Dict[str, Any],
        *,
        lang_manager: Optional[LanguageManager] = None,
    ) -> ModuleConfig:
        """Create configuration for asbuilt modules."""
        lm = lang_manager or LanguageManager()
        config = ModuleConfig(
            Module.ASBUILT.value,
            title=lm.translate(
                TranslationKeys.DATA_DISPLAY_WIDGETS_ASBUILT_OVERVIEW_TITLE,
            ),
        )
        config.set_detailed_content(
            lm.translate(TranslationKeys.DATA_DISPLAY_WIDGETS_ASBUILT_DETAIL_CONTENT)
        )
        return config

