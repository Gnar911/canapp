import sys
from typing import Optional, TypeVar, Generic
from PySide6 import QtWidgets
from PySide6.QtWidgets import QWidget, QListView
# from CenterContextPane import CenterContextManagerViewModel
# from can_sdk.canlog_viewmodel import BasicFileLogContext, FilterMode, LogContextManager
from can_sdk.dbc_manager import CANDBManager
# from can_sdk.data_object import CANLogLine
from canapp.widgets.basic_component.CollapsibleSection import CollapsibleSection
from canapp.widgets.FilterTimeScopeSlider import FilterTimeScopeSlider
# from ui_sdk.components.pyqt.MessageFilterCheckList import MessageFilterCheckList
# from ui_sdk.components.pyqt.ChannelFilterCheckList import ChannelFilterCheckList
# from ui_sdk.components.pyqt.SignalFilterCheckList import SignalFilterCheckList
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex, QTimer
from typing import Dict, List, Optional, Tuple
# from can_sdk.logger_setup import LOG, setup_logger
from canapp.vm.log_viewmodel import LogViewModel, MessageItem, SignalItem, ChannelItem
from can_sdk.dbc_manager import CANDBManager
from typing import List, Dict, Optional, Tuple
from PySide6.QtCore import Qt, QModelIndex, QAbstractListModel
from PySide6.QtCore import Qt, QSortFilterProxyModel
from PySide6.QtWidgets import QLineEdit, QListView
from ultility import *

# class CheckListSearch(QWidget):
#     def __init__(
#         self
#     ):
#         super().__init__()
#         layout = QVBoxLayout(self)
#         search_row = QHBoxLayout()
#         self.search = QLineEdit()
#         self.search.setPlaceholderText("Search…")
#         search_row.addWidget(self.search)
#         self.search.textChanged.connect(self.filter_items)
#         self.all_btn.clicked.connect(self.check_all)
#         self.clear_btn.clicked.connect(self.uncheck_all)
#         self.list.itemChanged.connect(self._on_item_changed)

#     def _apply_item_visual_state(self, item: QListWidgetItem):
#         palette = self.palette()
#         checked_color = palette.color(QPalette.Active, QPalette.Text)
#         unchecked_color = palette.color(QPalette.Disabled, QPalette.Text)
#         if item.checkState() == Qt.Checked:
#             item.setForeground(checked_color)
#         else:
#             item.setForeground(unchecked_color)

#     def filter_items(self, text: str):
#         text = text.lower()
#         for i in range(self.list.count()):
#             item = self.list.item(i)
#             item.setHidden(text not in item.text().lower())

#     def _on_item_changed(self, item: QListWidgetItem):
#         if self._reordering:
#             return

#         self._apply_item_visual_state(item)

#         row = self.list.row(item)
#         if row < 0:
#             return

#         target_row = None
#         if item.checkState() == Qt.Checked:
#             if row > 0:
#                 target_row = 0
#         else:
#             last_row = self.list.count() - 1
#             if row < last_row:
#                 target_row = last_row

#         if target_row is None:
#             return

#         self._reordering = True
#         try:
#             moved = self.list.takeItem(row)
#             if target_row >= self.list.count():
#                 self.list.addItem(moved)
#             else:
#                 self.list.insertItem(target_row, moved)
#             self.filter_items(self.search.text())
#         finally:
#             self._reordering = False


T = TypeVar("T")
class FilterItemsListModel(QAbstractListModel, Generic[T]):

    ROLE_ITEM = Qt.UserRole + 1

    def __init__(self, vm: LogViewModel, parent=None):
        super().__init__(parent)

        self.vm = vm
        self._items: list[T] = []

        self.vm.commonStateChanged.connect(self.reevaluate)

        self.reevaluate()

    def reevaluate(self):
        self.beginResetModel()

        if isinstance(self._items, 
                      list[MessageItem]): 
            self._items = self.vm.filterMessageList

        if isinstance(self._items,
                       list[SignalItem]): 
            self._items = self.vm.filterSignalList

        if isinstance(self._items, 
                      list[ChannelItem]): 
            self._items = self.vm.filterChannelList

        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        return len(self._items)

    # Model -> View
    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        item = self._items[index.row()]

        if role == Qt.DisplayRole:
            return item.show

        if role == Qt.CheckStateRole:
            return Qt.Checked if item.checked else Qt.Unchecked

        if role == self.ROLE_ITEM:
            return item

        return None

    def flags(self, index):
        if not index.isValid():
            return Qt.NoItemFlags

        return (
            Qt.ItemIsEnabled
            | Qt.ItemIsSelectable
            | Qt.ItemIsUserCheckable
        )

    # View -> Model
    def setData(self, index, value, role):
        if (
            not index.isValid()
            or role != Qt.CheckStateRole
        ):
            return False

        checked = (value == Qt.Checked)
        item = self._items[index.row()]
        self.vm.messageFilter = item.data

        return True


