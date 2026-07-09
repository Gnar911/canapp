from __future__ import annotations

from typing import Any

from PySide6.QtCore import Property, Signal, Slot

from .base_view_model import BaseViewModel


class ChannelViewModel(BaseViewModel):
    channelsChanged = Signal()
    lastErrorChanged = Signal()

    def __init__(self, can_service: Any, event_types: dict[str, type] | None = None):
        super().__init__(event_types=event_types)
        self._can_service = can_service
        self._channels: list[dict[str, Any]] = []
        self._last_error = ""

        self._subscribe_event(self._can_service, "ChannelAcquiredEvent", self._on_channel_event)
        self._subscribe_event(self._can_service, "ChannelReleasedEvent", self._on_channel_event)
        self._subscribe_event(self._can_service, "ChannelStateChangedEvent", self._on_channel_event)

        self.refresh()

    @Property("QVariantList", notify=channelsChanged)
    def channels(self) -> list[dict[str, Any]]:
        return self._channels

    @Property(str, notify=lastErrorChanged)
    def lastError(self) -> str:
        return self._last_error

    @Slot(result="QVariantList")
    def refresh(self) -> list[dict[str, Any]]:
        snapshot = self._can_service.get_channels_snapshot()
        channels: list[dict[str, Any]] = []
        for handle, info in snapshot.items():
            data = self._normalize_info(info)
            data["handle"] = int(handle)
            channels.append(data)
        channels.sort(key=lambda x: x.get("handle", 0))
        self._set_if_changed(self, "_channels", channels, self.channelsChanged)
        return channels

    @Slot(int, result=bool)
    def acquire(self, handle: int) -> bool:
        ok = bool(self._can_service.acquire(handle))
        if not ok:
            self._set_if_changed(self, "_last_error", f"Failed to acquire channel: {handle}", self.lastErrorChanged)
        self.refresh()
        return ok

    @Slot(int)
    def release(self, handle: int) -> None:
        self._can_service.release(handle)
        self.refresh()

    def _on_channel_event(self, _: Any) -> None:
        self.refresh()

    @staticmethod
    def _normalize_info(info: Any) -> dict[str, Any]:
        if isinstance(info, dict):
            return dict(info)

        result: dict[str, Any] = {}
        for name in ("channel_id", "state", "bitrate", "fd", "name", "serial"):
            if hasattr(info, name):
                value = getattr(info, name)
                result[name] = value.name if hasattr(value, "name") else value
        return result
