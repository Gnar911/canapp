from PySide6.QtCore import Qt
# from can_sdk.dbc_manager import CANDBManager 
# from can_sdk.connection_viewmodel import CANConnectManager, Handle, CANSendManager
# from can_sdk.logger_setup import LOG, setup_logger
from typing import Optional
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QMessageBox, QPushButton, QApplication)
from PySide6.QtCore import Slot, Qt
# from canapp.widgets.TreeSenderTable import TreeSenderTable
# from canapp.widgets.DBCCombobox import DBCComboBox
# from canapp.widgets.ChannelComboBox import ChannelComboBox
from PySide6.QtCore import (
    QAbstractItemModel,
    QItemSelectionModel,
    QModelIndex,
    Qt,
)
from canapp.widgets.ParseableEditBox import CanIdEditBox, RawBytesEditBox
from canapp.widgets.DLCSpinbox import DLCSpinBox
# from can_sdk.data_object import CANLogLine, CANLogPlay, SignalFilter, SendState
# from can_sdk.global_event import event_on_signal_select
from ultility import bytes_to_hex_raw, hex_raw_to_bytes 
# TEST module
# from can_sdk.parser import LogParser
# from can_sdk.connection_viewmodel import CANConnectManager, Handle, CANDeviceType, ChannelContext
import sys
import re
import math
from dataclasses import dataclass
from typing import Any, Optional, Callable, Dict, List, Tuple
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt
from copy import deepcopy
from typing import Any, Optional

from PySide6.QtCore import (
    QItemSelectionModel,
    QModelIndex,
    Qt,
)
from PySide6.QtGui import (
    QFont,
)
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QHeaderView,
    QLineEdit,
    QStyledItemDelegate,
    QToolTip,
    QToolButton,
    QTreeView,
    QVBoxLayout,
    QWidget,
)

from canapp.widgets.ParseableEditBox import (
    TimeEditBox,
    RawBytesEditBox,
)
from canapp.widgets.DLCSpinbox import DLCSpinBox
from canapp.widgets.DlcRawBinder import DlcRawBinder
from canapp.vm.schedule_view_model import \
    CANLogPlay, DecodedSignalLine, ScheduleViewModel, MessageItem, CANDeviceInfo

