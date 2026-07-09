from __future__ import annotations

from typing import Any

from PySide6.QtCore import Property, Signal, Slot

from .base_view_model import BaseViewModel

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

class ReplayState(Enum):
    NONE = auto() # deterministic default when replay source is unavailable
    IDLE_WAIT = auto() # state after finish or not start
    PLAYING = auto() # state after resume
    PAUSED = auto() # state after pause

@dataclass(slots=True, frozen=True)
class ReplayWorkerState(DomainEvent):
    source: Optional[Record]
    mode: LoopForever | Repeat
    registered_channels: tuple[int, ...] # register/unregister channel state
    replay_state: ReplayState
    current_index: int
    current_cycle: int
    total_rows: int
    ignored_msg_ids: tuple[int, ...]
    time_scope: Optional[TimeScope] # is at timesope state or not
    last_cmd: ReplayCmdEvent
    
class ReplayViewModel(BaseViewModel):
    replayStateChanged = Signal()
    progressChanged = Signal()
    currentRecordIdChanged = Signal()
    loopEnabledChanged = Signal()
    repeatCountChanged = Signal()
    filterMsgIdsChanged = Signal()
    timeScopeChanged = Signal()
    lastStatusChanged = Signal()
    lastErrorChanged = Signal()

    def __init__(self, can_service: Any, event_types: dict[str, type] | None = None):
        super().__init__(event_types=event_types)
        self._can_service = can_service

        self._replay_state = "Stopped"
        self._progress = 0.0
        self._current_record_id = -1
        self._loop_enabled = False
        self._repeat_count = 1
        self._filter_msg_ids: list[int] = []
        self._time_scope = {"startTs": None, "endTs": None}
        self._last_status: dict[str, Any] = {}
        self._last_error = ""

        self._subscribe_event(self._can_service, "ReplayStartedEvent", self._on_started)
        self._subscribe_event(self._can_service, "ReplayStoppedEvent", self._on_stopped)
        self._subscribe_event(self._can_service, "ReplayPausedEvent", self._on_paused)
        self._subscribe_event(self._can_service, "ReplayResumedEvent", self._on_resumed)
        self._subscribe_event(self._can_service, "ReplayProgressEvent", self._on_progress)
        self._subscribe_event(self._can_service, "ReplayStatusEvent", self._on_status)
        self._subscribe_event(self._can_service, "ReplayFailedEvent", self._on_failed)

    @Property(str, notify=replayStateChanged)
    def replayState(self) -> str:
        return self._replay_state

    @Property(float, notify=progressChanged)
    def progress(self) -> float:
        return self._progress

    @Property(int, notify=currentRecordIdChanged)
    def currentRecordId(self) -> int:
        return self._current_record_id

    @Property(bool, notify=loopEnabledChanged)
    def loopEnabled(self) -> bool:
        return self._loop_enabled

    @Property(int, notify=repeatCountChanged)
    def repeatCount(self) -> int:
        return self._repeat_count

    @Property("QVariantList", notify=filterMsgIdsChanged)
    def filterMsgIds(self) -> list[int]:
        return self._filter_msg_ids

    @Property("QVariantMap", notify=timeScopeChanged)
    def timeScope(self) -> dict[str, float | None]:
        return self._time_scope

    @Property("QVariantMap", notify=lastStatusChanged)
    def lastStatus(self) -> dict[str, Any]:
        return self._last_status

    @Property(str, notify=lastErrorChanged)
    def lastError(self) -> str:
        return self._last_error

    @Slot(int, result=bool)
    def startReplay(self, record_id: int) -> bool:
        ok = bool(self._can_service.start_replay(record_id))
        if ok:
            self._set_if_changed(self, "_current_record_id", record_id, self.currentRecordIdChanged)
            self._set_if_changed(self, "_replay_state", "Running", self.replayStateChanged)
            self._set_if_changed(self, "_last_error", "", self.lastErrorChanged)
        else:
            self._set_if_changed(self, "_last_error", f"Failed to start replay: {record_id}", self.lastErrorChanged)
        return ok

    @Slot(result=bool)
    def stopReplay(self) -> bool:
        ok = bool(self._can_service.stop_replay())
        if ok:
            self._set_if_changed(self, "_replay_state", "Stopped", self.replayStateChanged)
            self._set_if_changed(self, "_progress", 0.0, self.progressChanged)
        return ok

    @Slot(result=bool)
    def pauseReplay(self) -> bool:
        ok = bool(self._can_service.pause_replay())
        if ok:
            self._set_if_changed(self, "_replay_state", "Paused", self.replayStateChanged)
        return ok

    @Slot(result=bool)
    def resumeReplay(self) -> bool:
        ok = bool(self._can_service.resume_replay())
        if ok:
            self._set_if_changed(self, "_replay_state", "Running", self.replayStateChanged)
        return ok

    @Slot(bool, result=bool)
    def setLoop(self, enabled: bool) -> bool:
        ok = bool(self._can_service.set_loop(enabled))
        if ok:
            self._set_if_changed(self, "_loop_enabled", enabled, self.loopEnabledChanged)
        return ok

    @Slot(int, result=bool)
    def setRepeat(self, count: int) -> bool:
        ok = bool(self._can_service.set_repeat(count))
        if ok:
            self._set_if_changed(self, "_repeat_count", count, self.repeatCountChanged)
        return ok

    @Slot("QVariantList", result=bool)
    def setMsgIdFilter(self, msg_ids: list[int]) -> bool:
        ids = [int(v) for v in msg_ids]
        ok = bool(self._can_service.set_msg_id_filter(ids))
        if ok:
            self._set_if_changed(self, "_filter_msg_ids", ids, self.filterMsgIdsChanged)
        return ok

    @Slot(result=bool)
    def clearMsgIdFilter(self) -> bool:
        ok = bool(self._can_service.set_msg_id_filter(None))
        if ok:
            self._set_if_changed(self, "_filter_msg_ids", [], self.filterMsgIdsChanged)
        return ok

    @Slot(float, float, result=bool)
    def setTimeScope(self, start_ts: float, end_ts: float) -> bool:
        ok = bool(self._can_service.set_time_scope(start_ts, end_ts))
        if ok:
            scope = {"startTs": start_ts, "endTs": end_ts}
            self._set_if_changed(self, "_time_scope", scope, self.timeScopeChanged)
        return ok

    @Slot(result=bool)
    def clearTimeScope(self) -> bool:
        ok = bool(self._can_service.set_time_scope(None, None))
        if ok:
            self._set_if_changed(self, "_time_scope", {"startTs": None, "endTs": None}, self.timeScopeChanged)
        return ok

    @Slot(result="QVariantMap")
    def refreshStatus(self) -> dict[str, Any]:
        status = dict(self._can_service.get_replay_status(refresh=True, timeout_s=1.0))
        self._apply_status(status)
        return status

    def _apply_status(self, status: dict[str, Any]) -> None:
        self._set_if_changed(self, "_last_status", status, self.lastStatusChanged)

        progress = float(status.get("progress", self._progress))
        self._set_if_changed(self, "_progress", progress, self.progressChanged)

        state = status.get("state")
        if state is not None:
            self._set_if_changed(self, "_replay_state", str(state), self.replayStateChanged)

    def _on_started(self, event: Any) -> None:
        record_id = getattr(event, "record_id", getattr(event, "id", self._current_record_id))
        self._set_if_changed(self, "_current_record_id", int(record_id), self.currentRecordIdChanged)
        self._set_if_changed(self, "_replay_state", "Running", self.replayStateChanged)

    def _on_stopped(self, _: Any) -> None:
        self._set_if_changed(self, "_replay_state", "Stopped", self.replayStateChanged)
        self._set_if_changed(self, "_progress", 0.0, self.progressChanged)

    def _on_paused(self, _: Any) -> None:
        self._set_if_changed(self, "_replay_state", "Paused", self.replayStateChanged)

    def _on_resumed(self, _: Any) -> None:
        self._set_if_changed(self, "_replay_state", "Running", self.replayStateChanged)

    def _on_progress(self, event: Any) -> None:
        progress = float(getattr(event, "progress", 0.0))
        self._set_if_changed(self, "_progress", progress, self.progressChanged)

    def _on_status(self, event: Any) -> None:
        status = getattr(event, "status", None)
        if isinstance(status, dict):
            self._apply_status(status)

    def _on_failed(self, event: Any) -> None:
        message = str(getattr(event, "message", "Replay operation failed"))
        self._set_if_changed(self, "_last_error", message, self.lastErrorChanged)
