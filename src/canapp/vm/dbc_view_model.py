from __future__ import annotations

from typing import Any
from dataclasses import dataclass

from PySide6.QtCore import Signal, Slot, QTimer, QObject

# from .base_view_model import BaseViewModel
from cansrv.file_service import get_file_service, DBCId
from cansrv.application_events import DBCLoadedEvent
from fs_test.mock_vm import ParseModel, DBCModel
from pathlib import Path
from PySide6.QtCore import (
    Qt,
    QModelIndex,
    QAbstractListModel,
)
from typing import Protocol, TypeVar, Generic

class DisplayItem(Protocol):
    @property
    def show(self) -> str:
        ...

@dataclass(frozen=True)
class DbcItem:
    dbc_id: DBCId
    file_path: str

@dataclass(frozen=True)
class MessageItem:
    can_id: int
    msg_name: str

    @property
    def show(self) -> str:
        return f"[{self.can_id:03X}] {self.msg_name}"

@dataclass(frozen=True)
class SignalItem:
    can_id: int
    signal_name: str
    msg_name: str

    @property
    def show(self) -> str:
        return f"[{self.can_id:03X}] {self.msg_name} - {self.signal_name}"
    
T = TypeVar("T", bound=DisplayItem)

class ListModel(QAbstractListModel, Generic[T]):
    ItemRole = Qt.UserRole + 1

    def __init__(
        self,
        items: list[T],
        parent=None,
    ):
        super().__init__(parent)
        self._items = items

    def rowCount(
        self,
        parent: QModelIndex = QModelIndex(),
    ) -> int:
        if parent.isValid():
            return 0

        return len(self._items)

    def data(
        self,
        index: QModelIndex,
        role: int = Qt.DisplayRole,
    ):
        if not index.isValid():
            return None

        row = index.row()

        if not 0 <= row < len(self._items):
            return None

        item = self._items[row]

        if role == Qt.DisplayRole:
            return item.show

        if role == self.ItemRole:
            return item

        return None

    def roleNames(self):
        return {
            self.ItemRole: b"item",
        }
    
class DbcViewModel(QObject, DBCModel):
    dbcChanged = Signal()
    filterChanged = Signal()
    onMessageSelect = Signal()
    signalSelectChanged = Signal()

    def __init__(self):
        super().__init__()
        self._file_service = get_file_service()
        self._dbc_id: DBCId | None = None

        self._items: list[DbcItem] = []
        self._message_lists: list[MessageItem] = []
        self._signal_lists: list[SignalItem] = []

        self.dbcs = ListModel[DbcItem](
            self._items,
            self,
        )

        self.messages = ListModel[MessageItem](
            self._message_lists,
            self,
        )

        self.signals = ListModel[SignalItem](
            self._signal_lists,
            self,
        )

        self._curMessage: MessageItem | None = None
        self._curSignal: SignalItem | None = None

        self._msg_filter = "Message Filter"
        self._sig_filter = "Signal Filter"

    @property
    def curMessage(self):
        return self._curMessage

    """ NOTE: Selecting message, flip signals"""
    @curMessage.setter
    def curMessage(self, value):
        if self._curMessage == value:
            return

        self._curMessage = value
        msg = self._curMessage
        signal_lists: list[SignalItem] = []
        for sig in list(msg.signals):
            signal_lists.append(
                SignalItem(
                    can_id=msg.frame_id,
                    msg_name=msg.name,
                    signal_name=sig.name,
                )
            )
        self._signal_lists = signal_lists

    @property
    def curSignal(self):
        return self._curSignal

    @curSignal.setter
    def curSignal(self, value):
        if self._curSignal == value:
            return

        self._curSignal = value
        self.signalSelectChanged.emit()

    @property
    def msgFilter(self):
        return self._msg_filter

    @msgFilter.setter
    def msgFilter(self, value):
        if self._msg_filter == "Message Filter":
            return

        self._msg_filter = value
        self.filterChanged.emit()

    @property
    def sigFilter(self):
        return self._sig_filter

    @sigFilter.setter
    def sigFilter(self, value):
        if self._sig_filter == "Signal Filter":
            return

        self._sig_filter = value
        self.filterChanged.emit()

    @property
    def dbc_id(self):
        return self._dbc_id

    @dbc_id.setter
    def dbc_id(self, value):
        if self._dbc_id == value:
            return
        self._dbc_id = value
        self.dbcChanged.emit()

    def on_dbc_loaded(self, event: DBCLoadedEvent):
        DBCModel.on_dbc_model_loaded(event)

        candb = self._file_service.get_candb_data(event.dbc_id)
        db_path = str(candb.file_path)

        item = DbcItem(event.dbc_id, db_path)
        if item not in self._items:
            self._items.append(item)

        msg_defs = list(candb.messages)

        message_lists: list[MessageItem] = []
        signal_lists: list[SignalItem] = []

        for msg in msg_defs:
            message_lists.append(
                MessageItem(can_id=msg.frame_id, msg_name=msg.name)
            )
        for sig in list(msg_defs[0].signals):
            signal_lists.append(
                SignalItem(
                    can_id=msg.frame_id,
                    msg_name=msg.name,
                    signal_name=sig.name,
                )
            )

        # NOTE: Update QT UI
        self._message_lists = message_lists
        self._signal_lists = signal_lists

        # NOTE: new dbc load does not means the screen must display it, just add to the list
        self.dbc_id = event.dbc_id

    @Slot(str)
    def loadDBC(self, db_file_path: str) -> None:
        # TODO: Could implement cache here if the same file_path and track changed
        self._file_service.parse_dbc_file(db_file_path)

    """ ui binding 
    Store selected_dbc in ViewModel
    ComboBox
    ↓
    currentIndexChanged
    ↓
    vm.selected_dbc = ...
    ↓
    dbcChanged.emit()
    ↓
    Properties re-evaluate
    """
    @property
    def dbcNum(self) -> int:
        return len(self._items)
    
    @property
    def hasDbc(self) -> bool:
        return self._dbc_id is not None

    @property
    def dbcMessagesCount(self) -> int:
        if self.dbc_id is None:
            return 0
        candb = get_file_service().get_candb_data(self.dbc_id)
        msg_defs = list(candb.messages)
        return len(msg_defs)

    @property
    def currentDbcFile(self) -> str:
        #TODO: Could use the DbcItem for cache instead
        candb = get_file_service().get_candb_data(self.dbc_id)
        return str(candb.file_path)
