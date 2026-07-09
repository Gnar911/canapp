from __future__ import annotations

from typing import Any

from PySide6.QtCore import Property, QObject

from .channel_view_model import ChannelViewModel
from .dbc_view_model import DbcViewModel
# from .device_view_model import DeviceViewModel
from .gateway_view_model import GatewayViewModel
from .record_viewmodel import RecordViewModel
from .replay_view_model import ReplayViewModel
from .schedule_view_model import ScheduleViewModel


class MainWindowViewModel(QObject):
    """Root composition for all VM modules used by the QML main window."""

    def __init__(
        self,
        can_service: Any,
        file_service: Any,
        event_types: dict[str, type] | None = None,
    ):
        super().__init__()
        self._dbc = DbcViewModel(file_service=file_service, event_types=event_types)
        self._recording = RecordViewModel(file_service=file_service, event_types=event_types)
        self._replay = ReplayViewModel(can_service=can_service, event_types=event_types)
        self._channel = ChannelViewModel(can_service=can_service, event_types=event_types)
        self._schedule = ScheduleViewModel(can_service=can_service, event_types=event_types)
        self._gateway = GatewayViewModel(can_service=can_service, event_types=event_types)
        #self._device = DeviceViewModel(can_service=can_service, event_types=event_types)

    @Property(QObject, constant=True)
    def dbc(self) -> QObject:
        return self._dbc

    @Property(QObject, constant=True)
    def recording(self) -> QObject:
        return self._recording

    @Property(QObject, constant=True)
    def replay(self) -> QObject:
        return self._replay

    @Property(QObject, constant=True)
    def channel(self) -> QObject:
        return self._channel

    @Property(QObject, constant=True)
    def schedule(self) -> QObject:
        return self._schedule

    @Property(QObject, constant=True)
    def gateway(self) -> QObject:
        return self._gateway

    @Property(QObject, constant=True)
    def device(self) -> QObject:
        return self._device
