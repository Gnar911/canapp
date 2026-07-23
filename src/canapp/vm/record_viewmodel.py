from __future__ import annotations

from typing import Any
from dataclasses import dataclass, field
from PySide6.QtCore import Signal, Slot, QTimer, QObject

# from .base_view_model import BaseViewModel
from cs_test.mock_vm import ScannerVM
from fs_test.mock_vm import RecordModel, RecorderStatusEvent
from canapp.data_object import CANLogLine
from cansrv.file_service import get_file_service, LogId, MetaDataStorageInterface, CANDBInfo
from cansrv.status import RecorderStatus
from lw.logger_setup import setup_logger, LOG
from data_object import CANLogLine, DecodedSignalLine

class RecordViewModel(QObject, RecordModel, ScannerVM):
    recordingChanged = Signal()
    progressChanged = Signal()

    def __init__(self):
        super().__init__()

        #self.record_state: RecorderStatus = RecorderStatus.STOPPED
        self._record_id: LogId | None = None
        self._is_play: bool = False

        self._metadata: MetaDataStorageInterface | None = None
        self._timer = QTimer(self)
        self._timer.setInterval(100)
        self._timer.timeout.connect(lambda: self.progressChanged.emit())
        self._timer.stop()

        #self._viewport = (0, 100)
        self._auto_fetch: bool = False

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
    def record_id(self, value: LogId | None) -> None:
        if self._record_id == value:
            return
        self._record_id = value
        self.recordingChanged.emit()

    @property
    def is_play(self) -> bool:
        return self._is_play

    @is_play.setter
    def is_play(self, value: bool) -> None:
        if self._is_play == value:
            return
        self._is_play = value
        self.recordingChanged.emit()

    @property
    def autoFetch(self):
        return self._auto_fetch

    @autoFetch.setter
    def autoFetch(self, value):
        if self._auto_fetch == value:
            return

        self._auto_fetch = value
        self.recordingChanged.emit()

    # @property
    # def viewport(self):
    #     return self._viewport

    # @viewport.setter
    # def viewport(self, value):
    #     if self._viewport == value:
    #         return

    #     self._viewport = value
    #     self.recordingChanged.emit()

    """ The only place the state changed """
    def on_recorder_status(self, event: RecorderStatusEvent):
        RecordModel.on_recorder_status(event)
        status = RecorderStatus(int(event.status))
        is_play = False
        record_id = event.log_id
        if status == RecorderStatus.STOPPED:
            assert record_id is None
            is_play = False
            self._timer.stop()
        elif status == RecorderStatus.STARTED:
            # NOTE: Event status changed
            assert record_id is not None
            self.metadata = MetaDataStorageInterface(record_id.path_token())
            self._timer.start()
            is_play = True
        self.is_play = is_play
        self.record_id = event.log_id

    @property
    def isRecording(self) -> bool:
        return self.is_play

    @property
    def isStop(self) -> bool:
        return not self.is_play

    @property
    def is_having_record(self) -> bool:
        return self.record_id is not None
    
    @property
    def is_empty_record(self) -> bool:
        return self.record_id is None

    @property
    def totalFrames(self) -> int:
        if self.metadata is None:
            return 0
        return self.metadata.fetch_count()
    
    @property
    def entries(self) -> list[CANLogLine]:
        # NOTE: No record loaded yet
        if self.record_id is None:
            return []

        first, count = self.viewport

        if self.autoFetch:
            first = max(self.totalFrames - count, 0)

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
            self.record_id,
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

            # pending = self._editing_line.get(int(line.line_number))
            lines.append(line)
            

        return lines

    @Slot()
    def startNewRecording(self) -> None:
        get_file_service().start_recording()

    @Slot()
    def stopRecording(self) -> None:
        get_file_service().stop_recording()

    @Slot(int, result=bool)
    def saveRecord(self, name: str = "") -> bool:
        # get_file_service().save_record(self.record_id)
        #TODO: pass the record id and name to record app store
        return False
