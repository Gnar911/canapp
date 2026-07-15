from PySide6.QtCore import (
    QModelIndex, Qt
)
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QMenu
)
from can_sdk.data_object import SignalFilter
from typing import Optional
from can_sdk.dbc_manager import CANDBManager
from lw.logger_setup import LOG
from can_sdk.canlog_viewmodel import LogContextViewModel, FilterState
from ui_sdk.components.pyqt.basic_component.CheckboxTable import CheckboxTable, CheckboxTableModel

class FilterSignalViewModel(CheckboxTableModel):
    COL_CHECK = 0
    COL_NAME  = 1
    COL_VALUE = 2

    def __init__(self, parent=None, model: CANDBManager = None):
        super().__init__(
            parent=parent,
            heading_num=3,
            headings=["#", "Signal Name", "Value"],
        )
        self.my_model = model

    @property
    def log_sig_current_filter(self):
        return self._items
    
    def data(self, index, role=Qt.DisplayRole) -> Optional[SignalFilter]:
        if not index.isValid():
            return None

        item = self._items[index.row()]

        if role == Qt.BackgroundRole and item.color:
            return QColor(item.color)

        return super().data(index, role)

    def _get_cell_value(self, item: SignalFilter, col: int):
        if col == self.COL_NAME:
            return item.sig_name
        if col == self.COL_VALUE:
            return item.value
        return ""

    # ---- API ----
    def add_item(self, item: SignalFilter):
        if item in self._items:
            return
        row = len(self._items)
        self.beginInsertRows(QModelIndex(), row, row)
        self._items.append(item)
        self._checked[row] = False
        self.endInsertRows()

    def delete_all(self):
        if not self._items:
            return
        self.beginResetModel()
        self._items.clear()
        self._checked.clear()
        self.endResetModel()

class FilterSignalTable(QWidget):
    def __init__(self, parent=None, model: CANDBManager = None, ctx_model: LogContextViewModel = None):
        super().__init__(parent)
        self.my_model = model
        self.ctx_model = ctx_model
        self.model = FilterSignalViewModel(self, model)
        self.table = CheckboxTable(self, self.model)
        self.view = self.table.view
        self.selection_model = self.table.selection_model
        self.view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.view.customContextMenuRequested.connect(self._show_context_menu)
        self.selection_model.currentChanged.connect(self._on_current_changed)
        self.selection_model.selectionChanged.connect(self._on_selection_changed)

        self.table.set_heading_num(3)
        self.table.set_headings(["#", "Signal Name", "Value"])
        self.table.set_column_widths([30, 160, 120])

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.table)

    def add_item(self, item: SignalFilter):
        """
        Add a SignalFilter to the table.
        """
        self.table.add_item(item)

    def remove_all(self):
        """
        Remove all rows from the table.
        """
        self.table.remove_all()

    def remove_selected(self):
        """
        Remove all currently selected rows.
        """
        self.table.remove_selected()


    def _on_current_changed(self, current: QModelIndex, previous: QModelIndex):
        LOG.debug("_on_current_changed")

        if not current.isValid() or current == previous:
            self.my_model.cur_sig = None
            return

        # Only react to the Signal Name column (avoid duplicate calls)
        if current.column() != FilterSignalViewModel.COL_NAME:
            return

        # Get SignalFilter directly from the model
        signal_filter: SignalFilter = self.model._items[current.row()]

        # Set into your domain model
        self.my_model.cur_sig = signal_filter

    def _on_selection_changed(self, selected, deselected):
        # keep cur_sig in sync when selection changes without currentChanged
        if selected.indexes():
            idx = selected.indexes()[0]
            if idx.column() == FilterSignalViewModel.COL_NAME:
                self.my_model.cur_sig = self.model._items[idx.row()]


    def current_selected_items(self) -> list[SignalFilter]:
        """
        Return all currently selected SignalFilter items.
        """
        return self.table.current_selected_items(FilterSignalViewModel.COL_NAME)

    # ---- context menu ----
    def _show_context_menu(self, pos):
        index = self.view.indexAt(pos)
        if not index.isValid():
            return

        menu = QMenu(self)

        highlight = menu.addMenu("Highlight")
        for label, color in [
            ("Red", "#FFCCCC"),
            ("Green", "#C6EFCE"),
            ("Pink", "#FFCCFF"),
            ("Blue", "#CCCCFF"),
            ("Violet", "#E5CCFF"),
            ("Cyan", "#CCF2FF"),
            ("Brown", "#FFD9B3"),
        ]:
            highlight.addAction(
                label,
                lambda c=color: self._mark_selected(c)
            )

        menu.addSeparator()
        menu.addAction("Clear", self._clear_selected)
        menu.addAction("Clear All", self.clear_all_colors)
        menu.exec(self.view.viewport().mapToGlobal(pos))

    # ---- actions ----
    def _mark_selected(self, color):
        sel = self.view.selectionModel().selectedIndexes()
        for idx in sel:
            if idx.column() == 1:
                self.model._items[idx.row()].color = color
        self.model.layoutChanged.emit()
        if self.ctx_model.cur_ctx.filter_state != FilterState.FILTER_SIG:
            return
        items = self.current_selected_items()
        mark_lines = self.ctx_model.cur_ctx.datalog.get_signals_by_list_signal_raw_value(
            signals = items, 
            target_search_lines = self.ctx_model.cur_ctx.canlog_filter)
        self.ctx_model.set_color_for_this_ctx_lines(mark_lines, color)

    def _clear_selected(self):
        sel = self.view.selectionModel().selectedIndexes()
        for idx in sel:
            self.model._items[idx.row()].color = None
        self.model.layoutChanged.emit()
        if self.ctx_model.cur_ctx.filter_state != FilterState.FILTER_SIG:
            return
        items = self.current_selected_items()
        """ There may be not filter state but user still click on this"""
        mark_lines = self.ctx_model.cur_ctx.datalog.get_signals_by_list_signal_raw_value(
        signals = items, 
        target_search_lines = self.ctx_model.cur_ctx.canlog_filter)
        self.ctx_model.set_color_for_this_ctx_lines(mark_lines, "")  

    def clear_all_colors(self):
        for item in self.model._items:
            item.color = None
        self.model.layoutChanged.emit()
        if self.ctx_model.cur_ctx.filter_state != FilterState.FILTER_SIG:
            return
        self.ctx_model.unset_color_for_this_ctx_lines(self.ctx_model.cur_ctx.canlog_filter, "") 

if __name__ == "__main__":
    def _build_mock_signal_filter(sig_name: str, value: str, color: Optional[str] = None) -> SignalFilter:
        item = SignalFilter()
        item.sig_name = sig_name
        item.value = value
        item.color = color
        return item


    def _mock_signal_filters() -> list[SignalFilter]:
        return [
            _build_mock_signal_filter("VehicleSpeed", "72.5 km/h", "#CCF2FF"),
            _build_mock_signal_filter("EngineRPM", "2450 rpm"),
            _build_mock_signal_filter("SteeringAngle", "-3.2 deg", "#E5CCFF"),
            _build_mock_signal_filter("BrakePressure", "18.7 bar"),
            _build_mock_signal_filter("BatteryVoltage", "12.4 V", "#C6EFCE"),
        ]

    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    w = FilterSignalTable()
    for signal_filter in _mock_signal_filters():
        w.add_item(signal_filter)
    w.resize(420, 260)
    w.show()

    sys.exit(app.exec())

