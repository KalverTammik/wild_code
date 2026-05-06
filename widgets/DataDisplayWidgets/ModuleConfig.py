"""
Module-specific configurations for ExtraInfoWidget.
Each module type can define its own status columns and activities.
"""

from typing import List, Tuple, Dict, Any, Optional
from ...python.GraphQLQueryLoader import GraphQLQueryLoader
from ...python.api_client import APIClient
from ...python.responses import DataDisplayExtractors
from ...utils.url_manager import Module
from ...languages.language_manager import LanguageManager
from ...languages.translation_keys import TranslationKeys
from ...modules.projects.project_board_overview_service import ProjectBoardOverviewService
from ...modules.projects.project_board_widgets import ProjectBoardOverviewWidget
from .EasementPropertiesWidget import EasementPropertiesWidget
from .TaskDetailOverviewWidget import TaskDetailOverviewWidget


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
        self.detail_open_callback = None
        self.show_detail_handle = False

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

    def set_detail_open_callback(self, callback):
        self.detail_open_callback = callback

    def set_show_detail_handle(self, value: bool):
        self.show_detail_handle = bool(value)

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
    def _load_single_item_description(*, module_type: str, query_name: str, root_field: str, item_data: Optional[Dict[str, Any]]) -> str:
        item_id = DataDisplayExtractors.extract_item_id(item_data)
        if not item_id:
            return ""

        query = GraphQLQueryLoader().load_query_by_module(module_type, query_name)
        data = APIClient().send_query(query, {"id": item_id}) or {}
        root = data.get(root_field) if isinstance(data, dict) else None
        if not isinstance(root, dict):
            return ""
        return DataDisplayExtractors.extract_description(root)

    @staticmethod
    def _create_task_description_config(
        module_type: str,
        item_data: Dict[str, Any],
        *,
        lang_manager: Optional[LanguageManager] = None,
    ) -> ModuleConfig:
        lm = lang_manager or LanguageManager()
        config = ModuleConfig(module_type, title="")
        config.set_detail_loader(
            lambda payload=item_data, lang=lm, current_module=module_type: TaskDetailOverviewWidget(
                item_data=payload,
                description_html=ModuleConfigFactory._load_single_item_description(
                    module_type=Module.TASK.value,
                    query_name="w_tasks_module_data_by_item_id.graphql",
                    root_field="task",
                    item_data=payload,
                ),
                module_name=current_module,
                lang_manager=lang,
            )
        )
        config.set_show_detail_handle(True)
        return config

    @staticmethod
    def _load_single_item_coordination_detail(*, item_data: Optional[Dict[str, Any]]) -> str:
        item_id = DataDisplayExtractors.extract_item_id(item_data)
        if not item_id:
            return ""

        query = GraphQLQueryLoader().load_query_by_module(
            Module.COORDINATION.value,
            "W_coordination_id.graphql",
        )
        data = APIClient().send_query(query, {"id": item_id}) or {}
        root = data.get("coordination") if isinstance(data, dict) else None
        if not isinstance(root, dict):
            return ""

        description = DataDisplayExtractors.extract_description(root).strip()
        terms = str(root.get("terms") or "").strip()
        terms_heading = LanguageManager().translate(TranslationKeys.DATA_DISPLAY_WIDGETS_TERMS_HEADING)

        sections: List[str] = []
        if description:
            sections.append(description)
        if terms:
            sections.append(f"<h3>{terms_heading}</h3>{terms}")
        return "".join(sections)

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
        if module_type == Module.COORDINATION.value:
            return ModuleConfigFactory._create_coordination_config(item_id, lang_manager=lang_manager)
        if module_type == Module.EASEMENT.value:
            return ModuleConfigFactory._create_easement_config(item_id, lang_manager=lang_manager)
        if module_type == Module.TASK.value:
            return ModuleConfigFactory._create_task_config(item_id, lang_manager=lang_manager)
        if module_type == Module.WORKS.value:
            return ModuleConfigFactory._create_works_config(item_id, lang_manager=lang_manager)
        if module_type == Module.ASBUILT.value:
            return ModuleConfigFactory._create_asbuilt_config(item_id, lang_manager=lang_manager)
        return ModuleConfig(str(module_type or ""), title="")

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
            lambda payload=item_id, lang=lm: TaskDetailOverviewWidget(
                item_data=payload,
                detail_widget=ProjectBoardOverviewWidget(
                    ProjectBoardOverviewService.build_project_board_data(
                        payload,
                        lang_manager=lang,
                    )
                ),
                module_name=Module.PROJECT.value,
                lang_manager=lang,
            )
        )
        config.set_show_detail_handle(True)

        return config

    @staticmethod
    def _create_contract_config(
        item_id: Dict[str, Any],
        *,
        lang_manager: Optional[LanguageManager] = None,
    ) -> ModuleConfig:
        """Create configuration for contract modules."""
        lm = lang_manager or LanguageManager()
        config = ModuleConfig(Module.CONTRACT.value, title="")
        config.set_detail_loader(
            lambda payload=item_id, lang=lm: TaskDetailOverviewWidget(
                item_data=payload,
                description_html=ModuleConfigFactory._load_single_item_description(
                    module_type=Module.CONTRACT.value,
                    query_name="w_contracts_module_data_by_item_id.graphql",
                    root_field="contract",
                    item_data=payload,
                ),
                module_name=Module.CONTRACT.value,
                lang_manager=lang,
            )
        )
        config.set_show_detail_handle(True)
        return config

    @staticmethod
    def _create_coordination_config(
        item_id: Dict[str, Any],
        *,
        lang_manager: Optional[LanguageManager] = None,
    ) -> ModuleConfig:
        """Create configuration for coordination modules."""
        lm = lang_manager or LanguageManager()
        config = ModuleConfig(Module.COORDINATION.value, title="")
        config.set_detail_loader(
            lambda payload=item_id, lang=lm: TaskDetailOverviewWidget(
                item_data=payload,
                description_html=ModuleConfigFactory._load_single_item_coordination_detail(
                    item_data=payload,
                ),
                module_name=Module.COORDINATION.value,
                lang_manager=lang,
            )
        )
        config.set_show_detail_handle(True)
        return config

    @staticmethod
    def _create_works_config(
        item_id: Dict[str, Any],
        *,
        lang_manager: Optional[LanguageManager] = None,
    ) -> ModuleConfig:
        """Create configuration for works modules."""
        return ModuleConfigFactory._create_task_description_config(
            Module.WORKS.value,
            item_id,
            lang_manager=lang_manager,
        )

    @staticmethod
    def _create_task_config(
        item_id: Dict[str, Any],
        *,
        lang_manager: Optional[LanguageManager] = None,
    ) -> ModuleConfig:
        return ModuleConfigFactory._create_task_description_config(
            Module.TASK.value,
            item_id,
            lang_manager=lang_manager,
        )

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
        config.set_detail_loader(
            lambda payload=item_id, lang=lm: TaskDetailOverviewWidget(
                item_data=payload,
                detail_widget=EasementPropertiesWidget(
                    item_data=payload,
                    lang_manager=lang,
                ),
                module_name=Module.EASEMENT.value,
                lang_manager=lang,
            )
        )
        config.set_detail_open_callback(
            lambda payload=item_id: EasementPropertiesWidget.show_connected_properties_on_map(payload)
        )
        config.set_show_detail_handle(True)
        return config

    @staticmethod
    def _create_asbuilt_config(
        item_id: Dict[str, Any],
        *,
        lang_manager: Optional[LanguageManager] = None,
    ) -> ModuleConfig:
        """Create configuration for asbuilt modules."""
        return ModuleConfigFactory._create_task_description_config(
            Module.ASBUILT.value,
            item_id,
            lang_manager=lang_manager,
        )

