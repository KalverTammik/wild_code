"""
Module-specific configurations for ExtraInfoWidget.
Each module type can define its own status columns and activities.
"""

from typing import List, Tuple, Dict, Any, Optional
from ...utils.url_manager import Module
from ...languages.language_manager import LanguageManager
from ...languages.translation_keys import TranslationKeys


class ModuleConfig:
    """Configuration class for different module types."""

    def __init__(self, module_type: str, *, title: str):
        self.module_type = module_type
        self.title = title
        self.columns: List[Dict[str, Any]] = []
        self.detailed_content = ""

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
        elif module_type == Module.CONTRACT.value:
            return ModuleConfigFactory._create_contract_config(item_id, lang_manager=lang_manager)
        else:
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

        # Tehtud column
        config.add_column(lm.translate(TranslationKeys.DATA_DISPLAY_WIDGETS_COLUMN_DONE), "#4CAF50", [
            (lm.translate(TranslationKeys.DATA_DISPLAY_WIDGETS_ACTIVITY_PLANNING), "✓"),
            (lm.translate(TranslationKeys.DATA_DISPLAY_WIDGETS_ACTIVITY_COMPILATION), "✓"),
            (lm.translate(TranslationKeys.DATA_DISPLAY_WIDGETS_ACTIVITY_REVIEW), "✓"),
            (lm.translate(TranslationKeys.DATA_DISPLAY_WIDGETS_ACTIVITY_APPROVAL), "✓"),
        ])

        # Töös column
        config.add_column(lm.translate(TranslationKeys.DATA_DISPLAY_WIDGETS_COLUMN_IN_PROGRESS), "#FF9800", [
            (lm.translate(TranslationKeys.DATA_DISPLAY_WIDGETS_ACTIVITY_TESTING), "⟳"),
            (lm.translate(TranslationKeys.DATA_DISPLAY_WIDGETS_ACTIVITY_DOCUMENTING), "⟳"),
            (lm.translate(TranslationKeys.DATA_DISPLAY_WIDGETS_ACTIVITY_OPTIMIZING), "⟳"),
        ])

        # Tegemata column
        config.add_column(lm.translate(TranslationKeys.DATA_DISPLAY_WIDGETS_COLUMN_TODO), "#F44336", [
            (lm.translate(TranslationKeys.DATA_DISPLAY_WIDGETS_ACTIVITY_PUBLISHING), "○"),
            (lm.translate(TranslationKeys.DATA_DISPLAY_WIDGETS_ACTIVITY_MONITORING), "○"),
            (lm.translate(TranslationKeys.DATA_DISPLAY_WIDGETS_ACTIVITY_ARCHIVING), "○"),
            (lm.translate(TranslationKeys.DATA_DISPLAY_WIDGETS_ACTIVITY_REPORTING), "○"),
        ])

        # Set detailed content
        config.set_detailed_content(
            lm.translate(TranslationKeys.DATA_DISPLAY_WIDGETS_PROJECT_DETAIL_CONTENT)
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