""" NOTE:
Model change	                            Qt notification
is_play, is_pause, direction, etc. changed	dataChanged -> ask data() again
rows inserted	                            beginInsertRows/endInsertRows
rows removed	                            beginRemoveRows/endRemoveRows
whole dataset replaced                  	beginResetModel/endResetModel
"""
class LogEditViewModel_QtAdapter(QAbstractItemModel):
    PLAY_ROLE = Qt.ItemDataRole.UserRole
    DEVICE_OPTIONS_ROLE = (Qt.ItemDataRole.UserRole + 1)
    DBC_OPTIONS_ROLE = Qt.ItemDataRole.UserRole + 2
    COL_STATUS = 0
    COL_DEVICE = 1
    COL_STR_DIFF = 2
    COL_DIRECTION = 3
    COL_CAN_ID_STR = 4
    COL_MSG_NAME = 5
    COL_DATA_LEN = 6
    COL_RAW_DATA_BYTES = 7

    COLUMN_COUNT = 8

    def __init__(
        self,
        vm: ScheduleViewModel,
        # entries: list[CANLogPlay],
        parent=None,
    ):
        super().__init__(parent)

        self._entries = vm._entries
        self._devices = vm._acquired_devices
        self._dbc_data = vm.canIDList

        vm.entriesChanged.connect(
            self._reevaluate
        )

        vm.dbcChanged.connect(
            lambda:
            (
                setattr(
                    self,
                    "_dbc_data",
                    vm.canIDList,
                ),
                #self._reevaluate(),
            )
        )

    def _reevaluate(self):
        self.beginResetModel()
        self.endResetModel()

    def columnCount(
        self,
        parent: QModelIndex = QModelIndex(),
    ) -> int:
        return self.COLUMN_COUNT

    def rowCount(
        self,
        parent: QModelIndex = QModelIndex(),
    ) -> int:
        if not parent.isValid():
            return len(self._entries)

        if parent.column() != 0:
            return 0

        obj = parent.internalPointer()

        if isinstance(obj, CANLogPlay):
            return len(obj.signals)

        return 0

    def hasChildren(
        self,
        parent: QModelIndex = QModelIndex(),
    ) -> bool:
        if not parent.isValid():
            return bool(self._entries)

        if parent.column() != 0:
            return False

        obj = parent.internalPointer()

        return (
            isinstance(obj, CANLogPlay)
            and bool(obj.signals)
        )

    def index(
        self,
        row: int,
        column: int,
        parent: QModelIndex = QModelIndex(),
    ) -> QModelIndex:
        if not self.hasIndex(
            row,
            column,
            parent,
        ):
            return QModelIndex()

        if not parent.isValid():
            return self.createIndex(
                row,
                column,
                self._entries[row],
            )

        parent_obj = parent.internalPointer()

        if not isinstance(
            parent_obj,
            CANLogPlay,
        ):
            return QModelIndex()

        if not 0 <= row < len(
            parent_obj.signals
        ):
            return QModelIndex()

        return self.createIndex(
            row,
            column,
            parent_obj.signals[row],
        )

    def parent(
        self,
        index: QModelIndex,
    ) -> QModelIndex:
        if not index.isValid():
            return QModelIndex()

        obj = index.internalPointer()

        if isinstance(obj, CANLogPlay):
            return QModelIndex()

        if not isinstance(
            obj,
            DecodedSignalLine,
        ):
            return QModelIndex()

        parent_obj = obj.parent

        if parent_obj is None:
            return QModelIndex()

        for row, entry in enumerate(
            self._entries
        ):
            if entry is parent_obj:
                return self.createIndex(
                    row,
                    0,
                    parent_obj,
                )

        return QModelIndex()

    def data(
        self,
        index: QModelIndex,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        if not index.isValid():
            return None

        obj = index.internalPointer()
        column = index.column()

        if role == self.PLAY_ROLE and isinstance(obj, CANLogPlay):
            return obj.data_model

        if role == self.PLAY_ROLE and isinstance(obj, DecodedSignalLine):
            #TODO: Select signal
            #return obj.data
            pass

        if (index.column() == self.COL_DEVICE and role == self.DEVICE_OPTIONS_ROLE):
            return self._devices

        if (index.column() == self.COL_CAN_ID_STR and role == self.DBC_OPTIONS_ROLE):
            return self._dbc_data

        """ NOTE: Display signal rows"""
        if (role == Qt.ItemDataRole.DisplayRole) and isinstance(obj,DecodedSignalLine,):
            if (
                column
                == self.COL_DEVICE
            ):
                #TODO: Signal decode on developing
                #return obj.show_signal
                pass

        """ NOTE: Display message rows"""
        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole,) and isinstance(obj,CANLogPlay,):
            if (
                column
                == self.COL_DEVICE
            ):
                return obj.device_info

            if (
                column
                == self.COL_STATUS
            ):
                return obj.status_display

            if (
                column
                == self.COL_STR_DIFF
            ):
                return obj.initial_periodic

            if (
                column
                == self.COL_DIRECTION
            ):
                return obj.direction

            if (
                column
                == self.COL_CAN_ID_STR
            ):
                return f"0x{obj.can_id:X}"

            if (
                column
                == self.COL_MSG_NAME
            ):
                return obj.message_name

            if (
                column
                == self.COL_DATA_LEN
            ):
                return obj.data_len

            if (
                column
                == self.COL_RAW_DATA_BYTES
            ):
                return obj.raw_data

        return None

    def flags(
        self,
        index: QModelIndex,
    ) -> Qt.ItemFlag:
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags

        flags = (
            Qt.ItemFlag.ItemIsEnabled
            | Qt.ItemFlag.ItemIsSelectable
        )

        obj = index.internalPointer()

        if not isinstance(
            obj,
            CANLogPlay,
        ):
            return flags

        if index.column() in (
            self.COL_MSG_NAME,
            self.COL_CAN_ID_STR,
            self.COL_DEVICE,
            self.COL_STR_DIFF,
            self.COL_DIRECTION,
            self.COL_DATA_LEN,
            self.COL_RAW_DATA_BYTES,
        ):
            flags |= (
                Qt.ItemFlag.ItemIsEditable
            )

        return flags

    def setData(
        self,
        index: QModelIndex,
        value: Any,
        role: int = Qt.ItemDataRole.EditRole,
    ) -> bool:
        if (
            role
            != Qt.ItemDataRole.EditRole
        ):
            return False

        if not index.isValid():
            return False

        obj = index.internalPointer()

        if not isinstance(
            obj,
            CANLogPlay,
        ):
            return False

        if not (
            self.flags(index)
            & Qt.ItemFlag.ItemIsEditable
        ):
            return False

        column = index.column()

        if (
            column
            == self.COL_CAN_ID_STR
        ) and isinstance(value, MessageItem):
            obj.device_info = value.can_id
            obj.message_name = value.msg_name

        elif (
            column
            == self.COL_DEVICE
        ):
            obj.device_info = value

        elif (
            column
            == self.COL_STR_DIFF
        ):
            obj.initial_periodic = str(value)

        elif (
            column
            == self.COL_DIRECTION
        ):
            obj.direction = str(value)

        elif (
            column
            == self.COL_MSG_NAME
        ):
            obj.message_name = str(value)

        elif (
            column
            == self.COL_DATA_LEN
        ):
            obj.data_len = int(value)

        elif (
            column
            == self.COL_RAW_DATA_BYTES
        ):
            obj.raw_data = str(value)

        else:
            return False

        self.dataChanged.emit(
            index,
            index,
            [
                Qt.ItemDataRole.DisplayRole,
                Qt.ItemDataRole.EditRole,
                Qt.ItemDataRole.UserRole,
            ],
        )

        return True

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        if (
            role
            != Qt.ItemDataRole.DisplayRole
        ):
            return None

        if (
            orientation
            != Qt.Orientation.Horizontal
        ):
            return None

        headers = (
            "Status",
            "Channel",
            "Diff",
            "Direction",
            "CAN ID",
            "Message",
            "DLC",
            "Data",
        )

        if not 0 <= section < len(
            headers
        ):
            return None

        return headers[section]

