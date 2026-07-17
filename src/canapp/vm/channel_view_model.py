from __future__ import annotations

from typing import Any

from PySide6.QtCore import Property, Signal, Slot

from .base_view_model import BaseViewModel
from cs_test.mock_vm import *
from can_service.can_srv import CANDeviceInfo
from can_service.srv_if import get_can_service_facade

class ChannelViewModel(BaseViewModel, ScannerVM):
    deviceStateChanged = Signal()

    def __init__(self):
        super().__init__()
        self._can_service = get_can_service_facade()
        self._available_devices: list[CANDeviceInfo] = []
        self._acquired_devices: list[CANDeviceInfo] = []

    @property
    def available_devices(self) -> list[CANDeviceInfo]:
        return self._available_devices

    @property
    def acquired_devices(self):
        return self._acquired_devices
    
    @acquired_devices.setter
    def acquired_devices(self, value):
        if self._acquired_devices == value:
            return

        self._acquired_devices = value
        self.deviceStateChanged.emit()

    @available_devices.setter
    def available_devices(self, value):
        if self._available_devices == value:
            return

        self._available_devices = value
        self.deviceStateChanged.emit()

    def on_scan_status(self, payload: ResponseACK | NotificationEvent) -> None:
        ScannerVM.on_scan_status(payload)
        if isinstance(payload, NotificationEvent):

            if isinstance(payload, ScanDevicePluggedStatus):
                #NOTE: To avoid event edge signal re-dup
                if payload.device_info not in self.available_devices:
                    self.available_devices.append(payload.device_info)

            if isinstance(payload.evt, ScanDeviceUnpluggedStatus):
                device = payload.device_info

                self.available_devices = [
                    d for d in self.available_devices
                    if d.device_id != device.device_id
                ]

                self.acquired_devices = [
                    d for d in self.acquired_devices
                    if d.device_id != device.device_id
                ]

        if isinstance(payload, ResponseACK):
            event = payload
            if event.cmd_type == ScanChannelAcquiredStatus:
                # device = payload.device_info

                # self.available_devices.remove(device)
                # self.acquired_devices.append(device)
                pass

            if event.cmd_type == ScanChannelReleasedStatus:
                # device = payload.device_info

                # self.acquired_devices.remove(device)
                # self.available_devices.append(device)
                pass
            
    @Slot(int, result=bool)
    def acquireDevice(self, selected_index: int) -> bool:

        if not (0 <= selected_index < len(self._available_devices)):
            return False

        device = self._available_devices[selected_index]

        return bool(self._can_service.acquire(device))

    @Slot(int)
    def releaseDevice(self, selected_index: int) -> None:

        if not (0 <= selected_index < len(self._acquired_devices)):
            return

        device = self._acquired_devices[selected_index]

        self._can_service.release(device)

