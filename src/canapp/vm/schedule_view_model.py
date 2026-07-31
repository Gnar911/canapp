from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from PySide6.QtCore import Signal, Slot, QObject
from copy import deepcopy

from cansrv.test.mock_vm import SendStatusVM, ScannerVM, DBCModel
from lw.qt.qtobject_adapter import QtViewModelBase
from cansrv.file_service import FileService, LogId, MetaDataStorageInterface, DBCId, CANDBInfo
from cansrv.test.mock_vm import *
from cansrv.can_srv import CANService, CANDeviceInfo
from cansrv.snd_contract import (
    SndAdd,
    SndClear,
    SndPause,
    SndRemove,
    SndResume,
    SndUpdateData,
    SndUpdatePeriod,
    SndDeviceAccquired,
    SndDeviceUnaccquired,
    SndIdentity,
    SndCmd
)
from lw.srv_event import SrvEvent
from cansrv.module.fs_core import LogRecord
from canapp.vm.data_object import (
    CANLogLine,
    DecodedSignalLine,
)
from cansrv.event_dispatcher import *

""" NOTE: For DBC's message selection"""
@dataclass(frozen=True)
class MessageItem:
    can_id: int
    msg_name: str

    @property
    def can_id_list_display(self) -> str:
        return str(self.can_id)

""" NOTE: Data model"""
@dataclass
class CANPlayEntry:
    device_info: CANDeviceInfo | None
    entry: LogRecord
    initial_periodic_second: float

    @property
    def identity(self) -> tuple[str, int]:
        device_id = ""
        if self.device_info is not None:
            device_id = self.device_info.device_id
        return (
            device_id,
            int(self.entry.can_id),
        )

@dataclass
class DecodedSignalLine:
    name: str
    raw_value: str
    unit: str
    parent: "CANLogPlay" | None = field(
        default=None,
        repr=False,
        compare=False,
    )

    @property
    def signal_line(self) -> str:
        text = f"{self.name}: {self.raw_value}"

        if self.unit:
            text += f" {self.unit}"

        return text


""" NOTE: Data View"""
@dataclass
class CANLogPlay:
    is_play: bool
    is_pause: bool
    is_disconnet: bool
    data_model: CANPlayEntry
    message_name: str = ""
    signals: list[DecodedSignalLine] = field(default=list)

    @property
    def device_info(self) -> CANDeviceInfo | None:
        return self.data_model.device_info

    @device_info.setter
    def device_info(self, value: CANDeviceInfo | None) -> None:
        self.data_model.device_info = value
    
    @property
    def initial_periodic_second(self) -> float:
        return float(self.data_model.initial_periodic_second)

    @initial_periodic_second.setter
    def initial_periodic_second(self, value: float) -> None:
        self.data_model.initial_periodic_second = float(value)

    """ NOTE: Add passthroughs"""
    @property
    def channel(self) -> str:
        return str(self.data_model.entry.channel)

    @channel.setter
    def channel(self, value: str) -> None:
        self.data_model.entry.channel = str(value)

    @property
    def can_id(self) -> int:
        return int(self.data_model.entry.can_id)

    @can_id.setter
    def can_id(self, value: int) -> None:
        self.data_model.entry.can_id = int(value)

    @property
    def direction(self) -> str:
        return str(self.data_model.entry.direction)

    @direction.setter
    def direction(self, value: str) -> None:
        self.data_model.entry.direction = str(value)

    @property
    def data_len(self) -> int:
        return int(self.data_model.entry.data_len)

    @data_len.setter
    def data_len(self, value: int) -> None:
        value = max(0, int(value))
        self.data_model.entry.data_len = value
        raw = bytes(self.data_model.entry.data)
        self.data_model.entry.data = raw[:value].ljust(value, b"\x00")

    @property
    def data(self) -> list[int]:
        raw = bytes(self.data_model.entry.data)
        return list(raw[: self.data_len])

    @data.setter
    def data(self, value: list[int]) -> None:
        clipped = [int(v) & 0xFF for v in value]
        self.data_model.entry.data = bytes(clipped)
        self.data_model.entry.data_len = len(clipped)

    @property
    def raw_data(self) -> str:
        return " ".join(f"{int(b) & 0xFF:02X}" for b in self.data)

    @raw_data.setter
    def raw_data(self, value: str) -> None:
        text = str(value).strip()
        if not text:
            self.data = []
            return

        parsed: list[int] = []
        for token in text.split():
            parsed.append(int(token, 16) & 0xFF)
        self.data = parsed

    """ NOTE: column select device"""
    @property
    def device_info_display(self) -> str:
        if self.data_model.device_info is None:
            return ""
        return self.data_model.device_info.device_id
    
    @property
    def status_display(self) -> str:
        if self.is_play:
            return "▶"
        elif self.is_pause:
            return "❚❚"
        elif self.is_disconnet:
            return "✕"
        return ""
    
    @classmethod
    def create_default(
        cls,
        # device_info: CANDeviceInfo,
    ) -> "CANLogPlay":
        entry = LogRecord()

        entry.can_id = 0
        entry.channel = ""
        entry.data = bytes()
        entry.data_len = 0
        entry.direction = 1
        entry.timestamp = 0.0

        return cls(
            is_play=False,
            is_pause=False,
            is_disconnet=False,
            data_model=CANPlayEntry(
                device_info=None,
                entry=entry,
                initial_periodic_second=100.0,
            ),
        )
    