""" NOTE:
SendViewModel
    │
    │ owns
    ▼
_entries: list[CANLogPlay]
    │
    │ reference
    ▼
QAbstractItemModel
    │
    ├──────────────────────────► QTreeView
    │                              │
    │                              │ uses
    │                              ▼
    │                     QStyledItemDelegate
    │                              │
    │                    editor value only
    │                              │
    ◄──────────────────────────────┘
         model.setData(index, value)
"""
class _TreeLogEditDelegate(
    QStyledItemDelegate
):
    def __init__(
        self,
        parent=None,
    ):
        super().__init__(parent)

        self._dlc_raw_binder = (
            DlcRawBinder()
        )

        self._row_height: Optional[int] = None

        # self._hovered_index = (
        #     QModelIndex()
        # )
    # def set_hovered_index(
    #     self,
    #     index: QModelIndex,
    # ) -> tuple[
    #     QModelIndex,
    #     QModelIndex,
    # ]:
    #     old = self._hovered_index

    #     new = (
    #         index
    #         if index.isValid()
    #         else QModelIndex()
    #     )

    #     if self._is_same_cell(
    #         old,
    #         new,
    #     ):
    #         return old, new

    #     self._hovered_index = new

    #     return old, new

    # def clear_hover(
    #     self,
    # ) -> QModelIndex:
    #     old = self._hovered_index

    #     self._hovered_index = (
    #         QModelIndex()
    #     )

    #     return old

    # def _is_same_cell(
    #     self,
    #     a: QModelIndex,
    #     b: QModelIndex,
    # ) -> bool:
    #     return (
    #         a.isValid()
    #         and b.isValid()
    #         and a.row() == b.row()
    #         and a.column() == b.column()
    #         and a.parent() == b.parent()
    #     )

    # def set_row_height(
    #     self,
    #     height: Optional[int],
    # ) -> None:
    #     self._row_height = (
    #         None
    #         if height is None
    #         else max(
    #             1,
    #             int(height),
    #         )
    #     )

    # def sizeHint(
    #     self,
    #     option,
    #     index,
    # ):
    #     size = super().sizeHint(
    #         option,
    #         index,
    #     )

    #     if (
    #         self._row_height
    #         is not None
    #     ):
    #         size.setHeight(
    #             self._row_height
    #         )

    #     return size

    def createEditor(
        self,
        parent,
        option,
        index,
    ):
        if not index.isValid():
            return None

        model = index.model()

        if not (
            model.flags(index)
            & Qt.ItemFlag.ItemIsEditable
        ):
            return None

        column = index.column()

        """ NOTE: Qt does not automatically call createEditor() again
                when user is opening the combobox
        """
        if (
            index.column() == LogEditViewModel_QtAdapter.COL_DEVICE):
            editor = QComboBox(parent)

            devices = index.data(LogEditViewModel_QtAdapter.DEVICE_OPTIONS_ROLE)

            """20260726 BUG: index.data() can return None"""
            for device in (devices or []):
                if isinstance(device, CANDeviceInfo):
                    editor.addItem(
                        device.device_id,
                        device,
                    )

            return editor

        if (
            index.column() == LogEditViewModel_QtAdapter.COL_CAN_ID_STR):
            editor = QComboBox(parent)

            dbc_data = index.data(LogEditViewModel_QtAdapter.DBC_OPTIONS_ROLE)

            """20260726 BUG: index.data() can return None"""
            for data in (dbc_data or []):
                if isinstance(data, MessageItem):
                    editor.addItem(
                        data.can_id_list_display,
                        data,
                    )

            return editor

        if (
            column
            == model.COL_STR_DIFF
        ):
            return TimeEditBox(
                parent
            )

        if (
            column
            == model.COL_CAN_ID_STR
        ):
            # return CanIdEditBox(
            #     parent
            # )
            return QComboBox(
                parent
            )

        if (
            column
            == model.COL_MSG_NAME
        ):
            return QLineEdit(
                parent
            )

        if (
            column
            == model.COL_DIRECTION
        ):
            editor = QComboBox(
                parent
            )

            editor.addItems(
                [
                    "Rx",
                    "Tx",
                ]
            )

            return editor

        if (
            column
            == model.COL_DATA_LEN
        ):
            editor = DLCSpinBox(
                parent
            )

            self._dlc_raw_binder.bind_dlc_editor(
                editor,
                index,
            )

            return editor

        if (
            column
            == model.COL_RAW_DATA_BYTES
        ):
            editor = RawBytesEditBox(
                parent
            )

            self._dlc_raw_binder.bind_raw_editor(
                editor,
                index,
            )

            return editor

        return None

    def setEditorData(
        self,
        editor,
        index,
    ) -> None:
        value = index.model().data(
            index,
            Qt.ItemDataRole.EditRole,
        )

        if isinstance(
            editor,
            TimeEditBox,
        ):
            editor.setText(
                str(
                    value
                    or "0ms"
                )
            )
            return

        if (
            index.column() == self.COL_DEVICE
            and isinstance(editor, QComboBox)
        ):
            device = value
            combo_index = editor.findData(device)
            editor.setCurrentIndex(combo_index)
            ...

        elif (
            index.column() == self.COL_CAN_ID
            and isinstance(editor, QComboBox)
        ):
            combo_index = editor.findData(value)
            editor.setCurrentIndex(combo_index)
            return
            ...

        elif (
            index.column() == self.COL_DIRECTION
            and isinstance(editor, QComboBox)
        ):
            text = str(
                value
                or "Rx"
            )

            combo_index = (
                editor.findText(
                    text
                )
            )

            editor.setCurrentIndex(
                combo_index
                if combo_index >= 0
                else 0
            )

            return

        if isinstance(
            editor,
            DLCSpinBox,
        ):
            editor.set_dlc_value(
                int(value)
            )

            return

        if isinstance(
            editor,
            RawBytesEditBox,
        ):
            editor.setText(
                str(
                    value
                    or ""
                )
            )

            obj = (
                index.internalPointer()
            )

            if isinstance(
                obj,
                CANLogPlay,
            ):
                self._dlc_raw_binder.normalize_raw_editor_for_row(
                    editor,
                    int(
                        obj.data_len
                    ),
                )

            return

        if isinstance(
            editor,
            QLineEdit,
        ):
            editor.setText(
                str(
                    value
                    or ""
                )
            )

            return

        super().setEditorData(
            editor,
            index,
        )

    def setModelData(
        self,
        editor,
        model,
        index,
    ) -> None:
        if isinstance(
            editor,
            TimeEditBox,
        ):
            editor._commit()

            value = (
                editor.text()
            )

        # elif isinstance(
        #     editor,
        #     CanIdEditBox,
        # ):
        #     editor._commit()
        #     value = editor.current_value()

        elif (
            index.column() == self.COL_DEVICE
            and isinstance(
                editor, 
                QComboBox)
        ):
            """20260726 BUG: QComboBox.currentData() can return None"""
            value = (
                editor.currentData()
            )
            if value is None:
                return

        elif (
            index.column() == self.COL_CAN_ID
            and isinstance(
                editor, 
                QComboBox)
        ):
            """20260726 BUG: QComboBox.currentData() can return None"""
            value = (
                editor.currentData()
            )
            if value is None:
                return

        elif (
            index.column() == self.COL_DIRECTION
            and isinstance(
                editor, 
                QComboBox)
        ):
            value = (
                editor.currentText()
            )
            

        elif isinstance(
            editor,
            DLCSpinBox,
        ):
            value = (
                editor.current_dlc_value()
            )

        elif isinstance(
            editor,
            RawBytesEditBox,
        ):
            value = (
                editor.text()
            )

        elif isinstance(
            editor,
            QLineEdit,
        ):
            value = (
                editor.text()
            )

        else:
            super().setModelData(
                editor,
                model,
                index,
            )
            return

        model.setData(
            index,
            value,
            Qt.ItemDataRole.EditRole,
        )


