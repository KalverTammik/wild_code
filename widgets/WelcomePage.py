from qgis.PyQt.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QFrame, QScrollArea
from ..languages.language_manager import LanguageManager
from ..ui.mixins.token_mixin import TokenMixin
from ..constants.module_names import Module
from ..ui.theme_manager import ThemeManager
from ..constants.file_paths import ConfigPaths
from .ModuleKpiCard import ModuleKpiCard
from .Tags.tag_prototype_panel import TagPrototypePanel


class WelcomePage(TokenMixin, QWidget):

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        TokenMixin.__init__(self)
        self.setObjectName("WelcomePage")
        self.lang_manager = LanguageManager()
        self._kpi_cards = []

        self._kpi_grid = QGridLayout()
        self._kpi_grid.setContentsMargins(0, 0, 0, 0)
        self._kpi_grid.setHorizontalSpacing(12)
        self._kpi_grid.setVerticalSpacing(12)

        card_specs = [
            {
                "module_key": Module.PROPERTY.value,
                "query_name": "CountPropertiesForKpi.graphql",
                "root_field": "properties",
                "show_breakdown": False,
            },
            {
                "module_key": Module.PROJECT.value,
                "query_name": "CountProjectsForKpi.graphql",
                "show_breakdown": True,
            },
            {
                "module_key": Module.CONTRACT.value,
                "query_name": "CountContractsForKpi.graphql",
                "show_breakdown": True,
            },
            {
                "module_key": Module.COORDINATION.value,
                "query_name": "CountCoordinationsForKpi.graphql",
                "show_breakdown": True,
            },
            {
                "module_key": Module.EASEMENT.value,
                "query_name": "CountEasementsForKpi.graphql",
                "show_breakdown": False,
            },
            {
                "module_key": Module.WORKS.value,
                "query_name": "CountTasksForKpi.graphql",
                "root_field": "tasks",
                "show_breakdown": False,
            },
            {
                "module_key": Module.ASBUILT.value,
                "query_name": "CountTasksForKpi.graphql",
                "root_field": "tasks",
                "show_breakdown": False,
            },
        ]

        column_count = 3
        for index, spec in enumerate(card_specs):
            card = ModuleKpiCard(
                module_key=spec["module_key"],
                query_name=spec["query_name"],
                parent=self,
                root_field=spec.get("root_field"),
                show_breakdown=bool(spec.get("show_breakdown", True)),
            )
            self._kpi_cards.append(card)
            row = index // column_count
            column = index % column_count
            self._kpi_grid.addWidget(card, row, column)

        self._kpi_grid.setColumnStretch(column_count, 1)

        kpi_shell = QFrame(self)
        kpi_shell.setObjectName("WelcomeKpiShell")
        kpi_shell.setLayout(self._kpi_grid)

        # A prototype under review: only development builds show it, above the KPI cards and scrollable.
        self._tag_prototype = None
        if ConfigPaths.IS_DEV:
            outer = QVBoxLayout(self)
            outer.setContentsMargins(0, 0, 0, 0)
            scroll = QScrollArea(self)
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.Shape.NoFrame)
            page = QWidget(scroll)
            scroll.setWidget(page)
            outer.addWidget(scroll)
            layout = QVBoxLayout(page)
            self._tag_prototype = TagPrototypePanel(page)
            layout.addWidget(self._tag_prototype)
        else:
            layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)
        layout.addWidget(kpi_shell)
        layout.addStretch(1)

        self.retheme()

    def activate(self):
        for card in self._kpi_cards:
            card.refresh()
        if self._tag_prototype is not None:
            self._tag_prototype.activate()

    def deactivate(self):
        for card in self._kpi_cards:
            card.deactivate()
        if self._tag_prototype is not None:
            self._tag_prototype.deactivate()

    def get_widget(self):
        """Return self as the widget for module system compatibility."""
        return self

    def retheme(self):
        ThemeManager.apply_module_style(self)
        for card in self._kpi_cards:
            card.retheme()
        if self._tag_prototype is not None:
            self._tag_prototype.retheme()
