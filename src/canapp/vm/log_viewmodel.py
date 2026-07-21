from __future__ import annotations

from typing import List, Any
from PySide6.QtCore import Signal, Slot, QTimer, QObject
from dataclasses import dataclass, replace
from copy import deepcopy

# from .base_view_model import BaseViewModel

""" NOTE BUG 20260720 Cost 1h to fix:
    cansrv package is installed as a PEP 660 editable install that uses a dynamic import finder, not a static path. 
    import __editable___cansrv_0_1_0_finder; __editable___cansrv_0_1_0_finder.install()
    Python interpreter: executes that .pth → runs the finder → cansrv resolves. ✅ (that's why every terminal import works)
Pylance/Pyright: does static analysis. It never executes .pth code — it only reads .pth files that contain literal directory paths. 
So it has literally no idea where cansrv lives → "could not be resolved." ❌
-> Pyright + setuptools-strict-editable incompatibility.

1. Reinstalled cansrv in compat editable mode → pip now writes a plain static .pth (.../cansrv/src) that Pylance reads:
-> python3 -m pip install -e . --config-settings editable_mode=compat 2>&1 | tail -n 20

2. Made cansrv.test a real subpackage via symlink so runtime and Pylance agree:
-> ln -s ../../test project/cansrv/src/cansrv/test

3. Simplified the extraPaths in canapp/.vscode/settings.json and project/.vscode/settings.json to just cansrv/src (safety net).

-> workk immediately with reload VSCode

cansrv was installed with setuptools' strict editable mode, which writes a .pth that is actually executable code running a dynamic import finder:
import __editable___cansrv_0_1_0_finder; __editable___cansrv_0_1_0_finder.install()
"""
from cansrv.test.mock_vm import *
# from file_service.application_events import ParserStatusEvent, DBCLoadedEvent
# from file_service.status import ParserStatus
# from file_service.file_service import get_file_service, LogId, MetaDataStorageInterface, DBCId, CANDBInfo
from cansrv.application_events import ParserStatusEvent, DBCLoadedEvent
from cansrv.status import ParserStatus
from cansrv.file_service import get_file_service, LogId, MetaDataStorageInterface, DBCId, CANDBInfo, ViewBrowser, LogQuery
# from file_service.module.fs_core import LogRecord
from canapp.data_object import CANLogLine, DecodedSignalLine
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

