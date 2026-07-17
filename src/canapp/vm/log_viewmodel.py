from __future__ import annotations

from typing import List, Any
from PySide6.QtCore import Signal, Slot, QTimer
from dataclasses import dataclass, replace
from copy import deepcopy

from .base_view_model import BaseViewModel
from fs_test.mock_vm import ParseModel
from cs_test.mock_vm import *
from file_service.application_events import ParserStatusEvent, DBCLoadedEvent
from file_service.status import ParserStatus
from file_service.file_service import get_file_service, LogId, MetaDataStorageInterface, DBCId, CANDBInfo, CA
# from file_service.module.fs_core import LogRecord
from canapp.data_object import CANLogLine, DecodedSignalLine
from can_service.srv_status import ResponseACK, NotificationEvent
from typing import Literal
from lw.logger_setup import LOG

RowId = int

""" NOTE This class responsibility is to facing the service worker for 1 call parse log, this also have no
        responsibile for checking duplicate or block 2 parse log call service """

""" NOTE
    The browse/import action uses the LogViewModel to initialize a new parsing session.

    vm = LogViewModel()
    vm.startParsing(file_path)

    The Log View tab also uses the same LogViewModel for the remainder of the session.

    LogView(vm)

    
    20260704
    QML itself does not enforce valid states.

    Suppose your ViewModel exposes:

    @property
    def is_loading(self): ...

    @property
    def progress(self): ...

    @property
    def error_message(self): ...

    Then QML binds:

    ProgressBar {
        visible: vm.isLoading
        value: vm.progress
    }

    Label {
        visible: vm.errorMessage !== ""
        text: vm.errorMessage
    }

    Nothing stops the ViewModel from producing:
    isLoading = true
    progress = 100
    errorMessage = "Failed"    

    A more common way:
    Expose a single enum plus properties
    This is very common in Qt.
    For example:

    class ParserStatus(Enum):
        IDLE
        RUNNING
        DONE
        FAILED

    and

    @property
    def status(self): ...

    @property
    def progress(self): ...

    Then QML does:

    ProgressBar {
        visible: vm.status === ParserStatus.RUNNING
        value: vm.progress
    }

    Notice:

    progress exists all the time.
    The View only uses it when status == RUNNING.

    However,...
    the ViewModel must maintain the invariant.

    For example:

    status == RUNNING
        ⇒ log_id != None

    status == FAILED
        ⇒ error != None

    status == IDLE
        ⇒ log_id == None
"""

@dataclass(frozen=True)
class NoFilter:
    pass

@dataclass(frozen=True)
class MsgFilter:
    can_ids: List[int]
    changed: bool = False
    
@dataclass(frozen=True)
class SigFilter:
    signals: List[Any]
    changed: bool = False

@dataclass(frozen=True)
class DirectionFilter:
    direction: Literal["Rx", "Tx"]

@dataclass(frozen=True)
class ChannelFilter:
    channels: List[str]


@dataclass(frozen=True)
class TimeFilter:
    first_ts: float
    last_ts: float


@dataclass(frozen=True)
class FilterState:
    direction: DirectionFilter | None = None
    message: MsgFilter | None = None
    signal: SigFilter | None = None
    channel: ChannelFilter | None = None
    time: TimeFilter | None = None