""" 20260726 NOTE:
    Check box list is rendered by the higher layer called QStyledItemDelegate

    Model
    │
    │  DisplayRole -> "Engine"
    │  CheckStateRole -> Checked
    ▼
    QListView, QTreeView
    │
    ▼
    QStyledItemDelegate (QAbstractItemDelegate) implemented checkBoxed item style
    │
    ▼
    QStyle
    │
    ▼
    Paint checkbox + text
"""
class FiltersPanel(QtWidgets.QWidget):
    def __init__(
        self,
        parent: QWidget,
        vm: LogViewModel
    ):
        super().__init__(parent)
        self.vm = vm

        self._build_ui()
        self.rb_rx_only.toggled.connect(
            lambda checked: checked and setattr(self.vm, "messageFilter", "Rx")
        )

        self.rb_tx_only.toggled.connect(
            lambda checked: checked and setattr(self.vm, "messageFilter", "Tx")
        )

        self.rb_none.toggled.connect(
            lambda checked: checked and setattr(self.vm, "messageFilter", None)
        )

    def _build_ui(self):
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        # --- Message Filter section ---
        self.section_message = CollapsibleSection("Filter Message")
        msg_content = QtWidgets.QVBoxLayout()

        self.edit_message_search = QLineEdit(self)
        self.edit_message_search.setPlaceholderText("Search...")

        self.message_model = FilterItemsListModel(self.vm)

        self.message_proxy = QSortFilterProxyModel(self)
        self.message_proxy.setSourceModel(self.message_model)
        self.message_proxy.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.message_proxy.setFilterRole(Qt.DisplayRole)

        self.message_filter = QListView(self)
        self.message_filter.setModel(self.message_proxy)

        self.edit_message_search.textChanged.connect(
            self.message_proxy.setFilterFixedString
        )

        msg_content.addWidget(self.edit_message_search)
        msg_content.addWidget(self.message_filter)

        self.section_message.setContentLayout(msg_content)


        # --- Channel Filter section ---
        self.section_channel = CollapsibleSection("Filter Channel")
        channel_content = QtWidgets.QVBoxLayout()

        self.edit_channel_search = QLineEdit(self)
        self.edit_channel_search.setPlaceholderText("Search...")

        self.channel_model = FilterItemsListModel(self.vm)

        self.channel_proxy = QSortFilterProxyModel(self)
        self.channel_proxy.setSourceModel(self.channel_model)
        self.channel_proxy.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.channel_proxy.setFilterRole(Qt.DisplayRole)

        self.channel_filter = QListView(self)
        self.channel_filter.setModel(self.channel_proxy)

        self.edit_channel_search.textChanged.connect(
            self.channel_proxy.setFilterFixedString
        )

        channel_content.addWidget(self.edit_channel_search)
        channel_content.addWidget(self.channel_filter)

        self.section_channel.setContentLayout(channel_content)

        # --- Signal Filter section ---
        """ NOTE: TODO : ON IMPLEMTATION"""
        # self.section_signal = CollapsibleSection("Filter Signal")
        # sig_content = QtWidgets.QVBoxLayout()
        # self.signal_filter_panel = SignalFilterCheckList(
        #     parent=self,
        #     ctx_model=self.log_ctx_mgr,
        # )
        # sig_content.addWidget(self.signal_filter_panel)
        # self.section_signal.setContentLayout(sig_content)

        self.section_dir = CollapsibleSection("Filter Rx/Tx")
        dir_content = QtWidgets.QVBoxLayout()
        group_dir = QtWidgets.QGroupBox("")
        group_dir_layout = QtWidgets.QHBoxLayout(group_dir)
        group_dir_layout.setContentsMargins(6, 6, 6, 6)
        group_dir_layout.setSpacing(10)

        self.rb_rx_only = QtWidgets.QRadioButton("Rx Only")
        self.rb_tx_only = QtWidgets.QRadioButton("Tx Only")
        self.rb_none = QtWidgets.QRadioButton("None")
        self.rb_none.setChecked(True)

        group_dir_layout.addWidget(self.rb_rx_only)
        group_dir_layout.addWidget(self.rb_tx_only)
        group_dir_layout.addWidget(self.rb_none)
        group_dir_layout.addStretch(1)
        dir_content.addWidget(group_dir)
        self.section_dir.setContentLayout(dir_content)

        """ NOTE: TODO : ON IMPLEMTATION"""
        # self.section_time = CollapsibleSection("Filter Time Range")
        # time_content = QtWidgets.QVBoxLayout()
        # group_time = QtWidgets.QGroupBox("")
        # group_time_layout = QtWidgets.QVBoxLayout(group_time)
        # group_time_layout.setContentsMargins(6, 6, 6, 6)
        # group_time_layout.setSpacing(6)

        # self.range_slider = FilterTimeScopeSlider(
        #     parent=self,
        #     ctx_model=self.log_ctx_mgr,
        # )

        # group_time_layout.addWidget(self.range_slider)
        # time_content.addWidget(group_time)
        # self.section_time.setContentLayout(time_content)

        root.addWidget(self.section_message)
        #root.addWidget(self.section_signal)
        root.addWidget(self.section_channel)
        root.addWidget(self.section_dir)
        #root.addWidget(self.section_time)
        root.addStretch(1)

    # def _on_dir_filter_changed(self):
    #     if self.rb_rx_only.isChecked():
    #         self.target_logfile.set_dir_filter(FilterMode.RX_ONLY)
    #     elif self.rb_tx_only.isChecked():
    #         self.target_logfile.set_dir_filter(FilterMode.TX_ONLY)
    #     else:
    #         self.target_logfile.unset_dir_filter()

    # def on_event_target_logfile_changed(self, file: BasicFileLogContext):
    #     if file is None:
    #         return
    #     if self.target_logfile is not None:
    #         self.target_logfile.event_on_filter_changed.remove_all_subscribes()
    #     file.event_on_filter_changed.subscribe(self.on_event_filter_changed)
    #     self.target_logfile = file
    #     self.range_slider.set_context(file)
    #     self.rb_none.setChecked(True)

    # def on_event_filter_changed(self, data: list[CANLogLine]):
    #     self._filtered_lines = list(data)
    #     if self.target_logfile is not None:
    #         self.range_slider.set_context(self.target_logfile)
