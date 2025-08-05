"""
HinnapakkujaModule: Main entry point for the hinnapakkumise koostaja module.
Implements BaseModule and connects UI, logic, and data.
"""
from .ui.HinnapakkujaDialog import HinnapakkujaDialog
from .ui.HinnapakkujaForm import HinnapakkujaForm
from .ui.HinnapakkujaOfferView import HinnapakkujaOfferView
from .logic.HinnapakkujaLogic import HinnapakkujaLogic
from ...BaseModule import BaseModule
from PyQt5.QtCore import QObject

class HinnapakkujaModule(BaseModule, QObject):
    def __init__(self, parent=None):
        BaseModule.__init__(self)
        QObject.__init__(self, parent)
        self.name = "HINNAPAKKUJA_MODULE"
        self.dialog = HinnapakkujaDialog(parent)
        self.form = HinnapakkujaForm()
        self.offerView = None
        self.logic = HinnapakkujaLogic()
        self.priceData = self.logic.get_mock_price_data()
        self.lastInput = None
        self.dialog.setContentWidget(self.form)
        self.form.formSubmitted.connect(self.onFormSubmitted)

    def activate(self):
        self.dialog.show()

    def deactivate(self):
        self.dialog.hide()

    def run(self):
        self.activate()

    def reset(self):
        self.dialog.setContentWidget(self.form)

    def get_widget(self):
        return self.dialog

    def onFormSubmitted(self, data):
        self.lastInput = data
        result = self.logic.calculate_nodes_and_materials(data, self.priceData)
        html = self.renderOfferHtml(result)
        if not self.offerView:
            self.offerView = HinnapakkujaOfferView(html)
            self.offerView.editRequested.connect(self.onEditRequested)
            self.offerView.exportRequested.connect(self.onExportRequested)
            self.offerView.saveRequested.connect(self.onSaveRequested)
        else:
            self.offerView.setHtmlContent(html)
        self.dialog.setContentWidget(self.offerView)

    def onEditRequested(self):
        self.dialog.setContentWidget(self.form)

    def onExportRequested(self, fmt):
        # TODO: Implement PDF/Excel export
        pass

    def onSaveRequested(self):
        # TODO: Implement project save
        pass

    def renderOfferHtml(self, result):
        # Professionaalne HTML hinnapakkumine
        summary = result.get("summary", {})
        nodes = result.get("nodes", [])
        total = result.get("total", 0)
        supplier = result.get("supplier", "")
        html = f"""
        <div style='font-family:sans-serif;max-width:700px;margin:0 auto;'>
        <h2 style='color:#09908f;'>Hinnapakkumine: kortermaja veevarustus, kanalisatsioon, põrandaküte</h2>
        <h4>Sisendi kokkuvõte</h4>
        <ul>
            <li>Korterite arv: {summary.get('apartments')}</li>
            <li>Trepikodade arv: {summary.get('staircases')}</li>
            <li>Korruste arv: {summary.get('floors')}</li>
            <li>Vannitubade arv: {summary.get('bathrooms')}</li>
            <li>Eraldi WC: {'Jah' if summary.get('separate_wc') else 'Ei'}</li>
            <li>Köögis veepunkt: {'Jah' if summary.get('kitchen_water') else 'Ei'}</li>
            <li>Põrandaküte: {'Jah' if summary.get('underfloor_heating') else 'Ei'}</li>
            <li>Kütetsoonide arv: {summary.get('heating_zones')}</li>
            <li>Kollektori harude arv: {summary.get('collector_branches')}</li>
            <li>Soovitav tarnija: {summary.get('supplier')}</li>
            <li>Materjalitüüp: {summary.get('material')}</li>
            <li>Lisa 10% varu: {'Jah' if summary.get('reserve') else 'Ei'}</li>
        </ul>
        <h4>Tüüpsõlmede tabel</h4>
        <table border='1' cellpadding='6' cellspacing='0' style='border-collapse:collapse;width:100%;background:#222;color:#ececf1;'>
            <tr style='background:#09908f;color:#fff;'>
                <th>Sõlm</th><th>Kogus</th><th>Komponent</th><th>Kogus</th><th>Ühik</th><th>Hind/ühik (€)</th><th>Kokku (€)</th>
            </tr>
        """
        for node in nodes:
            rowspan = len(node["components"])
            first = True
            for comp in node["components"]:
                html += "<tr>"
                if first:
                    html += f"<td rowspan='{rowspan}'>{node['name']}</td><td rowspan='{rowspan}'>{node['qty']}</td>"
                    first = False
                html += f"<td>{comp['name']}</td><td>{comp['qty']}</td><td>{comp['unit']}</td><td>{comp['price_per_unit']}</td><td>{comp['total']}</td>"
                html += "</tr>"
        html += f"""
        </table>
        <h3 style='text-align:right;color:#09908f;'>Kogusumma: <span style='font-size:1.3em'>{total} €</span></h3>
        <div style='font-size:0.95em;color:#aaa;'>
        Tarnija: <b>{supplier}</b> | Hinnad on indikatiivsed, tootekoodid ja täpsed hinnad leiad: <a href='https://{supplier.lower()}.ee' target='_blank'>{supplier}.ee</a>
        </div>
        </div>
        """
        return html
