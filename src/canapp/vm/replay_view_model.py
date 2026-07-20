from __future__ import annotations

from typing import Any, Optional

from PySide6.QtCore import Property, Signal, Slot, QObject
from cs_test.mock_vm import *
from cansrv.can_srv import CANService
from cansrv.file_service import LogId
from fs_test.mock_vm import ParseModel, DBCModel
from cansrv.application_events import ParserStatusEvent, DBCLoadedEvent
from cansrv.status import ParserStatus
from cansrv.file_service import get_file_service, LogId, MetaDataStorageInterface, DBCId
from typing import TypeAlias
from cansrv.can_srv import CANDeviceInfo
from lw.srv_event import SrvEvent

""" NOTE: State machine define region"""
@dataclass(frozen=True)
class LoopForever:
    pass

@dataclass(frozen=True)
class Repeat:
    count: int

@dataclass(frozen=True)
class TimeScope:
    start_ts: float
    end_ts: float

@dataclass(frozen=True, slots=True)
class Empty:
    """
    No replay source has been selected.
    """
    pass

@dataclass(frozen=True, slots=True)
class Ready:
    """
    A source exists and is ready to play.
    """
    source: LogId


@dataclass(frozen=True, slots=True)
class Playing:
    """
    A source is actively being replayed.
    """
    source: LogId


@dataclass(frozen=True, slots=True)
class Paused:
    """
    Replay is paused, but the source remains active.
    """
    source: LogId

ReplayState: TypeAlias = Empty | Ready | Playing | Paused
    
@dataclass(slots=True)
class ReplayConfig:
    mode: LoopForever | Repeat
    ignored_msg_ids: tuple[int, ...] = ()
    time_scope: TimeScope | None = None


