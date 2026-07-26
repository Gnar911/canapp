from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from PySide6.QtCore import Signal, Slot, QObject
from copy import deepcopy

from cansrv.test.mock_vm import SendStatusVM, ScannerVM, DBCModel
from cansrv.file_service import get_file_service, LogId, MetaDataStorageInterface, DBCId, CANDBInfo
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
from cansrv.module.fs_core import ParsedEntry
from data_object import (
    CANLogLine,
    DecodedSignalLine,
)

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
    entry: ParsedEntry
    initial_periodic: float

    @property
    def identity(self) -> tuple[str, int]:
        device_id = ""
        if self.device_info is not None:
            device_id = self.device_info.device_id
        return (
            device_id,
            int(self.entry.can_id),
        )
    
""" NOTE: Data View"""
@dataclass
class CANLogPlay:
    is_play: bool
    is_pause: bool
    is_disconnet: bool
    data_model: CANPlayEntry
    message_name: str = ""

    @property
    def device_info(self) -> CANDeviceInfo | None:
        return self.data_model.device_info

    @device_info.setter
    def device_info(self, value: CANDeviceInfo | None) -> None:
        self.data_model.device_info = value
    
    @property
    def initial_periodic(self) -> float:
        return float(self.data_model.initial_periodic)

    @initial_periodic.setter
    def initial_periodic(self, value: float) -> None:
        self.data_model.initial_periodic = float(value)

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

    @property
    def changed(self) -> bool:
        return bool(self.data_model.entry.changed)

    @changed.setter
    def changed(self, value: bool) -> None:
        self.data_model.entry.changed = int(bool(value))
    @property
    def last_timestamp(self) -> float:
        return float(self.data_model.entry.last_timestamp)

    @last_timestamp.setter
    def last_timestamp(self, value: float) -> None:
        self.data_model.entry.last_timestamp = float(value)

    @property
    def line_number(self) -> int:
        row_id = getattr(self.data_model.entry, "row_id", None)
        if row_id is not None:
            return int(row_id)
        return int(self.data_model.entry.line_number)

    # @property
    # def show_direction(self) -> str:
    #     return self.direction

    # @property
    # def show_can_id(self) -> str:
    #     return f"{self.can_id:X}"

    # @property
    # def show_data_len(self) -> int:
    #     return self.data_len

    # @property
    # def show_raw_data(self) -> str:
    #     return self.raw_data

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
        entry = ParsedEntry()

        entry.can_id = 0
        entry.channel = ""
        entry.data = bytes()
        entry.data_len = 0
        entry.direction = 1
        entry.timestamp = 0.0
        entry.changed = 0
        entry.last_timestamp = 0.0
        entry.line_number = -1

        return cls(
            is_play=False,
            is_pause=False,
            is_disconnet=False,
            data_model=CANPlayEntry(
                device_info=None,
                entry=entry,
                initial_periodic=100.0,
            ),
        )
    
