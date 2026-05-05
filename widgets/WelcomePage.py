from PyQt5.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QFrame
from ..languages.language_manager import LanguageManager
from ..ui.mixins.token_mixin import TokenMixin
from ..utils.url_manager import Module
from ..widgets.theme_manager import ThemeManager
from .ModuleKpiCard import ModuleKpiCard


class WelcomePage(TokenMixin, QWidget):

    def __init__(self, lang_manager=None, parent=None):
        QWidget.__init__(self, parent)
        TokenMixin.__init__(self)
        self.setObjectName("WelcomePage")
        self.lang_manager = lang_manager or LanguageManager()
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
                lang_manager=self.lang_manager,
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

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)
        layout.addWidget(kpi_shell)
        layout.addStretch(1)

        self.retheme()

    def activate(self):
        for card in self._kpi_cards:
            refresh = getattr(card, "refresh", None)
            if callable(refresh):
                refresh()

    def deactivate(self):
        for card in self._kpi_cards:
            deactivate = getattr(card, "deactivate", None)
            if callable(deactivate):
                deactivate()

    def get_widget(self):
        """Return self as the widget for module system compatibility."""
        return self

    def retheme(self):
        ThemeManager.apply_module_style(self)
        for card in self._kpi_cards:
            retheme = getattr(card, "retheme", None)
            if callable(retheme):
                retheme()