class ReplayViewModel(QObject, ReplayStatusVM, ScannerVM, ParseModel, SendStatusVM, DBCModel):
    replayStateChanged = Signal()
    progressChanged = Signal()
    dbcChanged = Signal()

    def __init__(self):
        super().__init__()
        self._can_service = CANService()
        # self._source: Optional[LogId]
        # self._mode: LoopForever | Repeat
        # self.is_play:  bool = False
        # self.is_pause: bool = False
        # self.ignored_msg_ids: tuple[int, ...]
        # self.time_scope: Optional[TimeScope] # is at timesope state or not

        self._dbc_id: DBCId | None = None
        self._state: ReplayState = Empty()
        self._config = ReplayConfig(
            mode=LoopForever(),
        )
        self._current_cycle = 0
        self._is_active = True
        #current_index: int
        #current_cycle: int
        #total_rows: int

        self._available_devices: list[CANDeviceInfo] = []
        self._acquired_devices: list[CANDeviceInfo] = []

    """ State Machine"""
    @property
    def available_devices(self):
        return self._available_devices
    @property
    def acquired_devices(self):
        return self._acquired_devices
    
    @acquired_devices.setter
    def acquired_devices(self, value):
        if self._acquired_devices == value:
            return

        self._acquired_devices = value
        self.deviceStateChanged.emit()

    @available_devices.setter
    def available_devices(self, value):
        if self._available_devices == value:
            return

        self._available_devices = value
        self.deviceStateChanged.emit()

    @property
    def is_active(self):
        return self._is_active

    @is_active.setter
    def is_active(self, value):
        if self._is_active == value:
            return
                                                             
        self._is_active = value
        self.replayStateChanged.emit()

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, value):
        if self._state == value:
            return
                                                             
        self._state = value
        self.replayStateChanged.emit()

    @property
    def config(self):
        return self._config

    @config.setter
    def config(self, value):
        if self._config == value:
            return
                                                             
        self._config = value
        self.replayStateChanged.emit()

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
    def current_cycle(self):
        return self._current_cycle

    @current_cycle.setter
    def current_cycle(self, value):
        if self._current_cycle == value:
            return

        self._current_cycle = value
        self.dbcChanged.emit()


    def on_dbc_loaded(self, event: DBCLoadedEvent):
        DBCModel.on_dbc_model_loaded(event=event)
        """ NOTE: re-evaluate only the DBC name on the filter table"""
        self.dbc_id = event.dbc_id

    def on_parser_status(self, event: ParserStatusEvent):
        ParseModel.on_parser_status(self, event)
        status = ParserStatus(int(event.status))
        if status != ParserStatus.DONE:
            source = event.log_id
            assert source is not None
            """ NOTE: User load the file into the log view panel, auto set it to the replay service"""
            self._can_service.set_source(source)

    def on_send_status(self, event: SrvEvent) -> None:
        SendStatusVM.on_send_status(event)
        evt = event
        if isinstance(evt, SndClear):
            self.is_active = False

        if isinstance(evt, SndAdd):
            self.is_active = True
        
    def on_replay_status(self, event: SrvEvent) -> None:
        ReplayStatusVM.on_replay_status(self, event)
        evt = event

        if isinstance(evt, ReplaySetSource):
            self.current_cycle = 0
            self.state = Ready(source=evt.source)
            return

        if isinstance(evt, RplFinished):
            if isinstance(self.state, (Playing, Paused)):
                self.state = Ready(source=self.state.source)
            return

        if isinstance(evt, RplCycleFinished):
            self.current_cycle = int(evt.cycle_th)
            return

        if evt == ReplayCmdType.START or evt == ReplayCmdType.RESUME:
            if isinstance(self.state, (Ready, Paused)):
                self.state = Playing(source=self.state.source)
            return

        if evt == ReplayInterruptCmdType.PAUSE:
            if isinstance(self.state, Playing):
                self.state = Paused(source=self.state.source)
            return

        if evt == ReplayInterruptCmdType.STOP:
            if isinstance(self.state, (Playing, Paused)):
                self.state = Ready(source=self.state.source)
            self.current_cycle = 0

            return

        if evt == ReplayInterruptCmdType.UNSET_SOURCE:
            self._current_cycle = 0
            self.state = Empty()
            return

        if isinstance(evt, ReplaySetLoop):
            self.config = ReplayConfig(
                mode=LoopForever() if bool(evt.enabled) else Repeat(count=1),
                ignored_msg_ids=self.config.ignored_msg_ids,
                time_scope=self.config.time_scope,
            )
            return

        if isinstance(evt, ReplaySetRepeat):
            self.config = ReplayConfig(
                mode=Repeat(count=max(1, int(evt.count))),
                ignored_msg_ids=self.config.ignored_msg_ids,
                time_scope=self.config.time_scope,
            )
            return

        if isinstance(evt, ReplaySetFilterMsg):
            self.config = ReplayConfig(
                mode=self.config.mode,
                ignored_msg_ids=tuple(int(v) for v in evt.msg_ids),
                time_scope=self.config.time_scope,
            )
            return

        if isinstance(evt, ReplaySetTimescope):
            time_scope: TimeScope | None
            if evt.start_ts is None or evt.end_ts is None:
                time_scope = None
            else:
                time_scope = TimeScope(
                    start_ts=float(evt.start_ts),
                    end_ts=float(evt.end_ts),
                )
            self.config = ReplayConfig(
                mode=self.config.mode,
                ignored_msg_ids=self.config.ignored_msg_ids,
                time_scope=time_scope,
            )
            return
        
    def on_scan_status(self, payload: SrvEvent) -> None:
        ScannerVM.on_scan_status(payload)
        if isinstance(payload, ScanDevicePluggedStatus):
            # NOTE: avoid duplicate add when repeated plug notifications arrive
            if payload.device_info not in self.available_devices:
                self.available_devices.append(payload.device_info)
            return

        if isinstance(payload, ScanDeviceUnpluggedStatus):
            device = payload.device_info

            self.available_devices = [
                d for d in self.available_devices
                if d.device_id != device.device_id
            ]

            self.acquired_devices = [
                d for d in self.acquired_devices
                if d.device_id != device.device_id
            ]
            return

        if isinstance(payload, ScanChannelAcquiredStatus):
            device = payload.device_info
            self.available_devices.remove(device)
            self.acquired_devices.append(device)
            return

        if isinstance(payload, ScanChannelReleasedStatus):
            device = payload.device_info
            self.acquired_devices.remove(device)
            self.available_devices.append(device)
            return
                
    """ NOTE: There is no button to set source on the replay screen -> this API View should not existed"""
    # def setSource(self, record_id: LogId) -> bool:
    #     self._can_service.set_source(record_id)

    """ NOTE: Button start replay"""
    @Slot()
    def startReplay(self) -> None:
        self._can_service.start_replay()
        return None

    """ NOTE: Button stop replay"""
    @Slot()
    def stopReplay(self) -> None:
        self._can_service.stop_replay()
        return None

    """ NOTE: Button pause replay"""
    @Slot()
    def pauseReplay(self) -> None:
        self._can_service.pause_replay()
        return None

    @Slot()
    def resumeReplay(self) -> None:
        self._can_service.resume_replay()
        return None

    @Slot(bool)
    def setLoop(self, enabled: bool) -> None:
        self._can_service.set_loop(enabled)
        return None

    @Slot(int)
    def setRepeat(self, count: int) -> None:
        self._can_service.set_repeat(count)
        return None

    @Slot("QVariantList")
    def setMsgIdFilter(self, msg_ids: list[int]) -> None:
        ids = [int(v) for v in msg_ids]
        self._can_service.set_msg_id_filter(ids)
        return None

    @Slot()
    def clearMsgIdFilter(self) -> None:
        self._can_service.set_msg_id_filter(None)
        return None

    @Slot(float, float)
    def setTimeScope(self, start_ts: float, end_ts: float) -> None:
        self._can_service.set_time_scope(start_ts, end_ts)
        return None

    @Slot()
    def clearTimeScope(self) -> None:
        self._can_service.set_time_scope(None, None)
        return None

    @property
    def isReplay(self) -> bool:
        return isinstance(self.state, Playing)

    @property
    def isStop(self) -> bool:
        return isinstance(self.state, (Empty, Ready))

    @property
    def isPause(self) -> bool:
        return isinstance(self.state, Paused)

    @property
    def isHavingRecord(self) -> bool:
        return self.record_id is not None
    
    @property
    def isActive(self) -> bool:
        return self.is_active
    
    @property
    def isEmptyRecord(self) -> bool:
        return self.record_id is None

    @property
    def msgFilterList(self) -> list[int]:
        # UI list-box view of ignored message IDs
        return list(self.config.ignored_msg_ids)

    @property
    def hasMsgFilter(self) -> bool:
        return len(self.config.ignored_msg_ids) > 0

    @property
    def timeScopeRange(self) -> tuple[float, float] | None:
        scope = self.config.time_scope
        if scope is None:
            return None
        return (float(scope.start_ts), float(scope.end_ts))

    @property
    def hasTimeScope(self) -> bool:
        return self.config.time_scope is not None

    @property
    def isLoopOn(self) -> bool:
        return isinstance(self.config.mode, LoopForever)

    @property
    def setCycle(self) -> int:
        mode = self.config.mode
        if isinstance(mode, Repeat):
            return max(1, int(mode.count))
        # loop-forever has no fixed upper cycle count
        return 0

    @property
    def currentCycle(self) -> int:
        return int(self.current_cycle)

    @property
    def totalFrames(self) -> int:
        if self.metadata is None:
            return 0
        return self.metadata.fetch_count()

