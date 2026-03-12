import webbrowser
import requests
from datetime import datetime, timedelta
from types import MethodType

from PyQt5.QtCore import Qt, QPropertyAnimation
from PyQt5.QtWidgets import (
    QDialog, QFrame)

from ...config.settings import Filepaths, FilesByNames, OpenLink
from ...config.SetupModules.AsBuitSettings import AsBuiltDrawings, DraggableFrame
from ...config.settings_new import PluginSettings

from ...queries.python.tasks.taskQueries import CreateTask
from ...queries.python.update_relations.updateElementProperties import ConnectElementWithPropertysties
from ...queries.python.users.user import UserSettings

from ...KeelelisedMuutujad.Maa_amet_fields import Katastriyksus
from ...KeelelisedMuutujad.modules import Module
from ...KeelelisedMuutujad.messages import Headings, HoiatusTexts

from ...utils.ComboboxHelper import ComboBoxHelper
from ...utils.TableUtilys.FlagIconHelper import FlagIconHelper
from ...app.Animations.AnimatedGradientBorderFrame import AnimatedGradientBorderFrame
from ..AsBuilt.ASBuilt import TaskMain
from ...widgets.decisionUIs.DecisionMaker import DecisionDialogHelper


combo_handler = ComboBoxHelper()


class worksTools:

    def __init__(self, parent) -> None:
        self.dialog = parent
    @staticmethod
    def load_worksTools(feature, properties_feature):
        widget_name = Filepaths._get_widget_name(FilesByNames().worksTools_UI)
        widget = Filepaths.load_ui_file(widget_name)

        widget.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool)
        widget.setAttribute(Qt.WA_TranslucentBackground)
        widget.adjustSize()

        worksTools._setup_draggable_frame(widget)
        worksTools._apply_gradient_frame(widget)
        worksTools._connect_buttons(widget)

        worksTools._initialize_data(widget, feature, properties_feature)

        animation = QPropertyAnimation(widget, b"windowOpacity")
        animation.setDuration(300)
        animation.setStartValue(0.0)
        animation.setEndValue(1.0)
        animation.start()

        # Connect the save button to a wrapper function that validates THEN accepts
        widget.pbSave.clicked.connect(lambda: worksTools._validate_and_submit(widget, feature, properties_feature))


        result = widget.exec_()
        widget.setAttribute(Qt.WA_DeleteOnClose)



        if result == QDialog.Accepted:
            #worksTools._apply_widget_values(widget, feature, properties_feature)
            return True
        return False

    @staticmethod
    def _validate_and_submit(widget, feature, properties_feature):
        result = worksTools._apply_widget_values(widget, feature, properties_feature)
        if result:
            widget.accept()  # ✅ Only close the dialog if values are valid

    @staticmethod
    def _setup_draggable_frame(widget):
        drag_frame = widget.findChild(QFrame, "dragFrame")
        if drag_frame:
            drag_frame.mousePressEvent = MethodType(DraggableFrame.mousePressEvent, drag_frame)
            drag_frame.mouseMoveEvent = MethodType(DraggableFrame.mouseMoveEvent, drag_frame)
            drag_frame._drag_pos = None
            drag_frame.setCursor(Qt.OpenHandCursor)
    @staticmethod
    def _apply_gradient_frame(widget):
        AsBuiltDrawings.replace_frame(widget, "FrameMain", style=AnimatedGradientBorderFrame.GENTLEMAN)
    @staticmethod
    def _connect_buttons(widget):

        widget.pbCancel.clicked.connect(lambda: widget.reject())
    @staticmethod
    def _initialize_data(widget, feature, properties_feature):
        # Title setup
        task_label = widget.lblHeadingValue
        full_address = ""
        if properties_feature:
            address = properties_feature[Katastriyksus.l_aadress]
            asum = properties_feature[Katastriyksus.ay_nimi]
            full_address = f"{address}, {asum}"
        task_label.setText(full_address)

        # Priority combobox
        worksTools._populate_priority_combo(widget.cmbPriority)

        # Date/time labels
        now = datetime.now()
        widget.lblStartDate.setText(now.strftime("%Y-%m-%d"))
        widget.lblStartTime.setText(now.strftime("%H:%M"))

        # User fields
        worksTools._populate_users(widget)

        # Work types
        module = Module.WORKS
        group_values = PluginSettings.load_setting(
            module=module,
            context=PluginSettings.CONTEXT_PREFERRED,
            subcontext=PluginSettings.OPTION_TYPE,
            key_type=PluginSettings.SUB_CONTEXT_TYPE_GROUP,
            text_fomated=True
        )
        combo_handler.refresh_combo_box_with_group_values(widget.workTypes, module, group_values)

        worksTools._setup_dynamic_title(widget.workTypes, widget.lblHeadingValue, prefix_text=full_address, lineEdit=widget.worksTitleadition)
    @staticmethod
    def _populate_priority_combo(combo):
        priority_map = {
            "URGENT": "Kiire",
            "HIGH": "Kõrge",
            "MEDIUM": "Keskmine",
            "LOW": "Madal"
        }

        # ➕ Add an empty initial item
        combo.addItem("")  # No icon, no display text
        combo.setItemData(0, None, Qt.UserRole)  # No associated enum value

        for enum_value, display_name in priority_map.items():
            icon = FlagIconHelper.generate_icon(priority=enum_value, size=18)
            combo.addItem(icon, display_name)
            combo.setItemData(combo.count() - 1, enum_value, Qt.UserRole)
    @staticmethod
    def _populate_users(widget):
        users = UserSettings.load_users()

        # ➕ Add empty item to cmbResponsible
        widget.cmbResponsible.clear()
        widget.cmbResponsible.addItem("")  # Empty visible text
        widget.cmbResponsible.setItemData(0, None, Qt.UserRole)

        for label, user_id in users:
            widget.cmbResponsible.addItem(label)
            widget.cmbResponsible.setItemData(widget.cmbResponsible.count() - 1, user_id, Qt.UserRole)

        widget.mcbxUsers.clear()

        for label, user_id in users:
            widget.mcbxUsers.addItem(label)
            index = widget.mcbxUsers.findText(label)
            widget.mcbxUsers.setItemData(index, user_id, Qt.UserRole)
            widget.mcbxUsers.setItemData(index, Qt.Unchecked, Qt.CheckStateRole)

    @staticmethod
    def _setup_dynamic_title(comboBox, label, prefix_text="", lineEdit=None):
        def update_label():
            parts = []
            if prefix_text:
                parts.append(prefix_text)
            if comboBox.currentText():
                parts.append(comboBox.currentText())
            if lineEdit and lineEdit.text().strip():
                parts.append(lineEdit.text().strip())
            label.setText(" - ".join(parts))

        comboBox.currentIndexChanged.connect(lambda _: update_label())
        if lineEdit:
            lineEdit.textChanged.connect(lambda _: update_label())
        update_label()
    @staticmethod
    def _apply_widget_values(widget, feature, properties_feature):
        #print("Saving data")
        # ✅ Validate required selections
        type_id = widget.workTypes.currentData()
        responsible_id = widget.cmbResponsible.itemData(widget.cmbResponsible.currentIndex(), Qt.UserRole)
        priority = widget.cmbPriority.itemData(widget.cmbPriority.currentIndex(), Qt.UserRole)

        # Check required fields
        if not (type_id and responsible_id):
            #print("Some fields are not filled")
            buttons = {"keep": "Edasi"}
            DecisionDialogHelper.ask_user(
                title=Headings.inFO_SIMPLE,
                message="Palun täida kohustuslikud väljad",
                options=buttons,
                parent=widget,
                type=AnimatedGradientBorderFrame.WARNING
            )
            return False  # ✋ prevent closing

        # 🎯 Proceed with rest of logic
        now = datetime.now()
        start_date = now.strftime("%Y-%m-%d")
        description = widget.worksDesc.toPlainText().strip()
        responsible = widget.cmbResponsible.currentText().strip()
        users_variable = CreateTask.prepare_associate_variable(widget.mcbxUsers, responsible_id)
        work_type = widget.workTypes.currentText().strip()
        task_title = widget.lblHeadingValue.text().strip()

        variables = {
            "title": task_title,
            "description": description,
            "priority": priority,
            "startAt": start_date,
            "dueAt": (now + timedelta(days=7)).strftime("%Y-%m-%d"),
            "typeId": type_id,
            "members": {"associate": users_variable}
        }

        task_id = CreateTask.Create_Task(variables)

        details = TaskMain.load_task_data(task_id)
        status_payload = ((details or {}).get("data") or {}).get("task", {}).get("status", {}) or {}
        status_type = str(status_payload.get("type") or "").upper()

        try:
            status_id = int(status_payload.get("id")) if status_payload.get("id") is not None else None
        except (TypeError, ValueError):
            status_id = None

        try:
            task_id_value = int(task_id)
        except (TypeError, ValueError):
            task_id_value = task_id

        end_date = now if status_type == "CLOSED" else None

        # Update feature attributes
        feature.setAttribute("ext_job_id", task_id_value)
        feature.setAttribute("ext_system", "Kavitro")
        feature.setAttribute("ext_job_name", task_title)
        feature.setAttribute("ext_job_type", work_type)
        feature.setAttribute("ext_url", "")
        feature.setAttribute("ext_job_state", status_id)
        feature.setAttribute("begin_date", now)
        feature.setAttribute("end_date", end_date)
        feature.setAttribute("added_by", responsible)
        feature.setAttribute("added_date", now)
        feature.setAttribute("updated_by", responsible)
        feature.setAttribute("update_date", now)

        # Link properties if provided
        if properties_feature:
            tunnus = str(properties_feature[Katastriyksus.tunnus])
            ConnectElementWithPropertysties.connect_single_properties(task_id, [tunnus])

        # Open task in browser
        link = f"{OpenLink.weblink_by_module(f'/{OpenLink.get_module_link(Module.TASK)}s/')}{task_id}"
        response = requests.get(link, verify=False)
        webbrowser.open(response.url)

        return True  # ✅ success

