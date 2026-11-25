"""
Module-specific configurations for ExtraInfoWidget: the detail view each module card opens.
"""

from typing import List, Dict, Any, Optional
from ...python.GraphQLQueryLoader import GraphQLQueryLoader
from ...python.api_client import APIClient
from ...python.responses import DataDisplayExtractors
from ...constants.module_names import Module
from ...languages.language_manager import LanguageManager
from ...languages.translation_keys import TranslationKeys
from .EasementPropertiesWidget import EasementPropertiesWidget
from .TaskDetailOverviewWidget import TaskDetailOverviewWidget
from .AsyncContentWidget import AsyncContentWidget


class ModuleConfig:
    """Detail view of one module card; without a loader the card has no detail handle."""

    def __init__(self):
        self.detail_loader = None
        self.detail_open_callback = None
        self.show_detail_handle = False

    def set_detail_loader(self, loader):
        self.detail_loader = loader

    def set_detail_open_callback(self, callback):
        self.detail_open_callback = callback

    def set_show_detail_handle(self, value: bool):
        self.show_detail_handle = bool(value)


class ModuleConfigFactory:
    """Factory for creating module-specific configurations."""

    # module type -> factory(item_id) -> ModuleConfig. A module whose detail
    # view lives in its own package registers it (ui/modules_registry.py), so this widget
    # package never imports modules/.
    _registered_factories: Dict[str, Any] = {}

    @classmethod
    def register(cls, module_type: str, factory) -> None:
        cls._registered_factories[module_type] = factory

    @staticmethod
    def _load_single_item_description(*, module_type: str, query_name: str, root_field: str, item_data: Optional[Dict[str, Any]]) -> str:
        item_id = DataDisplayExtractors.extract_item_id(item_data)
        if not item_id:
            return ""

        query = GraphQLQueryLoader().load_query_by_module(module_type, query_name)
        data = APIClient().send_query(query, {"id": item_id}) or {}
        root = data.get(root_field) if isinstance(data, dict) else None
        if not isinstance(root, dict):
            raise RuntimeError("Detail response is missing the requested item")
        return DataDisplayExtractors.extract_description(root)

    @staticmethod
    def _create_task_description_config(
        module_type: str,
        item_data: Dict[str, Any],
    ) -> ModuleConfig:
        config = ModuleConfig()
        config.set_detail_loader(
            lambda payload=item_data, current_module=module_type: AsyncContentWidget(
                lambda: ModuleConfigFactory._load_single_item_description(
                    module_type=Module.TASK.value,
                    query_name="w_tasks_module_data_by_item_id.graphql",
                    root_field="task",
                    item_data=payload,
                ),
                lambda description: TaskDetailOverviewWidget(
                    item_data=payload,
                    description_html=description,
                    module_name=current_module,
                ),
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
            raise RuntimeError("Detail response is missing the requested coordination")

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
    ) -> ModuleConfig:
        """Create configuration based on module type."""
        registered = ModuleConfigFactory._registered_factories.get(module_type)
        if registered is not None:
            return registered(item_id)
        if module_type == Module.CONTRACT.value:
            return ModuleConfigFactory._create_contract_config(item_id)
        if module_type == Module.COORDINATION.value:
            return ModuleConfigFactory._create_coordination_config(item_id)
        if module_type == Module.EASEMENT.value:
            return ModuleConfigFactory._create_easement_config(item_id)
        if module_type == Module.TASK.value:
            return ModuleConfigFactory._create_task_config(item_id)
        if module_type == Module.WORKS.value:
            return ModuleConfigFactory._create_works_config(item_id)
        if module_type == Module.ASBUILT.value:
            return ModuleConfigFactory._create_asbuilt_config(item_id)
        return ModuleConfig()

    @staticmethod
    def _create_contract_config(
        item_id: Dict[str, Any],
    ) -> ModuleConfig:
        """Create configuration for contract modules."""
        config = ModuleConfig()
        config.set_detail_loader(
            lambda payload=item_id: AsyncContentWidget(
                lambda: ModuleConfigFactory._load_single_item_description(
                    module_type=Module.CONTRACT.value,
                    query_name="w_contracts_module_data_by_item_id.graphql",
                    root_field="contract",
                    item_data=payload,
                ),
                lambda description: TaskDetailOverviewWidget(
                    item_data=payload,
                    description_html=description,
                    module_name=Module.CONTRACT.value,
                ),
            )
        )
        config.set_show_detail_handle(True)
        return config

    @staticmethod
    def _create_coordination_config(
        item_id: Dict[str, Any],
    ) -> ModuleConfig:
        """Create configuration for coordination modules."""
        config = ModuleConfig()
        config.set_detail_loader(
            lambda payload=item_id: AsyncContentWidget(
                lambda: ModuleConfigFactory._load_single_item_coordination_detail(
                    item_data=payload,
                ),
                lambda description: TaskDetailOverviewWidget(
                    item_data=payload,
                    description_html=description,
                    module_name=Module.COORDINATION.value,
                ),
            )
        )
        config.set_show_detail_handle(True)
        return config

    @staticmethod
    def _create_works_config(
        item_id: Dict[str, Any],
    ) -> ModuleConfig:
        """Create configuration for works modules."""
        return ModuleConfigFactory._create_task_description_config(
            Module.WORKS.value,
            item_id,
        )

    @staticmethod
    def _create_task_config(
        item_id: Dict[str, Any],
    ) -> ModuleConfig:
        return ModuleConfigFactory._create_task_description_config(
            Module.TASK.value,
            item_id,
        )

    @staticmethod
    def _create_easement_config(
        item_id: Dict[str, Any],
    ) -> ModuleConfig:
        config = ModuleConfig()
        config.set_detail_loader(
            lambda payload=item_id: TaskDetailOverviewWidget(
                item_data=payload,
                detail_widget=EasementPropertiesWidget(
                    item_data=payload,
                ),
                module_name=Module.EASEMENT.value,
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
    ) -> ModuleConfig:
        """Create configuration for asbuilt modules."""
        return ModuleConfigFactory._create_task_description_config(
            Module.ASBUILT.value,
            item_id,
        )

