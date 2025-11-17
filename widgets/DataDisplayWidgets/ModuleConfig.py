"""
Module-specific configurations for ExtraInfoWidget.
Each module type can define its own status columns and activities.
"""

from typing import List, Tuple, Dict, Any
from ...utils.url_manager import Module


class ModuleConfig:
    """Configuration class for different module types."""

    def __init__(self, module_type: str):
        self.module_type = module_type
        self.title = "Tegevuste ülevaade"
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
    def create_config(module_type: str, item_id: Dict[str, Any] = None) -> ModuleConfig:
        """Create configuration based on module type."""
        if module_type == Module.PROJECT.value:
            return ModuleConfigFactory._create_project_config(item_id)
        elif module_type == Module.CONTRACT.value:
            return ModuleConfigFactory._create_contract_config(item_id)

    @staticmethod
    def _create_project_config(item_id: Dict[str, Any]) -> ModuleConfig:
        """Create configuration for project modules."""
        config = ModuleConfig(Module.PROJECT.value)
        #print(f"[ModuleConfigFactory] Creating project config for item: {item_id}")
        config.set_title("Projekti tegevuste ülevaade")

        # Tehtud column
        config.add_column("Tehtud", "#4CAF50", [
            ("Planeerimine", "✓"),
            ("Koostamine", "✓"),
            ("Ülevaatamine", "✓"),
            ("Kinnitamine", "✓")
        ])

        # Töös column
        config.add_column("Töös", "#FF9800", [
            ("Testimine", "⟳"),
            ("Dokumenteerimine", "⟳"),
            ("Optimeerimine", "⟳")
        ])

        # Tegemata column
        config.add_column("Tegemata", "#F44336", [
            ("Avaldamine", "○"),
            ("Jälgimine", "○"),
            ("Arhiveerimine", "○"),
            ("Raporteerimine", "○")
        ])

        # Set detailed content
        config.set_detailed_content("""
        <h3>Projekti Detailne Ülevaade</h3>
        <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.</p>

        <h4>Projekti Faasid</h4>
        <ul>
        <li><b>Planeerimine:</b> Projekti eesmärkide ja ulatuse määramine</li>
        <li><b>Koostamine:</b> Projekti komponentide arendamine</li>
        <li><b>Testimine:</b> Funktsionaalsuse kontrollimine</li>
        <li><b>Avaldamine:</b> Projekti lõplik väljastamine</li>
        </ul>

        <h4>Projekti Statistika</h4>
        <p>Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.</p>
        """)

        return config

    @staticmethod
    def _create_contract_config(item_id: Dict[str, Any]) -> ModuleConfig:
        """Create configuration for contract modules."""
        config = ModuleConfig(Module.CONTRACT.value)
        config.set_title("Lepingu tegevuste ülevaade")

        # Lepingu staatused
        config.add_column("Allkirjastatud", "#4CAF50", [
            ("Lepingu koostamine", "✓"),
            ("Osapoolte nõusolek", "✓"),
            ("Notariaalne kinnitamine", "✓")
        ])

        config.add_column("Töötlemisel", "#FF9800", [
            ("Juriidiline ülevaatus", "⟳"),
            ("Finantskontroll", "⟳")
        ])

        config.add_column("Ootel", "#F44336", [
            ("Osapoolte allkirjad", "○"),
            ("Täitmise kontroll", "○")
        ])

        config.set_detailed_content("""
        <h3>Lepingu Detailne Ülevaade</h3>
        <p>Contract management and legal documentation overview.</p>

        <h4>Lepingu Faasid</h4>
        <ul>
        <li><b>Allkirjastatud:</b> Legal binding agreements</li>
        <li><b>Töötlemisel:</b> Under legal and financial review</li>
        <li><b>Ootel:</b> Awaiting signatures or completion</li>
        </ul>
        """)

        return config

