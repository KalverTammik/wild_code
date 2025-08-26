# -*- coding: utf-8 -*-
"""
TodoManagerModule – lihtne ülesannete/märkuste haldur sinu QGIS plugina jaoks.

Eesmärk: võimalikult vähe üle-mõtlemist. Üks fail, üks moodul.
- Instantsiatribuudid (name/display_name/icon) nagu sinu reeglites.
- Salvestus: QgsSettings alla JSON-ina (võtme all: wild_code/todo/tasks).
- UI: kerge QWidget + QTableView. Lisamine/muutmine/eemaldamine/oluliseks märkimine.
- Teema: ThemeManager.apply_module_style(widget, ...), kui saadaval.
- Esmakäivitusel initsialiseerib 6 ülesannet vastavalt sinu palvele.

Integreerimine:
    from .TodoManagerModule import TodoManagerModule
    module_manager.registerModule(TodoManagerModule())

Märkused:
- Plaaniga ja kirjeldusega punktid (#2, #3) saavad vaikekirjelduse "[Lisa kirjeldus]" – saad seda hiljem muuta.
- Punkt #4 märgitakse oluliseks.
"""
from __future__ import annotations

import json
import typing as T
from dataclasses import dataclass, asdict
from uuid import uuid4
from datetime import datetime

from qgis.PyQt.QtCore import Qt, QAbstractTableModel, QModelIndex, QVariant, pyqtSignal
from qgis.PyQt.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableView, QHeaderView,
    QMessageBox, QInputDialog, QLineEdit
)
from qgis.core import QgsSettings

# --- Valikulised importid – kui sinu projektis olemas ---
try:
    from .BaseModule import BaseModule  # tüüpiline asukoht, kohanda vajadusel
except Exception:  # pragma: no cover
    class BaseModule(object):  # minimaalne stub testimiseks
        def __init__(self):
            pass

try:
    from .ThemeManager import ThemeManager  # kui olemas, rakendame QSS
except Exception:  # pragma: no cover
    class ThemeManager:  # stub
        @staticmethod
        def apply_module_style(widget: QWidget, qss_paths: T.List[str] | None = None) -> None:
            pass

try:
    from .LanguageManager import LanguageManager
except Exception:  # pragma: no cover
    class LanguageManager:
        @staticmethod
        def sidebar_button(key: str) -> str:
            return "Ülesanded"

# --- Püsivad väärtused ---
SETTINGS_KEY = "wild_code/todo/tasks"
DATE_FMT = "%Y-%m-%d %H:%M:%S"

class TaskStatus:
    IGNORE = "IGNORE"              # "Esialgu eirame"
    PLAN = "PLAN"                  # "Lisa tööplaani"
    PLAN_WITH_DESC = "PLAN_WITH_DESC"  # "Lisa tööplaani kirjeldusega"

STATUS_LABELS_ET = {
    TaskStatus.IGNORE: "Eirata (praegu)",
    TaskStatus.PLAN: "Tööplaani",
    TaskStatus.PLAN_WITH_DESC: "Tööplaani (kirjeldusega)",
}

@dataclass
class Task:
    id: str
    title: str
    status: str
    description: str = ""
    important: bool = False
    created_at: str = ""
    updated_at: str = ""

    @staticmethod
    def new(title: str, status: str, description: str = "", important: bool = False) -> "Task":
        now = datetime.now().strftime(DATE_FMT)
        return Task(id=str(uuid4()), title=title, status=status, description=description,
                    important=important, created_at=now, updated_at=now)

# --- Salvesti ---
class TaskStore:
    def __init__(self, settings: QgsSettings):
        self._settings = settings

    def load(self) -> T.List[Task]:
        raw = self._settings.value(SETTINGS_KEY, "", type=str)
        if not raw:
            return []
        try:
            data = json.loads(raw)
            return [Task(**t) for t in data]
        except Exception:
            return []

    def save(self, tasks: T.List[Task]) -> None:
        payload = json.dumps([asdict(t) for t in tasks], ensure_ascii=False)
        self._settings.setValue(SETTINGS_KEY, payload)