class ScheduleViewModel(QtViewModelBase, SendStatusVM, ScannerVM, DBCModel):
    entriesChanged = Signal()
    stateChanged = Signal()
    dbcChanged = Signal()

    def __init__(self, can_service: CANService, file_service: FileService):
        super().__init__()
        # Initialize mixins after QObject/QtViewModelBase initialization
        self.init_mixins(SendStatusVM, ScannerVM, DBCModel)

        if can_service is None:
            raise TypeError("ScheduleViewModel requires a CANService instance")
        self._can_service = can_service
        self._file_service = file_service
        #file_service.subscribe_any(self.on_status_callback)
        can_service.subscribe(self.on_status_callback)
        #self._acquired_devices: list[CANDeviceInfo] = []

        self._editing_entry: CANLogPlay = CANLogPlay.create_default()
        self._entries: list[CANLogPlay] = [self._editing_entry]
        # self._tree_model = LogEditViewModel_QtAdapter(self)

        self._dbc_id: DBCId | None = None

    @property
    def entries(self) -> list[CANLogPlay]:
        return self._entries

    @property
    def editing_entry(self) -> CANLogPlay:
        return self._editing_entry

    @editing_entry.setter
    def editing_entry(
        self,
        value: CANLogPlay,
    ) -> None:
        if self._editing_entry == value:
            return
        self._editing_entry = value
        self.entriesChanged.emit()
        self.stateChanged.emit()
        
    @property
    def dbc_id(self):
        return self._dbc_id

    @dbc_id.setter
    def dbc_id(self, value):
        if self._dbc_id == value:
            return

        self._dbc_id = value
        self.dbcChanged.emit()

    @property
    def isHavingDevice(self):
        return len(self.acquired_devices) != 0
    
    @Slot(object)
    def sendMsgLoop(self, entry: CANPlayEntry):
        if entry.device_info is None:
            return
        # LOG.debug("sendMsgLoop")
        return self._can_service.send_msg_loop(
        entry.device_info,
        entry.entry,
        entry.initial_periodic_second,
    )
    @Slot(object)
    def sendOnce(self, entry: CANPlayEntry):
        return self._can_service.send_once(
            entry.device_info,
            entry.entry,
        )
        return None

    @Slot(object)
    def pauseMsg(self, entry: CANPlayEntry):
        return self._can_service.pause_msg(
            entry.device_info,
            entry.entry,
        )
        return None

    @Slot(object)
    def resumeMsg(self, entry: CANPlayEntry):
        return self._can_service.resume_msg(
            entry.device_info,
            entry.entry,
        )
        return None

    @Slot(object)
    def removeMsg(self, entry: CANPlayEntry):
        return self._can_service.remove_msg(
            entry.device_info,
            entry.entry,
        )
        return None

    @Slot()
    def clear(self):
        return self._can_service.clear()
        return None

    @Slot("QVariant", "QVariant", float)
    def updatePeriodic(self, entry: CANPlayEntry):
        return self._can_service.update_periodic(device_info, entry, period)
        return Nonei
    
    """BUG: Make sure all the status callbacks of the VM are called so that the event is set."""
    def on_status_callback(self, status):
        #LOG.debug("ScheduleViewModel.on_status_callback")
        # Mixin callbacks already chain with super(); call once to avoid
        # processing the same event multiple times.
        super().on_status_callback(status)

        evt = status

        if isinstance(evt, DBCLoadedEvent):
            self.dbc_id = evt.dbc_id
            return

        if isinstance(evt, SndClear):
            self._entries.clear()
            self.entriesChanged.emit()
            return

        if isinstance(evt, SndDeviceAccquired):
            # NOTE: Handled at ScannerVM
            return

        if isinstance(evt, SndDeviceUnaccquired):
            play = next(
                (
                    play
                    for play in self._entries
                    if play.data_model.device_info == evt.device_info
                ),
                None,
            )

            if play is not None:
                self._entries.remove(play)
                self.entriesChanged.emit()

            return

        if not isinstance(evt, SndCmd):
            return

        play = next(
            (
                play
                for play in self._entries
                if play.data_model.identity == evt.identity
            ),
            None,
        )

        if play is None:
            return

        if isinstance(evt, SndAdd):
            self._entries.append(play)
            # NOTE: Update Tree UI
            # self.entryInserted.emit()

        if isinstance(evt, SndPause):
            play.is_play = False
            play.is_pause = True
            # play.is_disconnect = False

        if isinstance(evt, SndResume):
            play.is_play = True
            play.is_pause = False
            # play.is_disconnect = False

        if isinstance(evt, SndRemove):
            self._entries.remove(play)
            # self.entryRemoved.emit()

        if isinstance(evt, SndUpdatePeriod):
            # TODO: implement
            return

        if isinstance(evt, SndUpdateData):
            # TODO: implement
            return

        self.entriesChanged.emit()

    @property
    def canIDList(self) -> list[MessageItem]:
        if self.dbc_id is None:
            return []
        candb = self._file_service.get_candb_data(self.dbc_id)
        msg_defs = list(candb.messages)

        message_lists:  list[MessageItem] = []
        for msg in msg_defs:
            message_lists.append(
                MessageItem(can_id=msg.frame_id, msg_name=msg.name))