_HOVER_STYLESHEET = """
    QTreeView::item:hover {
        background: rgba(255, 255, 255, 12);
    }
"""
# -----------------------------
# Main panel
# -----------------------------
class CustomSendMessagePanel(QtWidgets.QWidget):
    # send_status_signal = QtCore.Signal(object)

    def __init__(
        self,
        parent: QWidget,
        vm: ScheduleViewModel
    ):
        super().__init__(parent)
        self.vm = vm

        self._build_ui()

        # self.spin_dlc.valueChanged.connect(self._on_dlc_changed)
        # self.spin_cycle.valueChanged.connect(self._refresh_buttons)
        # self.chk_use_dbc.toggled.connect(self._on_use_dbc_toggled)
        # self.combo_msg.currentIndexChanged.connect(self._on_message_changed)
        # self.edit_msg.textChanged.connect(self._on_message_changed)
        """ NOTE: Flip current editing entry if user selecting one"""
        self.view.selectionModel().currentChanged.connect(
            lambda current, previous:
                setattr(
                    self.vm,
                    "editing_entry",
                    current.internalPointer(),
                )
                if (
                    current.isValid()
                    and isinstance(
                        current.internalPointer(),
                        CANLogPlay,
                    )
                )
                else None
        )
        self.btn_send.clicked.connect(
            lambda:
                self.vm.pauseMsg(
                    self.vm.editing_entry.data_model
                )
                if self.vm.editing_entry.is_play
                else
                self.vm.sendMsgLoop(
                    self.vm.editing_entry.data_model
                )
        )

        self.btn_remove.clicked.connect(
            lambda:
                self.vm.removeMsg(
                    self.vm.editing_entry.data_model
                )
        )

        self.btn_remove_all.clicked.connect(
            lambda:
                self.vm.clear()
        )

        self.btn_pause_all.clicked.connect(
            lambda:
                [
                    self.vm.pauseMsg(
                        play.data_model
                    )
                    for play in self.vm.entries
                    if play.is_play
                ]
        )

        # Initialize button states
        # self._refresh_buttons()
        # self._update_disconnect_overlay()

    # -----------------------------
    # UI construction
    # -----------------------------
    def _build_ui(
        self,
    ):
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        btn_row_widget = QtWidgets.QWidget(self)
        btn_row = QtWidgets.QHBoxLayout(btn_row_widget)
        btn_row.setContentsMargins(0, 0, 0, 0)
        btn_row.setSpacing(8)
        btn_row.addStretch(1)

        self.btn_add = QtWidgets.QPushButton("Add", self)
        self.btn_add.setFixedWidth(80)
        btn_row.addWidget(self.btn_add)

        self.btn_remove = QtWidgets.QPushButton("Remove", self)
        self.btn_remove.setFixedWidth(90)
        btn_row.addWidget(self.btn_remove)

        self.btn_send = QtWidgets.QPushButton("Send", self)
        self.btn_send.setFixedWidth(80)
        btn_row.addWidget(self.btn_send)

        self.btn_pause_all = QtWidgets.QPushButton("Pause all", self)
        self.btn_pause_all.setFixedWidth(100)
        self.btn_pause_all.setEnabled(False)
        btn_row.addWidget(self.btn_pause_all)

        self.btn_remove_all = QtWidgets.QPushButton("Remove All", self)
        self.btn_remove_all.setFixedWidth(110)
        self.btn_remove_all.setEnabled(False)
        btn_row.addWidget(self.btn_remove_all)

        root.addWidget(btn_row_widget)

        # Raw bytes paste input
        # self.raw_row_widget = QtWidgets.QWidget(self)
        # raw_row = QtWidgets.QHBoxLayout(self.raw_row_widget)
        # raw_row.setContentsMargins(0, 0, 0, 0)
        # raw_row.setSpacing(8)
        # self.lbl_raw_bytes = QtWidgets.QLabel("Raw Bytes:", self.raw_row_widget)
        # raw_row.addWidget(self.lbl_raw_bytes)

        # self.edit_raw_bytes = RawBytesEditBox(self.raw_row_widget)
        # raw_row.addWidget(self.edit_raw_bytes, 1)

        # self.lbl_raw_status = QtWidgets.QLabel("")
        # self.lbl_raw_status.setMinimumWidth(180)
        # raw_row.addWidget(self.lbl_raw_status)

        #root.addWidget(self.raw_row_widget)

        # Data bytes group
        # self.grp_data = QtWidgets.QGroupBox("", self)
        # self.grp_data_layout = QtWidgets.QGridLayout(self.grp_data)
        # self.grp_data_layout.setContentsMargins(0, 0, 0, 0)
        # self.grp_data_layout.setHorizontalSpacing(0)
        # self.grp_data_layout.setVerticalSpacing(0)

        # root.addWidget(self.grp_data)

        # Build initial byte editors based on DLC
        # self._hex_edits: List[HexByteLineEdit] = []
        # self._rebuild_hex_editors(self.spin_dlc.current_len_value())

        self.view = QTreeView(self)

        self.model_ = (
            LogEditViewModel_QtAdapter(
                self.vm,
                self,
            )
        )

        self.view.setModel(
            self.model_
        )

        # self.select_model = (
        #     _TreeLogEditDelegate(
        #         self.model_,
        #         self.view,
        #     )
        # )

        # self.view.setSelectionModel(
        #     self.select_model
        # )

        self._edit_delegate = (
            _TreeLogEditDelegate(
                self.view
            )
        )

        self.view.setItemDelegate(
            self._edit_delegate
        )

        mono = QFont(
            "Consolas",
            10,
        )

        mono.setStyleHint(
            QFont.StyleHint.Monospace
        )

        self.view.setFont(
            mono
        )

        header = self.view.header()

        header.setStretchLastSection(
            False
        )

        header.setSectionResizeMode(
            QHeaderView.ResizeMode.Interactive
        )

        header.setFixedHeight(
            20
        )

        self.view.setColumnWidth(
            LogEditViewModel_QtAdapter.COL_DEVICE,
            110,
        )

        self.view.setColumnWidth(
            LogEditViewModel_QtAdapter.COL_STR_DIFF,
            90,
        )

        self.view.setColumnWidth(
            LogEditViewModel_QtAdapter.COL_DIRECTION,
            90,
        )

        self.view.setColumnWidth(
            LogEditViewModel_QtAdapter.COL_CAN_ID_STR,
            90,
        )

        self.view.setColumnWidth(
            LogEditViewModel_QtAdapter.COL_DATA_LEN,
            70,
        )

        self.view.setColumnWidth(
            LogEditViewModel_QtAdapter.COL_RAW_DATA_BYTES,
            1120,
        )

        self.view.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection
        )

        self.view.setEditTriggers(
            QAbstractItemView.EditTrigger.DoubleClicked
            | QAbstractItemView.EditTrigger.EditKeyPressed
            | QAbstractItemView.EditTrigger.SelectedClicked
        )

        self.view.setUniformRowHeights(
            True
        )

        self.view.setAnimated(
            False
        )

        self.view.setAutoScroll(
            True
        )

        self.view.viewport().setMouseTracking(
            True
        )

        self.view.setStyleSheet(
            self._HOVER_STYLESHEET
        )

        self.view.viewport().installEventFilter(
            self
        )

        layout = QVBoxLayout(
            self
        )

        layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        layout.addWidget(
            self.view
        )
        root.addWidget(self.view, 1)

        self.add_btn = QToolButton(
            self.view.viewport()
        )

        self.add_btn.setText("+")
        self.add_btn.setFixedSize(
            28,
            28,
        )

        self.add_btn.setToolTip(
            "Add CAN message"
        )

        self.setLayout(root)


    # def resizeEvent(self, event):
    #     super().resizeEvent(event)
    #     if hasattr(self, "_disconnected_overlay"):
    #         self._disconnected_overlay.setGeometry(self.rect())
    #         if self._disconnected_overlay.isVisible():
    #             self._disconnected_overlay.raise_()

    # def _on_channels_state_changed(self, *_):
    #     if hasattr(self, "combo_channel"):
    #         prev_channel_name = self.combo_channel.currentText().strip()
    #         self.combo_channel.refresh_channels()
    #         if prev_channel_name:
    #             idx = self.combo_channel.findText(prev_channel_name, Qt.MatchExactly)
    #             if idx >= 0:
    #                 self.combo_channel.setCurrentIndex(idx)
    #     self._update_disconnect_overlay()

    # def _is_channel_disconnected(self) -> bool:
    #     if self.handle is None:
    #         return True

    #     checker = getattr(self.cnt_model, "is_channel_disconnected", None)
    #     if checker is None:
    #         return False

    #     try:
    #         return bool(checker(self.handle))
    #     except TypeError:
    #         return bool(checker())

    # def _update_disconnect_overlay(self):
    #     if not hasattr(self, "_disconnected_overlay"):
    #         return
    #     disconnected = self._is_channel_disconnected()
    #     if disconnected:
    #         self._disconnected_overlay.setGeometry(self.rect())
    #         self._disconnected_overlay.show()
    #         self._disconnected_overlay.raise_()
    #     else:
    #         self._disconnected_overlay.hide()

    # def _on_use_dbc_toggled(self, checked: bool):
    #     self.spin_dlc.setEnabled(not checked)
    #     self.raw_row_widget.setVisible(not checked)
    #     self.grp_data.setVisible(not checked)
    #     self.tree.set_allow_edit_raw_data(not checked)
    #     self.tree.set_message_name_visible(checked)
    #     if checked:
    #         self.msg_stack.setCurrentWidget(self.combo_msg)
    #         if self.combo_msg.current_value() is None and self.combo_msg.count() > 0:
    #             self.combo_msg.setCurrentIndex(0)
    #     else:
    #         self.msg_stack.setCurrentWidget(self.edit_msg)
    #         # if not self._is_syncing_event:
    #         #     self.spin_dlc.set_len_value(8)
    #         #     self._raw_baseline = None
    #         #     self._rebuild_hex_editors(8)
    #         #     self._set_hex_data(bytes([0] * 8), default_mask=[True] * 8)
    #     self._on_message_changed("")

    # def _on_event_signal_select(self, selection: SignalFilter):
    #     self._refresh_buttons()

    # -----------------------------
    # Sender events integration
    # -----------------------------
    # def _on_sender_status_changed(self, payload):
    #     self.send_status_signal.emit(payload)

    # def _log_added_state(self, source: str):
    #     if not self._added:
    #         LOG.debug("[SEND_PANEL][_added] %s | count=0 | entries=[]", source)
    #         return

    #     entries = []
    #     for can_id, entry in sorted(self._added.items(), key=lambda it: int(it[0])):
    #         state = getattr(entry, "send_state", SendState.NONE)
    #         state_name = state.name if hasattr(state, "name") else str(state)
    #         entries.append(f"0x{int(can_id):X}:{state_name}")

    #     LOG.debug(
    #         "[SEND_PANEL][_added] %s | count=%d | entries=[%s]",
    #         source,
    #         len(self._added),
    #         ", ".join(entries),
    #     )


    # -----------------------------
    # Message list / Combo integration
    # -----------------------------
    # def _rebuild_hex_editors(self, data_len: int, data: Optional[bytes] = None, baseline: Optional[bytes] = None):
    #     # Clear layout items
    #     while self.grp_data_layout.count():
    #         item = self.grp_data_layout.takeAt(0)
    #         w = item.widget()
    #         if w is not None:
    #             w.deleteLater()

    #     self._hex_edits = []
    #     #self.grp_data.setTitle(f"Data Bytes ({data_len})")
    #     cols = 16
    #     rows = max(1, math.ceil(data_len / cols))

    #     for i in range(data_len):
    #         e = HexByteLineEdit(self.grp_data)
    #         if baseline is not None and i < len(baseline):
    #             e.set_baseline(baseline[i])
    #         else:
    #             e.clear_baseline()

    #         if data is not None and i < len(data):
    #             e.set_value(data[i], is_default=True)
    #         else:
    #             e.set_value(0, is_default=True)
    #         r = i // cols
    #         c = i % cols
    #         self.grp_data_layout.addWidget(e, r, c)
    #         self._hex_edits.append(e)

    #     # add spacers so grid looks clean
    #     for r in range(rows):
    #         self.grp_data_layout.setRowStretch(r, 0)
    #     self.grp_data_layout.setColumnStretch(cols, 1)

    #     # hook edit events
    #     for e in self._hex_edits:
    #         e.textEdited.connect(self._refresh_buttons)

    # def _set_hex_data(self, data: bytes, default_mask: Optional[List[bool]] = None, baseline: Optional[bytes] = None):
    #     for i, e in enumerate(self._hex_edits):
    #         if baseline is not None and i < len(baseline):
    #             e.set_baseline(baseline[i])
    #         elif baseline is not None:
    #             e.clear_baseline()
    #         v = data[i] if i < len(data) else 0
    #         is_default = False
    #         if default_mask is not None and i < len(default_mask):
    #             is_default = default_mask[i]
    #         e.set_value(v, is_default=is_default)
    # -----------------------------
    # Event handlers
    # -----------------------------

    # def _get_default_mask(self) -> List[bool]:
    #     """
    #     True  = byte is still default (not user-edited)
    #     False = user modified
    #     """
    #     mask = []
    #     for e in self._hex_edits:
    #         mask.append(e._is_default_value)
    #     return mask

    # def _on_dlc_changed(self, dlc: int):
    #     prev_data = hex_raw_to_bytes(self.get_hex_raw_string())
    #     prev_default_mask = self._get_default_mask()
    #     data_len = self.candb.get_length_from_dlc(dlc)
    #     # Trim or extend data safely
    #     new_data = prev_data[:data_len]
    #     new_mask = prev_default_mask[:data_len]

    #     # Extend with DEFAULT zeros if DLC increased
    #     while len(new_data) < data_len:
    #         new_data += b"\x00"
    #         new_mask.append(True)  # <-- KEY LINE

    #     baseline = self._raw_baseline
    #     if baseline is not None:
    #         baseline = baseline[:data_len]

    #     self._rebuild_hex_editors(
    #         data_len,
    #         data=new_data,
    #         baseline=baseline
    #     )

    #     # Restore default/user intent state explicitly
    #     for i, e in enumerate(self._hex_edits):
    #         e._is_default_value = new_mask[i]
    #         e._apply_color()
    #     self._refresh_buttons()

    # def _on_message_changed(self, _t: str):
    #     cid = self._current_selected_can_id()
    #     if cid is None:
    #         self._refresh_buttons()
    #         return

    #     cid = int(cid)
    #     existing = self._added.get(cid)
    #     if existing is not None:
    #         try:
    #             cycle_ms = max(1, int(float(existing.timediff or 0.0) * 1000.0))
    #             self.spin_cycle.setValue(cycle_ms)
    #         except Exception:
    #             pass

    #         if hasattr(self, "combo_channel"):
    #             selected_name = self._channel_name_for_channel_value(getattr(existing, "channel", None))
    #             if selected_name:
    #                 idx = self.combo_channel.findText(str(selected_name), Qt.MatchExactly)
    #                 if idx >= 0:
    #                     self.combo_channel.setCurrentIndex(idx)

    #         data_len = max(0, int(existing.data_len or 0))
    #         self.spin_dlc.set_len_value(data_len)
    #         payload = hex_raw_to_bytes(str(existing.raw_data or ""))
    #         payload = payload[:data_len].ljust(data_len, b"\x00")
    #         self._rebuild_hex_editors(data_len)
    #         self._set_hex_data(payload, default_mask=[True] * data_len)
    #         self._refresh_buttons()
    #         return

    #     if self.chk_use_dbc.isChecked():
    #         can_id = self.combo_msg.current_value()
    #         if can_id is None and self.combo_msg.count() > 0:
    #             self.combo_msg.setCurrentIndex(0)
    #             can_id = self.combo_msg.current_value()
    #         if can_id is not None:
    #             msg = self.candb.get_message(can_id)
    #             if msg.cycle_time is not None:
    #                 self.spin_cycle.setValue(int(msg.cycle_time))
    #             else:
    #                 self.spin_cycle.setValue(0)
    #             self.spin_dlc.set_len_value(msg.length)
    #         self._rebuild_hex_editors(self.spin_dlc.current_len_value())
    #         self._set_hex_data(
    #             bytes([0] * self.spin_dlc.current_len_value()),
    #             default_mask=[True] * self.spin_dlc.current_len_value(),
    #         )

    #     self._refresh_buttons()

    # def _on_raw_bytes_debounced(self):
    #     data = self.edit_raw_bytes.current_value()
    #     if not data:
    #         self._raw_baseline = None
    #         if not self.chk_use_dbc.isChecked():
    #             self.spin_dlc.set_len_value(8)
    #             self._rebuild_hex_editors(8)
    #             self._set_hex_data(bytes([0] * 8), default_mask=[True] * 8)
    #             self._refresh_buttons()
    #         return
    #     self.spin_dlc.set_len_value(len(data))
    #     padded = data.ljust(len(data), b"\x00")
    #     self._raw_baseline = padded
    #     self._rebuild_hex_editors(len(data), data=padded, baseline=padded)
    #     self._refresh_buttons()

    # def get_hex_raw_string(self) -> str:
    #     """
    #     Read current values from self._hex_edits (List[HexByteLineEdit])
    #     and return CANLogLine-compatible raw hex string.

    #     Example:
    #         "00 1A FF"
    #     """
    #     parts: list[str] = []

    #     for e in self._hex_edits:
    #         v = e.value()          # HexByteLineEdit.value() -> Optional[int]
    #         if v is None:
    #             parts.append("00")
    #         else:
    #             parts.append(f"{int(v):02X}")

    #     return " ".join(parts)

    # @property
    # def entries(self) -> List[CANLogPlay]:
    #     return list(self._added.values())

    # def _on_add_or_update_clicked(self):
    #     LOG.debug("_on_add_or_update_clicked")
    #     self._log_added_state("button Add/Update pressed (before request)")
    #     cid = self._current_selected_can_id()
    #     if cid is None:
    #         return
    #     cid = int(cid)
    #     entry = self._build_line_from_ui(cid)
    #     if cid in self._added:
    #         entry.send_state = getattr(self._added[cid], "send_state", SendState.NONE)
    #     else:
    #         entry.send_state = SendState.NONE

    #     periodic_s = float(entry.timediff or 0.0)
    #     if periodic_s <= 0:
    #         LOG.warning("[SEND_PANEL][ADD] invalid periodic for can_id=%s", cid)
    #         return

    #     self._added[cid] = entry
    #     self.tree.set_data(self.entries)

    #     self.sender.send_msg_loop_from_line(entry, initial_periodic=periodic_s)

    #     # Keep current values as clean baseline after Add/Update.
    #     # This ensures Update is disabled until user changes something again.
    #     self._raw_baseline = None
    #     self.edit_raw_bytes.setText("")

    #     current_data = hex_raw_to_bytes(entry.raw_data or "")
    #     self._set_hex_data(
    #         current_data,
    #         default_mask=[True] * self.spin_dlc.current_len_value(),
    #     )
    #     self._log_added_state("button Add/Update pressed (after request)")
    #     self._refresh_buttons()

    # def _on_remove_clicked(self):
    #     LOG.debug("_on_remove_clicked")
    #     self._log_added_state("button Remove pressed (before request)")
    #     cid = self._current_selected_can_id()
    #     if cid is None:
    #         return
    #     cid = int(cid)
    #     channel_id = self._channel_id_from_handle()
    #     if channel_id is None:
    #         LOG.warning("[SEND_PANEL][REMOVE] invalid handle for channel_id, can_id=%s", cid)
    #         return
    #     LOG.debug(f"[SEND_PANEL][REMOVE] request remove for can_id={cid}")
    #     self.sender.remove_msg(channel_id, cid)
    #     self._log_added_state("button Remove pressed (after request, waiting status)")

    # def _on_send_pause_resume_clicked(self):
    #     LOG.debug("_on_send_pause_resume_clicked")
    #     cid = self._current_selected_can_id()
    #     if cid is None:
    #         return
    #     cid = int(cid)
    #     channel_id = self._channel_id_from_handle()
    #     if channel_id is None:
    #         LOG.warning("[SEND_PANEL][SEND] invalid handle for channel_id, can_id=%s", cid)
    #         return
    #     if cid not in self._added:
    #         return
    #     entry = self._added[cid]
    #     if getattr(entry, "send_state", SendState.NONE) == SendState.DISCONNETED:
    #         LOG.debug("[SEND_PANEL][SEND] blocked action for disconnected entry can_id=%s", cid)
    #         return

    #     cycle_ms = float(self.spin_cycle.value())
    #     periodic_s = cycle_ms / 1000.0

    #     # Decide action based on current button mode
    #     if self._send_button_mode == "SEND_FIRST":
    #         if cycle_ms < 1:
    #             self.sender.send_once_from_entry(entry)
    #             return
    #         self.sender.resume(channel_id, cid)
    #         return

    #     if self._send_button_mode == "PAUSE":
    #         self.sender.stop(channel_id, cid)
    #         return

    #     if self._send_button_mode == "RESUME":
    #         self.sender.resume(channel_id, cid)
    #         return

    # def _on_pause_all_clicked(self):
    #     LOG.debug("_on_pause_all_clicked")
    #     channel_id = self._channel_id_from_handle()
    #     if channel_id is None:
    #         LOG.warning("[SEND_PANEL][ALL] invalid handle for channel_id")
    #         return
    #     if self._send_all_button_mode == "SEND_ALL":
    #         self.sender.resume(channel_id, None)
    #         return

    #     if self._send_all_button_mode == "PAUSE_ALL":
    #         self.sender.stop(channel_id, None)
    #         return

    #     self.sender.resume(channel_id, None)


    # # -----------------------------
    # # State / dirty / buttons
    # # -----------------------------
    # def _current_selected_can_id(self) -> Optional[int]:
    #     if self.chk_use_dbc.isChecked():
    #         return self.combo_msg.current_value()
    #     return self.edit_msg.current_value()

    # def _channel_id_from_handle(self) -> Optional[int]:
    #     combo = getattr(self, "combo_channel", None)
    #     if combo is not None:
    #         selected_name = combo.currentText().strip()
    #         if selected_name:
    #             for handle in self.cnt_model.acquired_channels.keys():
    #                 try:
    #                     info = self.cnt_model.get_channel_info(handle)
    #                     name = str(getattr(info, "name", "") or "").strip()
    #                     if name == selected_name:
    #                         return int(handle.channel_idx)
    #                 except Exception:
    #                     continue
    #     if self.handle is None:
    #         return None
    #     return int(self.handle.channel_idx)
