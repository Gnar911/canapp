from __future__ import annotations

from typing import Any
from dataclasses import dataclass
import os

from PySide6.QtCore import Signal, Slot, QTimer, QObject

# from .base_view_model import BaseViewModel
from cansrv.file_service import get_file_service, DBCId, FileService
from cansrv.can_srv import CANService, get_can_service
from cansrv.event_dispatcher import DBCLoadedEvent
# from cansrv.application_events import DBCLoadedEvent
from lw.srv_event import SrvEvent
from cansrv.test.mock_vm import ParseModel, DBCModel
from pathlib import Path
from PySide6.QtCore import (
    Qt,
    QModelIndex,
    QAbstractListModel,
)
from typing import Protocol
from lw.logger_setup import LOG

class DisplayItem(Protocol):
    @property
    def show(self) -> str:
        ...

@dataclass(frozen=True)
class DbcItem(DisplayItem):
    dbc_id: DBCId
    file_path: str
    
    @property
    def show(self) -> str:
        #LOG.debug("show: %s",os.path.basename(self.file_path))
        return os.path.basename(self.file_path)
    
@dataclass(frozen=True)
class MessageItem(DisplayItem):
    can_id: int
    msg_name: str
    signals: list[SignalItem]

    @property
    def show(self) -> str:
        return f"[{self.can_id:03X}] {self.msg_name}"

@dataclass(frozen=True)
class SignalItem(DisplayItem):
    can_id: int
    signal_name: str
    msg_name: str

    @property
    def show(self) -> str:
        return f"[{self.can_id:03X}] {self.msg_name} - {self.signal_name}"

    
class DbcViewModel(QObject, DBCModel):
    dbcChanged = Signal()
    filterChanged = Signal()
    onMessageSelect = Signal()
    signalSelectChanged = Signal()

    def __init__(self, can_service: CANService, file_service: FileService):
        super().__init__()
        # injected services (fall back to singletons)
        self._can_service = can_service
        self._file_service = file_service
        file_service.subscribe_any(self.on_status_callback)
        can_service.subscribe(self.on_status_callback)
        self._dbc_id: DBCId | None = None

        self._items: list[DbcItem] = []
        self._message_lists: list[MessageItem] = []
        self._signal_lists: list[SignalItem] = []

        self._curMessage: MessageItem | None = None
        self._curSignal: SignalItem | None = None

        self._msg_filter = "Message Filter"
        self._sig_filter = "Signal Filter"

    @property
    def curMessage(self):
        return self._curMessage

    """ NOTE: Selecting message, flip signals"""
    @curMessage.setter
    def curMessage(self, value: MessageItem):
        if self._curMessage == value:
            return

        self._curMessage = value
        msg = self._curMessage
        self._signal_lists = msg.signals
        self.signalSelectChanged.emit()


    @property
    def curSignal(self):
        return self._curSignal

    @curSignal.setter
    def curSignal(self, value: SignalItem):
        if self._curSignal == value:
            return

        self._curSignal = value
        #self.signalSelectChanged.emit()

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

    """ BUG: AttributeError: 'ScanDeviceUnpluggedStatus' object has no attribute 'dbc_id'"""
    def on_status_callback(self, event: SrvEvent):
        super().on_status_callback(event)

        if not isinstance(event, DBCLoadedEvent):
            return 

        if event.dbc_id is None:
            return
        
        candb = self._file_service.get_candb_data(event.dbc_id)
        db_path = str(candb.file_path)

        item = DbcItem(event.dbc_id, db_path)
        if item not in self._items:
            self._items.append(item)

        msg_defs = list(candb.messages)

        message_lists: list[MessageItem] = []
        signal_lists: list[SignalItem] = []

        for msg in msg_defs:
            signals = []
            for sig in list(msg.signals):
                signals.append(
                    SignalItem(
                        can_id=msg.frame_id,
                        msg_name=msg.name,
                        signal_name=sig.name,
                    )
                )

            message_lists.append(
                MessageItem(can_id=msg.frame_id, msg_name=msg.name, signals=signals)
            )

            signal_lists.extend(signals)

        # NOTE: Update QT UI
        self._message_lists = message_lists
        self._signal_lists = signal_lists

        self.onMessageSelect.emit()
        self.signalSelectChanged.emit()

        # NOTE: new dbc load does not means the screen must display it, just add to the list
        self.dbc_id = event.dbc_id

    @Slot(str)
    def loadDBC(self, db_file_path: str):
        # TODO: Could implement cache here if the same file_path and track changed
        return self._file_service.parse_dbc_file(db_file_path)

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
        candb = self._file_service.get_candb_data(self.dbc_id)
        msg_defs = list(candb.messages)
        return len(msg_defs)

    @property
    def currentDbcFile(self) -> str:
        #TODO: Could use the DbcItem for cache instead
        candb = self._file_service.get_candb_data(self.dbc_id)
        return str(candb.file_path)
