from __future__ import annotations

from typing import Any, Optional

from PySide6.QtCore import Property, Signal, Slot, QObject, Qt
from PySide6.QtGui import QStandardItemModel, QStandardItem
from cs_test.mock_vm import *
from cansrv.can_srv import CANService
from cansrv.can_srv import get_can_service
from cansrv.file_service import LogId
from fs_test.mock_vm import ParseModel, DBCModel
from cansrv.application_events import ParserStatusEvent, DBCLoadedEvent
from cansrv.status import ParserStatus
from cansrv.file_service import get_file_service, LogId, MetaDataStorageInterface, DBCId, MetadataType
from typing import TypeAlias
from cansrv.can_srv import CANDeviceInfo
from lw.srv_event import SrvEvent
from dataclasses import replace

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
    """ NOTE This field is for cache"""
    file_name: str


@dataclass(frozen=True, slots=True)
class Playing:
    """
    A source is actively being replayed.
    """
    source: LogId
    file_name: str


@dataclass(frozen=True, slots=True)
class Paused:
    """
    Replay is paused, but the source remains active.
    """
    source: LogId

ReplayState: TypeAlias = Empty | Ready | Playing | Paused

""" NOTE: Make it immutable"""
@dataclass(frozen=True, slots=True)
class ReplayConfig:
    mode: LoopForever | Repeat = Repeat(1)
    ignored_msg_ids: frozenset[int] = frozenset()
    time_scope: TimeScope | None = None

""" 20260723 NOTE: UI Data ViewModel
    The reason for the frozen True is that this UI is state-driven, can not modify directly on UI 
"""
class CheckItem(QStandardItem):
    def __init__(
        self,
        value: int,
        is_checked: bool,
        msg_name: str = "",
    ):
        super().__init__()

        self.value = value
        self.msg_name = msg_name

        # DisplayRole
        self.setText(self.content)

        # CheckStateRole
        self.setCheckable(True)
        self.setCheckState(
            Qt.Checked
            if is_checked
            else Qt.Unchecked
        )

        # UserRole: underlying application data
        self.setData(
            value,
            Qt.UserRole,
        )

    @property
    def _msg_name(self) -> str:
        return (
            f" - {self.msg_name}"
            if self.msg_name
            else ""
        )

    @property
    def content(self) -> str:
        return f"0x{self.value:X}{self._msg_name}"

    @property
    def isChecked(self) -> bool:
        return self.checkState() == Qt.Checked

""" NOTE: 
    Qt has QStringListModel:

    model = QStringListModel([
        "CAN 0x100",
        "CAN 0x200",
        "CAN 0x300",
    ])


"""

