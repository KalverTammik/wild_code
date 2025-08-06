from PyQt5.QtWidgets import QWidget, QVBoxLayout
from ...languages.language_manager import LanguageManager
from ...widgets.theme_manager import ThemeManager
from .logic.HinnapakkujaLogic import HinnapakkujaLogic
from .ui.HinnapakkujaForm import HinnapakkujaForm
from .ui.HinnapakkujaOfferView import HinnapakkujaOfferView

class HinnapakkujaUI(QWidget):
    def __init__(self, lang_manager: LanguageManager, theme_manager: ThemeManager, theme_dir=None, qss_files=None):
        super().__init__()
        from ...module_manager import HINNAPAKKUJA_MODULE
        self.name = HINNAPAKKUJA_MODULE
        self.lang_manager = lang_manager
        self.theme_manager = theme_manager
        from ...constants.file_paths import StylePaths
        self.theme_dir = theme_dir or StylePaths.DARK
        from ...constants.file_paths import QssPaths
        self.qss_files = qss_files or [QssPaths.MAIN, QssPaths.SIDEBAR]
        self.logic = HinnapakkujaLogic()
        self.form = HinnapakkujaForm()
        self.offerView = None
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.form)
        self.form.formSubmitted.connect(self.onFormSubmitted)
        if self.theme_dir:
            self.theme_manager.apply_theme(self, self.theme_dir, qss_files=self.qss_files)
        else:
            raise ValueError("theme_dir must be provided to HinnapakkujaUI for theme application.")

    def onFormSubmitted(self, user_input):
        price_data = self.logic.get_mock_price_data()
        result = self.logic.calculate_nodes_and_materials(user_input, price_data)
        if self.offerView:
            self.layout.removeWidget(self.offerView)
            self.offerView.deleteLater()
        self.offerView = HinnapakkujaOfferView(result)
        self.layout.addWidget(self.offerView)

    def activate(self):
        pass
    def deactivate(self):
        pass
    def reset(self):
        if self.offerView:
            self.layout.removeWidget(self.offerView)
            self.offerView.deleteLater()
            self.offerView = None
        self.form.reset()
    def run(self):
        pass
    def get_widget(self):
        return self
