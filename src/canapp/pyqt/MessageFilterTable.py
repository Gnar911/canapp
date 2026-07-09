from PySide6.QtCore import Qt
from PySide6.QtGui import QStandardItem
from typing import Optional
from ui_sdk.components.pyqt.basic_component.ComboboxSearch import ComboBoxSearch
from can_sdk.dbc_manager import CANDBManager
from lw.logger_setup import LOG
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex, QTimer
from PySide6.QtWidgets import (
    QGroupBox, QPushButton, QTreeView,
    QVBoxLayout, QHBoxLayout, QMessageBox, QSizePolicy
)

class MessageFilterViewModel(QAbstractTableModel):
    ROLE_CAN_ID = Qt.UserRole + 1
    COL_CHECK = 0
    COL_NAME = 1

    def __init__(self, model2: CANDBManager = None, parent=None):
        super().__init__(parent)

        self.model2 = model2
        self.log_msg_current_filter: list[int] = []
        # self.model2.event_on_db_changed.subscribe(self._on_db_changed)

    # ---------- required ----------
    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self.log_msg_current_filter)

    def columnCount(self, parent=QModelIndex()) -> int:
        return 2

    def headerData(self, section, orientation, role):
        if role != Qt.DisplayRole or orientation != Qt.Horizontal:
            return None
        return ["#", "Message Name"][section]

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        can_id = self.log_msg_current_filter[index.row()]

        if role == Qt.CheckStateRole and index.column() == self.COL_CHECK:
            return Qt.Checked if getattr(self, "_checked", {}).get(index.row(), False) else Qt.Unchecked

        if role == Qt.DisplayRole and index.column() == self.COL_NAME:
            name = self.model2.get_message_name(can_id) or "Unknown"
            return f"[{can_id:03X}] {name}"

        if role == self.ROLE_CAN_ID:
            return can_id

        return None
    
    def get_selected_can_ids(self, selection_model) -> list[int]:
        if selection_model is None:
            return []
        sel = selection_model.selectedIndexes()
        if not sel:
            return []
        return [
            index.data(MessageFilterViewModel.ROLE_CAN_ID)
            for index in sel
            if index.isValid()
        ]

    def add_filter(self, can_id: int):
        if can_id in self.log_msg_current_filter:
            return
        row = len(self.log_msg_current_filter)
        self.beginInsertRows(QModelIndex(), row, row)
        self.log_msg_current_filter.append(can_id)
        self.endInsertRows()

    def remove_filters(self, can_ids: list[int]):
        # remove from bottom to top (important)
        rows = sorted(
            (self.log_msg_current_filter.index(cid)
            for cid in can_ids
            if cid in self.log_msg_current_filter),
            reverse=True
        )

        for row in rows:
            self.beginRemoveRows(QModelIndex(), row, row)
            del self.log_msg_current_filter[row]
            self.endRemoveRows()

    def clear_filters(self):
        if not self.log_msg_current_filter:
            return
        self.beginResetModel()
        self.log_msg_current_filter.clear()
        if hasattr(self, "_checked"):
            self._checked.clear()
        self.endResetModel()

    def get_filter_count(self) -> int:
        return len(self.log_msg_current_filter)

    def get_filters(self) -> list[int]:
        return list(self.log_msg_current_filter)


    def flags(self, index):
        if not index.isValid():
            return Qt.NoItemFlags
        flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        if index.column() == self.COL_CHECK:
            flags |= Qt.ItemIsUserCheckable
        return flags

    def setData(self, index, value, role):
        if index.column() == self.COL_CHECK and role == Qt.CheckStateRole:
            if not hasattr(self, "_checked"):
                self._checked = {}
            self._checked[index.row()] = (value == Qt.Checked)
            self.dataChanged.emit(index, index)
            return True
        return False
        
        
class MessageFilterTable(QTreeView):
    def __init__(self, model2: CANDBManager = None, parent=None):
        super().__init__(parent)
        self.filter_vm = MessageFilterViewModel(model2)
        self._selection_model = self.selectionModel()
	    # self.setModel(self.filter_vm)
        # self.setSelectionMode(QTreeView.ExtendedSelection)
        self.setRootIsDecorated(False)
        self.setModel(self.filter_vm)
        self.setSelectionMode(QTreeView.ExtendedSelection)
        self.setAlternatingRowColors(True)
        self.header().setStretchLastSection(True)
        self.setColumnWidth(0, 30)
        self._max_control_width = 360
        self.setMaximumWidth(self._max_control_width)
        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Expanding)
        
    def remove_selected(self):
        data = self.get_selected_can_ids()
        return self.filter_vm.remove_filters(data)

    def clear_filters(self):
        return self.filter_vm.clear_filters()

    def add_filter(self, data):
        return self.filter_vm.add_filter(data)

    def get_selected_can_ids(self):
        return self.filter_vm.get_selected_can_ids(self._selection_model)

    def get_filter_count(self) -> int:
        return self.filter_vm.get_filter_count()

    def get_filters(self) -> list[int]:
        return self.filter_vm.get_filters()
        
if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton

    app = QApplication(sys.argv)

    win = QWidget()
    layout = QVBoxLayout(win)

    model = CANDBManager()
    model.load_database(
        "/home/gnar911/Desktop/20260122 APP WEBSITE - CAN ANALYZER 3.0 CBCM TOOL APP ARC/CAN_Analyzer_MVVM/Database/EEA10_CANFD_R00c_withADAS_Main.dbc")
    
    cb = MessageFilterTable(win, model)
    layout.addWidget(cb)

    btn = QPushButton("Get CAN ID")
    btn.clicked.connect(lambda: print("current_can_id:", cb.current_can_id()))
    layout.addWidget(btn)

    win.resize(400, 120)
    win.show()

    sys.exit(app.exec())