class LogViewModel(BaseViewModel, ParseModel):
    progressChanged = Signal()
    stateChanged = Signal()

    def __init__(self):

        super().__init__()

        """ Model -> View state (service data type)
        NOTE: 
            (None, IDLE)
                |
        startParsing()
                |
        (LogId, IDLE)
            /      \
        DONE          FAILED

        Inital staet is idle, timer off
        """
        self._state: ParserStatus | None = None
        self._log_id: LogId | None = None
        self._dbc_id: DBCId | None = None

        self._metadata: MetaDataStorageInterface | None = None
        self._timer = QTimer(self)
        self._timer.setInterval(100)
        self._timer.timeout.connect(lambda: self.stateChanged.emit())
        self._timer.stop()

        """ View -> Model state View data type, could do 2 ways binding"""
        self._page_size = 10000 
        self._filter: FilterState = FilterState()
        self._editing_line: dict[RowId, CANLogLine] = {}
        self._viewport = (0, 100)
        self._auto_fetch: bool = False
    @property
    def editing_line(self):
        return self._editing_line

    @editing_line.setter
    def editing_line(self, value):
        if self._editing_line == value:
            return

        self._editing_line = value
        self.stateChanged.emit()

    @property
    def autoFetch(self):
        return self._auto_fetch

    @autoFetch.setter
    def autoFetch(self, value):
        if self._auto_fetch == value:
            return

        self._auto_fetch = value
        self.stateChanged.emit()

    @property
    def viewport(self):
        return self._viewport

    @viewport.setter
    def viewport(self, value):
        if self._viewport == value:
            return

        self._viewport = value
        self.stateChanged.emit()

    """ NOTE: View no need to care about construct full state so the ViewModel
        will expose individual properties and use replace
    """
    # @property
    # def filter(self):
    #     return self._filter

    # @filter.setter
    # def filter(self, value):
    #     if self._filter == value:
    #         return

    #     self._filter = value
    #     self.stateChanged.emit()

    @property
    def messageFilter(self):
        return self._filter.message

    @messageFilter.setter
    def messageFilter(self, value):
        self._filter = replace(
            self._filter,
            message=value,
        )
        self.stateChanged.emit()

    @property
    def directionFilter(self):
        return self._filter.direction

    @directionFilter.setter
    def directionFilter(self, value):
        self._filter = replace(
            self._filter,
            direction=value,
        )
        self.stateChanged.emit()

    @property
    def pageSize(self):
        return self._page_size

    """ THis settet are equal to a function callback that result in stateChanged"""
    @pageSize.setter
    def pageSize(self, value):
        if self._page_size == value:
            return

        self._page_size = value
        self.stateChanged.emit()

    """ NOTE: this is the setter/getter for use internally as state changed, not expose to View
    There is usually no public setter for read-only state.
    in C#, WPF (.NET)
    public Metadata Metadata
    {
        get => _metadata;
        private set
        {
            _metadata = value;
            OnPropertyChanged();
        }
    }
    The View can read Metadata.
    Only the ViewModel can write it because the setter is private.
        
    C++
    class VM {
    public:
        const Metadata& metadata() const;

    private:
        void setMetadata(Metadata m);
    };
    Q_PROPERTY(Metadata metadata
           READ metadata
           NOTIFY metadataChanged)
    """
    @property
    def metadata(self):
        return self._metadata

    @metadata.setter
    def metadata(self, value):
        if self._metadata == value:
            return

        self._metadata = value
        self.stateChanged.emit()

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, value):
        if self._state == value:
            return

        self._state = value
        self.stateChanged.emit()

    """ NOTE: log_id would not be a two-way bound property """
    @property
    def log_id(self):
        return self._log_id

    @log_id.setter
    def log_id(self, value):
        if self._log_id == value:
            return

        self._log_id = value
        self.stateChanged.emit()

    @property
    def dbc_id(self):
        return self._dbc_id

    @dbc_id.setter
    def dbc_id(self, value):
        if self._dbc_id == value:
            return

        self._dbc_id = value
        self.stateChanged.emit()

    """ Transition state change to done or failed, calback funcion for all the viewmodels"""
    def on_parser_status(self, event: ParserStatusEvent):
        ParseModel.on_parser_status(self, event)
        status = ParserStatus(int(event.status))
        log_id = event.log_id
        if status == ParserStatus.STARTED:
            if log_id is not None:
                self.metadata = MetaDataStorageInterface(log_id.path_token())
                self._timer.start()
            else:
                raise ValueError
        elif status == ParserStatus.FAILED:
            # if log_id is None:
            assert log_id is None
            self._timer.stop()
            ### NOTE: close storage
            self.metadata = None
        elif status == ParserStatus.DONE:
            assert log_id is not None
            self._timer.stop()
    
        self.log_id = log_id
        #self.state = status

    def on_dbc_loaded(self, event: DBCLoadedEvent):
        #self._dbc_info = event.candb_info
        self.dbc_id = event.dbc_id
            
    """ Transition state change to running or idle"""
    # @Slot(str)
    # def startParsing(self, path: str):
    #     log_id = get_file_service().parse_log_file(path)
    #     if log_id is None:
    #         self._timer.stop()
    #         ### NOTE: close storage
    #         self.metadata = None
    #     else:
    #         self.metadata = MetaDataStorageInterface(log_id.path_token())
    #         self._timer.start()
        
    #     """ NOTE Notify state change here"""
    #     self.log_id = log_id

    @Slot(str)
    def startParsing(self, path: str):
        get_file_service().parse_log_file(path)

    def closeLog(self):
        self.log_id = None

    @property
    def logTimestampRange(self) -> tuple[float, float]:
        if self.metadata is None:
            return (-1.0, -1.0)
        ts = self.metadata.get_first_last_timestamp()
        if ts is None:
            return (-1.0, -1.0)
        first_timestamp, last_timestamp = ts
        return (
            first_timestamp,
            last_timestamp,
        )

    @property
    def defaultLogName(self) -> str:
        if self.metadata is None:
            return ""
        #TODO
        return "ABCDXYZ"

    @property
    def totalPages(self) -> int:
        return (self.totalLines + self._page_size - 1) // self._page_size
    
    @property
    def progressBarIsActive(self) -> bool:
        return self.log_id is not None

    @property
    def totalLines(self) -> int:
        if self.metadata is None:
            return 0
        return self.metadata.fetch_count()

    # def save_edit(self) -> None:
    #     if not self.log_id:
    #         return
        
    #     if not self._editing_line:
    #         return
        
    #     entry_updates: list[EntryUpdate] = []
    #     for v in list(self._editing_line.values()):
    #         # v is a CANLogLine; map to EntryUpdate(line_number + LogRecord payload)
    #         r = LogRecord()
    #         r.channel = str(v.channel)
    #         r.can_id = int(v.can_id)

    #         d = v.direction.strip().lower()
    #         if d == "rx":
    #             r.direction = 0
    #         elif d == "tx":
    #             r.direction = 1

    #         r.data = list(v.data) if v.data is not None else []
    #         r.data_len = int(v.data_len)
    #         r.timestamp = float(v.timestamp)

    #         u = EntryUpdate()
    #         # convert 1-based line_number -> 0-based row_index expected by storage
    #         u.row_index = max(int(v.line_number) - 1, 0)
    #         u.record = r

    #         entry_updates.append(u)

    #     if get_file_service().save_log_edits(self.log_id, entry_updates):
    #         self._editing_line.clear()
    #         self.stateChanged.emit()
    
    @property
    def entries(self) -> list[CANLogLine]:
        if self.log_id is None:
            return []

        first, count = self.viewport

        if self.autoFetch:
            first = max(self.totalLines - count, 0)

        f = self._filter
        service = get_file_service()

        can_ids = None
        changed_only = False
        channels = None
        directions = None
        time_range = None

        if f.message is not None:
            can_ids = list(f.message.can_ids)
            changed_only = f.message.changed

        if f.channel is not None:
            channels = list(f.channel.channels)

        if f.direction is not None:
            directions = [f.direction.direction]

        if f.time is not None:
            time_range = (f.time.first_ts, f.time.last_ts)

        rows = service.read_page_filtered(
            self.log_id,
            first,
            first + count,
            can_ids=can_ids,
            channels=channels,
            directions=directions,
            changed_only=changed_only,
            time_range=time_range,
        )

        db: CANDBInfo | None = None
        # if not unload the DBC or load fail
        if self.dbc_id is not None:
            db = get_file_service().get_candb_data(self.dbc_id)

        lines: list[CANLogLine] = []
        for row in rows:
            LOG.debug("Row num: %s", row.line_number)
            line = CANLogLine(
                channel=str(row.channel),
                can_id=int(row.can_id),
                direction=str(row.direction),
                data_len=row.data_len,
                data=row.data,
                changed=bool(row.changed),
                line_number=int(row.line_number),
                timestamp=float(row.timestamp),
                last_timestamp=float(row.last_timestamp),
            )

            # Build decoded signals only when DBC is loaded.
            if db is not None:
                try:
                    result = db.decode_message(line.can_id, line.data)
                    message_def = db.get_message_by_frame_id(line.can_id)
                    LOG.debug("Decoded: %s", result)
                    LOG.debug("Message def: %s", message_def)

                    decoded_signals: list[DecodedSignalLine] = []
                    if isinstance(result, dict) and message_def is not None:
                        for sig_name, sig_value in result.items():
                            sig_def = None
                            try:
                                sig_def = message_def.get_signal_by_name(str(sig_name))
                            except Exception:
                                sig_def = None

                            LOG.debug("Sig def: %s", sig_def)

                            raw_value = 0
                            if isinstance(sig_value, bool):
                                raw_value = int(sig_value)
                            elif isinstance(sig_value, (int, float)):
                                raw_value = int(sig_value)
                            elif sig_def is not None and getattr(sig_def, "choices", None):
                                matched = False
                                for choice_raw, choice_label in sig_def.choices.items():
                                    if str(choice_label) == str(sig_value):
                                        raw_value = int(choice_raw)
                                        matched = True
                                        break
                                if not matched:
                                    raw_value = 0

                            sig = DecodedSignalLine(
                                raw_value=raw_value,
                                changed=bool(line.changed),
                            )
                            sig._runtime_signal_name = str(sig_name)
                            sig._sig_info = sig_def
                            decoded_signals.append(sig)

                    line.signals = decoded_signals
                except Exception as e:
                    LOG.exception("Decode failed: %s", e)

            pending = self._editing_line.get(int(line.line_number))
            lines.append(deepcopy(pending) if pending is not None else line)
            

        return lines