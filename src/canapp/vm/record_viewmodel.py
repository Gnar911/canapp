from __future__ import annotations

from typing import Any
from dataclasses import dataclass, field
from PySide6.QtCore import Property, Signal, Slot

from .base_view_model import BaseViewModel
from fs_test.mock_vm import RecordModel
from file_service.srv_if import get_file_service, LogId
from file_service.status import RecorderStatus
from lw.logger_setup import setup_logger, LOG
from data_object import CANLogLine

# class RecordingState:
#     pass

# """ Dataclass only equals when all fields are equal"""
# @dataclass
# class OnRecording(RecordingState):
#     record_id: LogId

# @dataclass
# class OnPaused(RecordingState):
#     record_id: LogId

# class OnStopped(RecordingState):
#     pass

class RecordViewModel(BaseViewModel, RecordModel):
    recordingChanged = Signal()

    def __init__(self):
        super().__init__()

        self.record_state: RecorderStatus = RecorderStatus.STOPPED
        self._record_id: LogId | None = None
        get_file_service().subscribe(RecorderStatus, self.on_recorder_status)

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

    """ The only place the state changed """
    def on_recorder_status(self, event: RecorderStatus) -> None:
        RecordModel.on_recorder_status(event)
        status = event
        if self.record_state == status:
            return
        self.record_state = status
        # if status == RecorderStatus.STOPPED:
        #     self.record_state = OnStopped()
        # elif status == RecorderStatus.PAUSED:
        #     self.record_state = OnPaused()

        self.recordingChanged.emit()


    @property
    def isRecording(self) -> bool:
        return isinstance(self.record_state, RecorderStatus.WAIT_RING or RecorderStatus.WRITE_BATCH)
    
    @property
    def totalFrames(self) -> int:
        return get_file_service().get_logfile_metadata(self.record_id).entry_count

    @property
    def isStop(self) -> bool:
        return isinstance(self.record_state, RecorderStatus.STOPPED)

    @property
    def is_having_record(self) -> bool:
        return self.record_id is not None
    
    @property
    def is_empty_record(self) -> bool:
        return self.record_id is None

    @property
    def fetchLogLines(self, first:int, count: int) -> list[CANLogLine]: 
        entries = get_file_service().read_page(self.record_id, first, first + count)

        #TODO: Construct the CANLogLine here
        for entry in entries:
            lines = CANLogLine(
                        channel=entry.channel,
                        can_id=int(entry.can_id),
                        direction=entry.direction,
                        data_len=int(entry.data_len),
                        raw_data=entry.raw_data,
                        changed=bool(entry.changed),
                        line_number=int(entry.line_number),
                        timestamp=float(entry.timestamp),
                        last_timestamp=float(entry.last_timestamp)
                    )

    @Slot()
    def startNewRecording(self) -> None:
        """ NOTE: True means:
        "I successfully accepted your request.", your request has been queued
        It does not mean recording has started.
        If there is something wrong with the system error other than the business error -> raise the exception other than return bool
        because the that is not what the app could handle with.
        """
        self.record_id = get_file_service().start_recording()

    @Slot()
    def stopRecording(self) -> None:
        get_file_service().stop_recording()

    @Slot(int, result=bool)
    def saveRecord(self, name: str = "") -> bool:
        get_file_service().save_record(self.record_id)
        #TODO: pass the record id and name to record app store