""" NOTE: this is the setter/getter for use internally as state changed, not expose to View
There is usually no public setter for read-only state.
in C#, WPF (.NET)
public Metadata Metadata
{
    get => __metadata;
    private set
    {
        __metadata = value;
        OnPropertyChanged();
    }
}
The View can read Metadata.
Only the ViewModel can write it because the setter is private.
    
C++
class VM {
public:
    const Metadata& _metadata() const;

private:
    void setMetadata(Metadata m);
};
Q_PROPERTY(Metadata _metadata
        READ _metadata
        NOTIFY _metadataChanged)
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

    def empty(self) -> bool:
        return self == FilterState()

    def to_query(self) -> LogQuery:
        query = LogQuery()

        if self.message is not None:
            query.can_ids = self.message.can_ids
            query.changed_only = self.message.changed

        if self.channel is not None:
            query.channels = self.channel.channels

        if self.direction is not None:
            query.directions = [
                0 if self.direction.direction == "Rx" else 1
            ]

        if self.time is not None:
            query.first_ts = self.time.first_ts
            query.last_ts = self.time.last_ts
            query.has_time_range = True

        return query

class LogViewModel(QObject, ParseModel, DBCModel):
    progressChanged = Signal()

    """ BUG: This is the common state changed, we update the trivial operation all at the same signal but this not good for
            high performance operation such as load entries.
    """
    commonStateChanged = Signal()

    browseChanged = Signal()

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
        #self._state: ParserStatus | None = None
        """ 20262107 BUG"""
        self._srv_feedback = False
        self._log_id: LogId | None = None
        self._dbc_id: DBCId | None = None

        self._metadata: MetaDataStorageInterface | None = None
        #self._view_browser: ViewBrowser | None = None
        self._lazy_count = 0
        self._row = 0
        self._timer = QTimer(self)
        self._timer.setInterval(100)
        self._timer.timeout.connect(lambda: self.progressChanged.emit())
        self._timer.stop()

        """ View -> Model state View data type, could do 2 ways binding"""
        self._page_size = 10000 
        # Internal page index is zero-based; start on the first page.
        self._page_num = 0
        self._filter: FilterState = FilterState()
        self._editing_line: dict[RowId, CANLogLine] = {}
        #self._viewport = (0, 100)
        self._auto_fetch: bool = False   
        self._editable_mode: bool = False

    """ NOTE: Qt Tree will auto re-evaluate for it"""
    @property
    def lazyCount(self) -> int:
        return self._lazy_count

    @lazyCount.setter
    def lazyCount(self, value: int) -> None:
        self._lazyCount = value

    @property
    def row(self) -> int:
        return self._row

    @row.setter
    def row(self, value: int) -> None:
        self._row = value

    @property
    def pageNum(self):
        return self._page_num

    @pageNum.setter
    def pageNum(self, value):
        if self._page_num == value:
            return

        self._page_num = value
        self.commonStateChanged.emit()
        self.browseChanged.emit()

    @property
    def editingLine(self):
        return self._editing_line

    @editingLine.setter
    def editingLine(self, value):
        if self._editing_line == value:
            return

        self._editing_line = value
        self.commonStateChanged.emit()

    # @property
    # def autoFetch(self) -> bool:
    #     return self._auto_fetch

    # @autoFetch.setter
    # def autoFetch(self, value: bool) -> None:
    #     if self._auto_fetch == value:
    #         return
    #     # Cannot enable auto-fetch while editing.
    #     self._auto_fetch = value and not self._editable_mode
    #     self.commonStateChanged.emit()
        
    @property
    def editableMode(self) -> bool:
        return self._editable_mode

    @editableMode.setter
    def editableMode(self, value: bool) -> None:
        if self._editable_mode == value:
            return
        # Entering editable mode forces auto-fetch off.
        if value:
            self._auto_fetch = False

        self._editable_mode = value
        self.commonStateChanged.emit()

    @property
    def pageSize(self):
        return self._page_size

    """ THis settet are equal to a function callback that result in commonStateChanged"""
    @pageSize.setter
    def pageSize(self, value):
        if self._page_size == value:
            return

        self._page_size = value
        self._page_num = 0
        self.commonStateChanged.emit()
        self.browseChanged.emit()

    """ NOTE: log_id would not be a two-way bound property """
    @property
    def log_id(self):
        return self._log_id

    @log_id.setter
    def log_id(self, value):

        """ 20262107 BUG: if 2 callback has the same log_id -> it not re-evaluate -> log_id only can only describe 2 state, start(done) and fail
                while the state and done should also have been distinguigh
        """
        if self._log_id == value and not self._srv_feedback:
            return

        self._log_id = value
        self.commonStateChanged.emit()
        self.browseChanged.emit()

    @property
    def dbc_id(self):
        return self._dbc_id

    @dbc_id.setter
    def dbc_id(self, value):
        if self._dbc_id == value:
            return

        self._dbc_id = value
        self.commonStateChanged.emit()
        self.browseChanged.emit()

    """ Transition state change to done or failed, calback funcion for all the viewmodels"""
    def on_parser_status(self, event: ParserStatusEvent):
        ParseModel.on_parser_status(self, event)
        status = ParserStatus(int(event.status))
        log_id = event.log_id

        """ BUG: """
        if status == ParserStatus.STARTED:
            if log_id is not None:
                self._metadata = MetaDataStorageInterface(log_id.path_token())
                #self._view_browser = get_file_service().browse_all(log_id)
                self._lazy_count = 0
                self._srv_feedback = False
                self._timer.start()
            else:
                raise ValueError
        elif status == ParserStatus.FAILED:
            # if log_id is None:
            assert log_id is None
            self._srv_feedback = True
            self._timer.stop()
            ### NOTE: close storage
            self._metadata = None
            self._lazy_count = 0
        elif status == ParserStatus.DONE:
            assert log_id is not None
            self._srv_feedback = True
            self._timer.stop()
    
        self.log_id = log_id

    def on_dbc_loaded(self, event: DBCLoadedEvent):
        DBCModel.on_dbc_model_loaded(event=event)
        self.dbc_id = event.dbc_id
            
    """ Transition state change to running or idle"""
    # @Slot(str)
    # def startParsing(self, path: str):
    #     log_id = get_file_service().parse_log_file(path)
    #     if log_id is None:
    #         self._timer.stop()
    #         ### NOTE: close storage
    #         self._metadata = None
    #     else:
    #         self._metadata = MetaDataStorageInterface(log_id.path_token())
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
        if self._metadata is None:
            return (-1.0, -1.0)
        ts = self._metadata.get_first_last_timestamp()
        if ts is None:
            return (-1.0, -1.0)
        first_timestamp, last_timestamp = ts
        return (
            first_timestamp,
            last_timestamp,
        )

    @property
    def defaultLogName(self) -> str:
        if self._metadata is None:
            return ""
        #TODO
        return "ABCDXYZ"

    @property
    def totalPages(self) -> int:
        return (self.totalLines + self._page_size - 1) // self._page_size
    
    @property
    def progressBarIsActive(self) -> bool:
        return self.log_id is not None

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
    #         self.commonStateChanged.emit()
    
    @property
    def messageFilter(self):
        return self._filter.message

    @messageFilter.setter
    def messageFilter(self, value: MsgFilter):
        self._filter = replace(
            self._filter,
            message=value,
        )
        self._lazy_count = 0

        """ NOTE: This is for re-evaluate all the visible rows with new ViewBrowser instance """
        self.commonStateChanged.emit()
        self.browseChanged.emit()

    @property
    def directionFilter(self):
        return self._filter.direction


    @directionFilter.setter
    def directionFilter(self, value: DirectionFilter):
        self._filter = replace(
            self._filter,
            direction=value,
        )
        self._lazy_count = 0

        """ NOTE: This is for re-evaluate all the visible rows with new ViewBrowser instance """
        self.commonStateChanged.emit()
        self.browseChanged.emit()
        
    """
    NOTE: Lazy load version
    """
    @property
    def entry(self) -> CANLogLine | None:
        if self._metadata is None:
            return None
        
        if self._filter.empty():
            view_browser = self._metadata.browse_all()
        else:
            view_browser = self._metadata.browse(self._filter.to_query())

        if not 0 <= self._row < view_browser.size():
            return None

        row = view_browser.at(
            self._row
        )

        line = CANLogLine(
            channel=str(row.channel),
            can_id=int(row.can_id),
            direction=str(row.direction),
            data_len=row.data_len,
            data=row.data,
            changed=bool(row.changed),
            line_number=int(row.line_number),
            timestamp=float(row.timestamp),
            last_timestamp=float(
                row.last_timestamp
            ),
        )

        db: CANDBInfo | None = None

        if self.dbc_id is not None:
            db = get_file_service().get_candb_data(
                self.dbc_id
            )
            
        if db is not None:
            result = db.decode_message(
                line.can_id,
                line.data,
            )
            message_def = (
                db.get_message_by_frame_id(
                    line.can_id
                )
            )

            decoded_signals: list[
                DecodedSignalLine
            ] = []

            if (
                isinstance(result, dict)
                and message_def is not None
            ):
                for sig_name, sig_value in result.items():
                    sig_def = None

                    try:
                        sig_def = (
                            message_def
                            .get_signal_by_name(
                                str(sig_name)
                            )
                        )
                    except Exception:
                        sig_def = None

                    raw_value = 0

                    if isinstance(
                        sig_value,
                        bool,
                    ):
                        raw_value = int(
                            sig_value
                        )

                    elif isinstance(
                        sig_value,
                        (int, float),
                    ):
                        raw_value = int(
                            sig_value
                        )

                    elif (
                        sig_def is not None
                        and getattr(
                            sig_def,
                            "choices",
                            None,
                        )
                    ):
                        for (
                            choice_raw,
                            choice_label,
                        ) in sig_def.choices.items():
                            if (
                                str(choice_label)
                                == str(sig_value)
                            ):
                                raw_value = int(
                                    choice_raw
                                )
                                break

                    sig = DecodedSignalLine(
                        raw_value=raw_value,
                        changed=bool(
                            line.changed
                        ),
                    )

                    sig._runtime_signal_name = str(
                        sig_name
                    )
                    sig._sig_info = sig_def

                    decoded_signals.append(
                        sig
                    )

            line.signals = decoded_signals


    """ NOTE: Page load version"""
    @property
    def entries(self) -> list[CANLogLine]:
        if self._metadata is None:
            return None
        
        if self._filter.empty():
            view_browser = self._metadata.browse_all()
        else:
            view_browser = self._metadata.browse(self._filter.to_query())

        db: CANDBInfo | None = None

        if self.dbc_id is not None:
            db = get_file_service().get_candb_data(
                self.dbc_id
            )

        lines: list[CANLogLine] = []

        start = self.pageNum * self.pageSize
        end = min(
            (self.pageNum + 1) * self.pageSize,
            view_browser.size(),
        )

        LOG.debug(
            "entries window page=%s size=%s browser_size=%s start=%s end=%s",
            self.pageNum,
            self.pageSize,
            view_browser.size(),
            start,
            end,
        )

        for i in range(start, end):
            row = view_browser.at(i)

            line = CANLogLine(
                channel=str(row.channel),
                can_id=int(row.can_id),
                direction=str(row.direction),
                data_len=row.data_len,
                data=row.data,
                changed=bool(row.changed),
                line_number=int(row.line_number),
                timestamp=float(row.timestamp),
                last_timestamp=float(
                    row.last_timestamp
                ),
            )

            if db is not None:
                try:
                    result = db.decode_message(
                        line.can_id,
                        line.data,
                    )
                    message_def = (
                        db.get_message_by_frame_id(
                            line.can_id
                        )
                    )

                    decoded_signals: list[
                        DecodedSignalLine
                    ] = []

                    if (
                        isinstance(result, dict)
                        and message_def is not None
                    ):
                        for sig_name, sig_value in result.items():
                            sig_def = None

                            try:
                                sig_def = (
                                    message_def
                                    .get_signal_by_name(
                                        str(sig_name)
                                    )
                                )
                            except Exception:
                                sig_def = None

                            raw_value = 0

                            if isinstance(
                                sig_value,
                                bool,
                            ):
                                raw_value = int(
                                    sig_value
                                )

                            elif isinstance(
                                sig_value,
                                (int, float),
                            ):
                                raw_value = int(
                                    sig_value
                                )

                            elif (
                                sig_def is not None
                                and getattr(
                                    sig_def,
                                    "choices",
                                    None,
                                )
                            ):
                                for (
                                    choice_raw,
                                    choice_label,
                                ) in sig_def.choices.items():
                                    if (
                                        str(choice_label)
                                        == str(sig_value)
                                    ):
                                        raw_value = int(
                                            choice_raw
                                        )
                                        break

                            sig = DecodedSignalLine(
                                raw_value=raw_value,
                                changed=bool(
                                    line.changed
                                ),
                            )

                            sig._runtime_signal_name = str(
                                sig_name
                            )
                            sig._sig_info = sig_def

                            decoded_signals.append(
                                sig
                            )

                    line.signals = decoded_signals

                except Exception as e:
                    LOG.exception(
                        "Decode failed: %s",
                        e,
                    )

            pending = self.editingLine.get(
                int(line.line_number)
            )

            lines.append(
                deepcopy(pending)
                if pending is not None
                else line
            )

            # LOG.debug("Row num: %s", row.line_number)

        return lines

    """ NOTE: This is not good view data for rows because it did not cover the filter state count"""
    @property
    def totalLines(self) -> int:
        if self._metadata is None:
            return 0
        
        if self._filter.empty():
            view_browser = self._metadata.browse_all()
        else:
            view_browser = self._metadata.browse(self._filter.to_query())

        return view_browser.size()