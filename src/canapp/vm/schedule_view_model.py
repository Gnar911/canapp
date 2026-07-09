from __future__ import annotations

from typing import Any

from PySide6.QtCore import Property, Signal, Slot

from .base_view_model import BaseViewModel


class ScheduleViewModel(BaseViewModel):
    sendStatusChanged = Signal()
    lastErrorChanged = Signal()

    def __init__(self, can_service: Any, event_types: dict[str, type] | None = None):
        super().__init__(event_types=event_types)
        self._can_service = can_service
        self._send_status: dict[str, Any] = {}
        self._last_error = ""

        self._subscribe_event(self._can_service, "SendStatusEvent", self._on_send_status)
        self._subscribe_event(self._can_service, "ScheduleFailedEvent", self._on_schedule_failed)

    @Property("QVariantMap", notify=sendStatusChanged)
    def sendStatus(self) -> dict[str, Any]:
        return self._send_status

    @Property(str, notify=lastErrorChanged)
    def lastError(self) -> str:
        return self._last_error

    @Slot("QVariant", float, float, result=bool)
    def sendMsgLoop(self, entry: Any, initial_periodic: float, timeout_s: float = 0.0) -> bool:
        return bool(self._can_service.send_msg_loop(entry, initial_periodic, timeout_s=timeout_s))

    @Slot("QVariant", result=bool)
    def sendOnce(self, entry: Any) -> bool:
        return bool(self._can_service.send_once(entry))

    @Slot(int, int, result=bool)
    def pauseMsg(self, channel_id: int, can_id: int) -> bool:
        return bool(self._can_service.pause_msg(channel_id, can_id))

    @Slot(result=bool)
    def pauseAll(self) -> bool:
        return bool(self._can_service.pause_all())

    @Slot(int, int, result=bool)
    def resumeMsg(self, channel_id: int, can_id: int) -> bool:
        return bool(self._can_service.resume_msg(channel_id, can_id))

    @Slot(result=bool)
    def resumeAll(self) -> bool:
        return bool(self._can_service.resume_all())

    @Slot(int, int, result=bool)
    def removeMsg(self, channel_id: int, can_id: int) -> bool:
        return bool(self._can_service.remove_msg(channel_id, can_id))

    @Slot(result=bool)
    def clear(self) -> bool:
        return bool(self._can_service.clear())

    @Slot(int, int, float, result=bool)
    def updatePeriodic(self, channel_id: int, can_id: int, period: float) -> bool:
        return bool(self._can_service.update_periodic(channel_id, can_id, period))

    @Slot(result="QVariantMap")
    def refreshSendStatus(self) -> dict[str, Any]:
        status = dict(self._can_service.get_send_status(refresh=True, timeout_s=1.0))
        self._set_if_changed(self, "_send_status", status, self.sendStatusChanged)
        return status

    def _on_send_status(self, event: Any) -> None:
        status = getattr(event, "status", None)
        if isinstance(status, dict):
            self._set_if_changed(self, "_send_status", status, self.sendStatusChanged)

    def _on_schedule_failed(self, event: Any) -> None:
        message = str(getattr(event, "message", "Schedule operation failed"))
        self._set_if_changed(self, "_last_error", message, self.lastErrorChanged)