# --- Tabelimudel ---
class TaskTableModel(QAbstractTableModel):
    COLUMNS = ["#", "Pealkiri", "Staatus", "Oluline", "Kirjeldus"]

    def __init__(self, tasks: T.List[Task], parent: QWidget | None = None):
        super().__init__(parent)
        self._tasks = tasks

    # Põhi
    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._tasks)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self.COLUMNS)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> T.Any:
        if not index.isValid():
            return QVariant()
        task = self._tasks[index.row()]
        col = index.column()
        if role in (Qt.DisplayRole, Qt.EditRole):
            if col == 0:
                return index.row() + 1
            if col == 1:
                return task.title
            if col == 2:
                return STATUS_LABELS_ET.get(task.status, task.status)
            if col == 3:
                return "✓" if task.important else ""
            if col == 4:
                return task.description
        if role == Qt.TextAlignmentRole:
            return Qt.AlignLeft | Qt.AlignVCenter
        return QVariant()

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole) -> T.Any:
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.COLUMNS[section]
        return super().headerData(section, orientation, role)

    # Abimeetodid
    def task_at(self, row: int) -> Task | None:
        if 0 <= row < len(self._tasks):
            return self._tasks[row]
        return None

    def add_task(self, task: Task):
        self.beginInsertRows(QModelIndex(), len(self._tasks), len(self._tasks))
        self._tasks.append(task)
        self.endInsertRows()

    def remove_row(self, row: int):
        if 0 <= row < len(self._tasks):
            self.beginRemoveRows(QModelIndex(), row, row)
            self._tasks.pop(row)
            self.endRemoveRows()

    def update_row(self, row: int, task: Task):
        if 0 <= row < len(self._tasks):
            self._tasks[row] = task
            tl = self.index(row, 0)
            br = self.index(row, self.columnCount()-1)
            self.dataChanged.emit(tl, br, [Qt.DisplayRole])

    def tasks(self) -> T.List[Task]:
        return list(self._tasks)