class ScheduleViewModel(QObject, SendStatusVM, ScannerVM, DBCModel):
    # entriesReset = Signal()
    # entryChanged = Signal(object)
    # entryInserted = Signal(object)
    # entryRemoved = Signal(object)
    # entriesReset = Signal()
    # entriesReset = Signal()
    entriesChanged = Signal()
    stateChanged = Signal()
    dbcChanged = Signal()

    def __init__(self):
        super().__init__()
        self._can_service = CANService()
        self._acquired_devices: list[CANDeviceInfo] = []

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

    def on_dbc_loaded(self, event: DBCLoadedEvent):
        DBCModel.on_dbc_model_loaded(event=event)
        self.dbc_id = event.dbc_id

    def on_scan_status(self, payload: SrvEvent) -> None:
        ScannerVM.on_scan_status(payload)
        if isinstance(payload, ScanDevicePluggedStatus):
            # NOTE: avoid duplicate add when repeated plug notifications arrive
            # if payload.device_info not in self.available_devices:
            #     self.available_devices.append(payload.device_info)
            pass

        if isinstance(payload, ScanDeviceUnpluggedStatus):
            device = payload.device_info

            self._acquired_devices = [
                d for d in self._acquired_devices
                if d.device_id != device.device_id
            ]

            self._acquired_devices.remove(device)
            play = next(
                (
                    play
                    for play in self._entries
                    if play.data_model.device_info
                    == payload.device_info
                ),
                None,
            )
            self._entries.remove(play)
            self.entriesChanged.emit()

        if isinstance(payload, ScanChannelAcquiredStatus):
            device = payload.device_info
            self._acquired_devices.append(device)

        if isinstance(payload, ScanChannelReleasedStatus):
            device = payload.device_info
            self._acquired_devices.remove(device)
            play = next(
                (
                    play
                    for play in self._entries
                    if play.data_model.device_info
                    == payload.device_info
                ),
                None,
            )
            self._entries.remove(play)
            self.entriesChanged.emit()

        self.stateChanged.emit()

    @property
    def isHavingDevice(self):
        return len(self._acquired_devices) != 0
    
    @Slot(object)
    def sendMsgLoop(self, entry: CANPlayEntry) -> None:
        self._can_service.send_msg_loop(
        entry.device_info,
        entry.entry,
        entry.initial_periodic,
    )
    @Slot(object)
    def sendOnce(self, entry: CANPlayEntry) -> None:
        self._can_service.send_once(
            entry.device_info,
            entry.entry,
        )
        return None

    @Slot(object)
    def pauseMsg(self, entry: CANPlayEntry) -> None:
        self._can_service.pause_msg(
            entry.device_info,
            entry.entry,
        )
        return None

    @Slot(object)
    def resumeMsg(self, entry: CANPlayEntry) -> None:
        self._can_service.resume_msg(
            entry.device_info,
            entry.entry,
        )
        return None

    @Slot(object)
    def removeMsg(self, entry: CANPlayEntry) -> None:
        self._can_service.remove_msg(
            entry.device_info,
            entry.entry,
        )
        return None

    @Slot()
    def clear(self) -> None:
        self._can_service.clear()
        return None

    @Slot("QVariant", "QVariant", float)
    def updatePeriodic(self, entry: CANPlayEntry) -> None:
        self._can_service.update_periodic(device_info, entry, period)
        return None

    def on_status_callback(self, status: SrvEvent) -> None:
        SendStatusVM.on_send_status(self, status)
        evt = status

        if isinstance(evt, SndClear):
            self._entries.clear()
            self.entriesChanged.emit()
            return

        if isinstance(evt, SndDeviceAccquired):
            #NOTE: Handled at scanner vm
            return

        if isinstance(evt, SndDeviceUnaccquired):
            play = next(
                (
                    play
                    for play in self._entries
                    if play.data_model.device_info
                    == evt.device_info
                ),
                None,
            )
            self._entries.remove(play)
            self.entriesChanged.emit()
            return

        if not isinstance(evt, SndCmd):
            return
        
        play = next(
            (
                play
                for play in self._entries
                if play.data_model.identity
                == evt.identity
            ),
            None,
        )

        if play is None:
            return
        
        if isinstance(evt, SndAdd):
            self._entries.append(play)

            """ NOTE: Update Tree UI"""
            #self.entryInserted.emit()

        if isinstance(evt, SndPause):
            play.is_play = False
            play.is_pause = True
            # play.is_disconnet = False

        if isinstance(evt, SndResume):
            play.is_play = True
            play.is_pause = False
            #play.is_disconnet = False

        if isinstance(evt, SndRemove):
            self._entries.remove(play)
            #self.entryRemoved.emit()

        if isinstance(evt, SndUpdatePeriod):
            #TODO: implement ?
            return

        if isinstance(evt, SndUpdateData):
            #TODO: implement ?
            return

        self.entriesChanged.emit()

    """ NOTE: DBC re-evaluation"""
    @property
    def canIDList(self) -> list[MessageItem]:
        if self.dbc_id is None:
            return []
        candb = get_file_service().get_candb_data(self.dbc_id)
        msg_defs = list(candb.messages)

        message_lists: list[MessageItem] = []
        for msg in msg_defs:
            message_lists.append(
                MessageItem(can_id=msg.frame_id, msg_name=msg.name)
            )
        return message_lists

