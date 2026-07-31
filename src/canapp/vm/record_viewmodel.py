from __future__ import annotations

from typing import Any
from dataclasses import dataclass, field
from PySide6.QtCore import Signal, Slot, QTimer, QObject

# from .base_view_model import BaseViewModel
from cansrv.test.mock_vm import ScannerVM,ReceiverVM
from cansrv.test.mock_vm import RecordIdEvent, RecorderStatusEvent
from canapp.vm.data_object import CANLogLine
from cansrv.file_service import get_file_service, LogId, MetaDataStorageInterface, CANDBInfo, FileService, MetadataType
# from cansrv.status import RecorderStatus
from lw.logger_setup import setup_logger, LOG
from canapp.vm.data_object import CANLogLine, DecodedSignalLine
from lw.qt.qtobject_adapter import QtViewModelBase
from cansrv.can_srv import CANService
from lw.srv_event import SrvEvent

class RecordViewModel(QtViewModelBase, ScannerVM, ReceiverVM):
    recordingChanged = Signal()
    stateChanged = Signal()
    progressChanged = Signal()

    def __init__(self, file_srv: FileService, can_srv: CANService):
        super().__init__()
        self.init_mixins(ScannerVM, ReceiverVM)

        self.file_srv = file_srv
        self.can_srv = can_srv
        """20260728 BUG: Forget to subscribe => bug not call to callback function """
        #file_srv.subscribe_any(self.on_status_callback)
        can_srv.subscribe(self.on_status_callback)
        self._record_id: LogId | None = None
        #self._is_play: bool = False

        self._row = 0
        self._metadata: MetaDataStorageInterface | None = None
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(lambda: self.progressChanged.emit())
        self._timer.stop()
        self._timer.start()

        """ 20260731 BUG: 
            In C++, QModelIndex stores an opaque pointer (internalPointer). In PySide, when you do:

            self.createIndex(row, column, python_object)

            Shiboken wraps the Python object, but it does not magically keep a strong reference to an object that has no other owners.    

            -> need to store to avoid detroy the object at entry
        """
        self.entries: list[CANLogLine] = []

    @property
    def record_id(self) -> LogId | None:
        return self._record_id

    """ 20260703 NOTE: The python property has no nofification property, it only the derived state until being called
        In QML the @Property has auto re-evaluate
        recordingChanged
            ↓
        isRecording changed
            ↓
        call isRecording getter
            ↓
        Button.enabled = new value
        But QWidget has no binding engine so after call the emit property changed, the UI on widget call update UI again
        Oneway to detect the state changed is using setter property and also other place use it.
    """
    @record_id.setter
    def record_id(self, value: LogId) -> None:
        if self._record_id == value:
            return
        self._record_id = value

        assert value is not None
        """ BUG: sqlite3_exec rc=5 sqlite_msg=database is locked -> fixed by make read only mode"""
        self._metadata = MetaDataStorageInterface(value.path_token(), read_only=True)

        """20260730 BUG: cross-thread QTimer.start()"""
        #self._timer.start()
        
        self.recordingChanged.emit()

    # @property
    # def autoFetch(self):
    #     return self._auto_fetch

    # @autoFetch.setter
    # def autoFetch(self, value):
    #     if self._auto_fetch == value:
    #         return

    #     self._auto_fetch = value
    #     self.recordingChanged.emit()

    """ The only place the state changed """
    def on_status_callback(self, event: SrvEvent):
        super().on_status_callback(event)
        if isinstance(event, RecordIdEvent):
            self.record_id = event.record_id

    @property
    def is_having_record(self) -> bool:
        return self.record_id is not None
    
    @property
    def is_empty_record(self) -> bool:
        return self.record_id is None

    # @Slot()
    # def startNewRecording(self):
    #     return self.file_srv.start_recording()

    # @Slot()
    # def stopRecording(self):
    #     return self.file_srv.stop_recording()

    @Slot(int, result=bool)
    def saveRecord(self, name: str = "") -> bool:
        # get_file_service().save_record(self.record_id)
        #TODO: pass the record id and name to record app store
        return False

    """ NOTE: Qt Tree will auto re-evaluate for it"""
    @property
    def totalRows(self) -> int:
        if self._metadata is None:
            return 0
        #return self._metadata.fetch_count()
        return self._metadata.get_metadata(MetadataType.TOTAL)
    
    @property
    def row(self) -> int:
        return self._row

    @row.setter
    def row(self, value: int) -> None:
        self._row = value

    """
    NOTE: Lazy load version
    """
    @property
    def entry(self) -> CANLogLine | None:
        if self._metadata is None:
            LOG.debug("self._metadata is None")
            return None
        
        view_browser = self._metadata.browse_all()

        if not 0 <= self._row < view_browser.size():
            LOG.debug("not 0 <= self._row < view_browser.size()")
            return None

        row = view_browser.at(
            self._row
        )

        line = CANLogLine(
            data_model=row,
        )

        # db: CANDBInfo | None = None

        # if self.dbc_id is not None:
        #     db = self.file_srv.get_candb_data(
        #         self.dbc_id
        #     )
            
        # if db is not None:
        #     result = db.decode_message(
        #         line.can_id,
        #         line.data,
        #     )
        #     message_def = (
        #         db.get_message_by_frame_id(
        #             line.can_id
        #         )
        #     )

        #     decoded_signals: list[
        #         DecodedSignalLine
        #     ] = []

        #     if (
        #         isinstance(result, dict)
        #         and message_def is not None
        #     ):
        #         for sig_name, sig_value in result.items():
        #             sig_def = None

        #             try:
        #                 sig_def = (
        #                     message_def
        #                     .get_signal_by_name(
        #                         str(sig_name)
        #                     )
        #                 )
        #             except Exception:
        #                 sig_def = None

        #             raw_value = 0

        #             if isinstance(
        #                 sig_value,
        #                 bool,
        #             ):
        #                 raw_value = int(
        #                     sig_value
        #                 )

        #             elif isinstance(
        #                 sig_value,
        #                 (int, float),
        #             ):
        #                 raw_value = int(
        #                     sig_value
        #                 )

        #             elif (
        #                 sig_def is not None
        #                 and getattr(
        #                     sig_def,
        #                     "choices",
        #                     None,
        #                 )
        #             ):
        #                 for (
        #                     choice_raw,
        #                     choice_label,
        #                 ) in sig_def.choices.items():
        #                     if (
        #                         str(choice_label)
        #                         == str(sig_value)
        #                     ):
        #                         raw_value = int(
        #                             choice_raw
        #                         )
        #                         break

        #             sig = DecodedSignalLine(
        #                 raw_value=raw_value,
        #                 changed=bool(
        #                     line.changed
        #                 ),
        #             )

        #             sig._runtime_signal_name = str(
        #                 sig_name
        #             )
        #             sig._sig_info = sig_def

        #             decoded_signals.append(
        #                 sig
        #             )

        #     line.signals = decoded_signals

        """ NOTE: need to store to avoid detroy the object at entry"""
        self.entries.append(line)
        return line