# --- Põhi-Widget ---
class TodoManagerWidget(QWidget):
    requestSave = pyqtSignal()

    def __init__(self, store: TaskStore, parent: QWidget | None = None):
        super().__init__(parent)
        self._store = store
        self._model = TaskTableModel(self._store.load())
        self._build_ui()
        self._ensure_seed_data()

        # Rakenda teema, kui ThemeManager on saadaval
        try:
            ThemeManager.apply_module_style(self, [])
        except Exception:
            pass

    # Esitekordne täitmine sinu kuue punktiga
    def _ensure_seed_data(self):
        if self._model.rowCount() > 0:
            return
        seed = [
            Task.new("Esialgu eirame", TaskStatus.IGNORE),
            Task.new("Lisa tööplaani kirjeldusega", TaskStatus.PLAN_WITH_DESC, description="[Lisa kirjeldus]"),
            Task.new("Lisa tööplaani kirjeldusega", TaskStatus.PLAN_WITH_DESC, description="[Lisa kirjeldus]"),
            Task.new("Lisa tööplaani. Oluline teema.", TaskStatus.PLAN, important=True),
            Task.new("Lisa tööplaani", TaskStatus.PLAN),
            Task.new("Lisa tööplaani", TaskStatus.PLAN),
        ]
        for t in seed:
            self._model.add_task(t)
        self._save()

    def _build_ui(self):
        lay = QVBoxLayout(self)

        # Toolbar
        tlay = QHBoxLayout()
        self.btn_add = QPushButton("Lisa")
        self.btn_edit = QPushButton("Muuda")
        self.btn_del = QPushButton("Kustuta")
        self.btn_imp = QPushButton("Märgi oluliseks")
        self.btn_plan = QPushButton("Staatus: tööplaani")
        self.btn_desc = QPushButton("Staatus: tööplaani + kirjeldus")
        self.btn_ignore = QPushButton("Staatus: eira")

        for b in (self.btn_add, self.btn_edit, self.btn_del, self.btn_imp, self.btn_plan, self.btn_desc, self.btn_ignore):
            tlay.addWidget(b)
        tlay.addStretch(1)

        # Tabel
        self.view = QTableView()
        self.view.setModel(self._model)
        self.view.setSelectionBehavior(QTableView.SelectRows)
        self.view.setSelectionMode(QTableView.SingleSelection)
        self.view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.view.verticalHeader().setVisible(False)

        lay.addLayout(tlay)
        lay.addWidget(self.view)

        # Signaalid
        self.btn_add.clicked.connect(self._on_add)
        self.btn_edit.clicked.connect(self._on_edit)
        self.btn_del.clicked.connect(self._on_del)
        self.btn_imp.clicked.connect(self._on_toggle_important)
        self.btn_plan.clicked.connect(lambda: self._set_status(TaskStatus.PLAN))
        self.btn_desc.clicked.connect(lambda: self._set_status(TaskStatus.PLAN_WITH_DESC))
        self.btn_ignore.clicked.connect(lambda: self._set_status(TaskStatus.IGNORE))

    def _current_row(self) -> int:
        sel = self.view.selectionModel()
        if not sel or not sel.hasSelection():
            return -1
        return sel.selectedRows()[0].row()

    def _on_add(self):
        title, ok = QInputDialog.getText(self, "Uus ülesanne", "Pealkiri:", QLineEdit.Normal)
        if not ok or not title.strip():
            return
        status = TaskStatus.PLAN
        if QMessageBox.question(self, "Kirjeldus?", "Kas lisame ka kirjelduse?", QMessageBox.Yes|QMessageBox.No) == QMessageBox.Yes:
            status = TaskStatus.PLAN_WITH_DESC
        desc = ""
        if status == TaskStatus.PLAN_WITH_DESC:
            desc, ok2 = QInputDialog.getMultiLineText(self, "Kirjeldus", "Kirjeldus:")
            if not ok2:
                desc = "[Lisa kirjeldus]"
        t = Task.new(title.strip(), status, description=desc)
        self._model.add_task(t)
        self._save()

    def _on_edit(self):
        row = self._current_row()
        task = self._model.task_at(row)
        if task is None:
            return
        title, ok = QInputDialog.getText(self, "Muuda pealkirja", "Pealkiri:", QLineEdit.Normal, task.title)
        if not ok or not title.strip():
            return
        desc = task.description
        if task.status == TaskStatus.PLAN_WITH_DESC:
            desc, ok2 = QInputDialog.getMultiLineText(self, "Muuda kirjeldust", "Kirjeldus:", desc)
            if not ok2:
                desc = task.description
        task.title = title.strip()
        task.description = desc
        task.updated_at = datetime.now().strftime(DATE_FMT)
        self._model.update_row(row, task)
        self._save()

    def _on_del(self):
        row = self._current_row()
        task = self._model.task_at(row)
        if task is None:
            return
        if QMessageBox.question(self, "Kustuta", f"Kustutan ülesande: {task.title}?", QMessageBox.Yes|QMessageBox.No) == QMessageBox.Yes:
            self._model.remove_row(row)
            self._save()

    def _on_toggle_important(self):
        row = self._current_row()
        task = self._model.task_at(row)
        if task is None:
            return
        task.important = not task.important
        task.updated_at = datetime.now().strftime(DATE_FMT)
        self._model.update_row(row, task)
        self._save()

    def _set_status(self, status: str):
        row = self._current_row()
        task = self._model.task_at(row)
        if task is None:
            return
        task.status = status
        if status == TaskStatus.PLAN_WITH_DESC and not task.description:
            task.description = "[Lisa kirjeldus]"
        task.updated_at = datetime.now().strftime(DATE_FMT)
        self._model.update_row(row, task)
        self._save()

    def _save(self):
        self._store.save(self._model.tasks())
        self.requestSave.emit()

# --- Moodul ---
class TodoManagerModule(BaseModule):
    def __init__(self):
        super().__init__()
        self.name = "TodoManager"
        try:
            self.display_name = LanguageManager.sidebar_button(self.name)
        except Exception:
            self.display_name = "Ülesanded"
        self.icon = None  # lisa soovi korral ModuleIcons-ist
        self._widget: TodoManagerWidget | None = None

    # Module contract
    def get_widget(self) -> QWidget:
        if self._widget is None:
            store = TaskStore(QgsSettings())
            self._widget = TodoManagerWidget(store)
        return self._widget

    def activate(self) -> None:
        # Vajadusel värskenda vaadet
        w = self.get_widget()
        w.repaint()

    def deactivate(self) -> None:
        pass

    def reset(self) -> None:
        # Ei kustuta andmeid, ainult UI reset (vajadusel)
        pass