class ReplayViewModel(QObject, ReplayStatusVM, ScannerVM, ParseModel, SendStatusVM, DBCModel):
    replayStateChanged = Signal()
    progressChanged = Signal()
    dbcChanged = Signal()

    def __init__(self):
        super().__init__()
        self._can_service = get_can_service()
        self._dbc_id: DBCId | None = None
        self._state: ReplayState = Empty()
        self._config = ReplayConfig()
        self._current_cycle = 0
        self._metadata: MetaDataStorageInterface | None = None
        #self._is_active = True
        #current_index: int
        #current_cycle: int
        #total_rows: int

        # self._available_devices: list[CANDeviceInfo] = []
        self._acquired_devices: list[CANDeviceInfo] = []
        self._accquired_device: CANDeviceInfo | None = None

        #self._in_log_message_list: list[CheckItem] = []
        #self._msg_list_model = QStandardItemModel(self)


    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, value):
        if self._state == value:
            return
                                                             
        self._state = value
        self.replayStateChanged.emit()

    """20260723 NOTE
    self.config = replace(...)
            │
            ▼
    creates NEW ReplayConfig
            │
            ▼
    calls @config.setter
            │
            ├── old == new → return, no signal
            │
            └── old != new
                    ↓
            self._config = value
                    ↓
            replayStateChanged.emit()
    """
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

    # def on_parser_status(self, event: ParserStatusEvent):
    #     ParseModel.on_parser_status(self, event)
    #     status = ParserStatus(int(event.status))
    #     if status != ParserStatus.DONE:
    #         source = event.log_id
    #         assert source is not None
    #         """ NOTE: User load the file into the log view panel, auto set it to the replay service"""
            # self._can_service.set_source(source)

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
            #NOTE: Open storage to get metadata
            self._metadata = MetaDataStorageInterface(evt.source.path_token())
            self.state = Ready(source=evt.source)
            return

        if isinstance(evt, RplFinished):
            assert isinstance(self.state, (Playing))
            self.state = Ready(source=self.state.source)
            pass

        if isinstance(evt, RplCycleFinished):
            self.current_cycle = int(evt.cycle_th)
            return

        if evt == ReplayCmdType.START or evt == ReplayCmdType.RESUME:
            """ NOTE State Transitioning """
            assert isinstance(self.state, (Ready, Paused))
            self.state = Playing(source=self.state.source)
            return

        if evt == ReplayInterruptCmdType.PAUSE:
            assert isinstance(self.state, Playing)
            self.state = Paused(source=self.state.source)
            return

        if evt == ReplayInterruptCmdType.STOP:
            assert isinstance(self.state, (Playing, Paused, Ready))
            self.state = Ready(source=self.state.source)
            self.current_cycle = 0

            return

        if evt == ReplayInterruptCmdType.UNSET_SOURCE:
            self._current_cycle = 0
            self._metadata = None
            self.state = Empty()
            return

        if isinstance(evt, ReplaySetLoop):
            self.config = replace(
                self.config,
                mode=LoopForever() if evt.enabled else Repeat(count=1),
            )
            return

        if isinstance(evt, ReplaySetRepeat):
            self.config = replace(
                self.config,
                mode=Repeat(count=max(1, evt.count)),
            )
            return

        if isinstance(evt, ReplaySetFilterMsg):
            self.config = replace(
                self.config,
                ignored_msg_ids=self.config.ignored_msg_ids | {evt.msg_id},
            )
            return

        if isinstance(evt, ReplaySetTimescope):
            time_scope = (
                TimeScope(
                    start_ts=float(evt.start_ts),
                    end_ts=float(evt.end_ts),
                )
                if evt.start_ts is not None
                and evt.end_ts is not None
                else None
            )

            self.config = replace(
                self.config,
                time_scope=time_scope,
            )
            return
        
    def on_scan_status(self, payload: SrvEvent) -> None:
        ScannerVM.on_scan_status(payload)
        if isinstance(payload, ScanDevicePluggedStatus):
            # NOTE: avoid duplicate add when repeated plug notifications arrive
            # if payload.device_info not in self.available_devices:
            #     self.available_devices.append(payload.device_info)
            pass

        if isinstance(payload, ScanDeviceUnpluggedStatus):
            device = payload.device_info

            # self.available_devices = [
            #     d for d in self.available_devices
            #     if d.device_id != device.device_id
            # ]

            self._acquired_devices = [
                d for d in self._acquired_devices
                if d.device_id != device.device_id
            ]

        if isinstance(payload, ScanChannelAcquiredStatus):
            device = payload.device_info
            #self.available_devices.remove(device)
            self._acquired_devices.append(device)

        if isinstance(payload, ScanChannelReleasedStatus):
            device = payload.device_info
            self._acquired_devices.remove(device)
            #self.available_devices.append(device)

        """ NOTE: Do not have the Reactor for list data object -> manual emit state change """
        self.replayStateChanged.emit()
                
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
    def resumeReplay(self):
        self._can_service.resume_replay()

    @Slot(bool)
    def setLoop(self, enabled: bool):
        self._can_service.set_loop(enabled)

    @Slot(int)
    def setRepeat(self, count: int):
        self._can_service.set_repeat(count)

    @Slot("QVariantList")
    def setMsgIdFilter(self, id: int):
        # ids = [int(v) for v in msg_ids]
        self._can_service.set_msg_id_filter(id)

    @Slot()
    def clearMsgIdFilter(self):
        self._can_service.set_msg_id_filter(None)

    @Slot(float, float)
    def setTimeScope(self, start_ts: float, end_ts: float):
        self._can_service.set_time_scope(start_ts, end_ts)

    @Slot()
    def clearTimeScope(self):
        self._can_service.set_time_scope(None, None)

    @property(bool, notify=replayStateChanged)
    def isHavingDevice(self):
        return len(self._acquired_devices) != 0

    @property(bool, notify=replayStateChanged)
    def isReplay(self):
        return isinstance(self.state, Playing)

    @property(bool, notify=replayStateChanged)
    def isStop(self) -> bool:
        return isinstance(self.state, (Empty, Ready))

    @property(bool, notify=replayStateChanged)
    def isPause(self) -> bool:
        return isinstance(self.state, Paused)

    @property(bool, notify=replayStateChanged)
    def isHavingRecord(self) -> bool:
        return self.record_id is not None
    
    @property(bool, notify=replayStateChanged)
    def isEmptyRecord(self) -> bool:
        return self.record_id is None

    @property
    def hasMsgFilter(self) -> bool:
        return len(self.config.ignored_msg_ids) > 0

    @property
    def timeRange(self) -> tuple[float, float]:
        scope = self.config.time_scope
        if scope is None:
            return [0.0, 0.0]
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

    @property
    def targetLog(self) -> str:
        if self._metadata is None:
            return "Null"
        return "ABCDXYZ"

    """ NOTE: Should not use the property for the Qt UI because we do not
            know the evaluation cost if it.
    """
    @property
    def inLogMessageLists(self) -> list[CheckItem]:
        if self._metadata is None:
            return []

        msg_ids = self._metadata.get_metadata(
            MetadataType.CAN_IDS
        )

        candb = (
            get_file_service().get_candb_data(self.dbc_id)
            if self.dbc_id is not None
            else None
        )

        def get_msg_name(msg_id: int) -> str:
            if candb is None:
                return ""

            try:
                return candb.get_message_by_frame_id(msg_id).name
            except KeyError:
                return ""

        return [
            CheckItem(
                value=msg_id,
                isChecked=msg_id in self.config.ignored_msg_ids,
                msg_name=get_msg_name(msg_id),
            )
            for msg_id in msg_ids
        ]
    
