from __future__ import annotations

from typing import Any

from PySide6.QtCore import Property, Signal, Slot, QObject

# from .base_view_model import BaseViewModel
from cansrv.test.mock_vm import *
from cansrv.can_srv import CANDeviceInfo, CANService
# from canapp.data_object import DeviceInfoLine
from lw.srv_event import SrvEvent
from PySide6.QtCore import (
    Qt,
    QModelIndex,
    QAbstractListModel,
)

@dataclass(frozen=True)
class DeviceInfoLine:
    data: CANDeviceInfo
    vendor_name: str
    channel_name: str
    channel_index: int

    is_available: bool
    is_acquired: bool
    is_disconnected: bool

    @property
    def show(self):
        return f"{self.vendor_name}: Channel {self.channel_name}:"

    @property
    def status_color(self) -> str:
        if self.is_disconnected:
            return "red"
        if self.is_acquired:
            return "green"
        if self.is_available:
            return "orange"
        return "gray"

    @property
    def status_show(self):
        if self.is_disconnected:
            return "DISCONNECTED"
        if self.is_acquired:
            return "LOCKED"
        if self.is_available:
            return "AVAILABLE"
    
class ChannelViewModel(QObject, ScannerVM):
    deviceStateChanged = Signal()

    def __init__(self, can_service: CANService):
        super().__init__()
        if can_service is None:
            raise TypeError("ChannelViewModel requires a CANService instance")
        self._can_service = can_service
        #file_srv.subscribe_any(vm.on_status_callback)
        can_service.subscribe(self.on_status_callback)

    def on_status_callback(self, event: SrvEvent):
        super().on_status_callback(event)
        """ NOTE: List is updated at the parent ScannerVM but we do not have react for list so we emit manually"""
        self.deviceStateChanged.emit()
            
    @Slot(object, result=bool)
    def acquireDevice(
        self,
        device: CANDeviceInfo,
    ):
        return self._can_service.acquire(device)

    @Slot(object)
    def releaseDevice(self, device: CANDeviceInfo):
        return self._can_service.release(device)

    """ Vendor list box"""
    @property
    def vendor_list(self) -> list[str]:
        vendors = {
            dev.vendor
            for dev in (*self.available_devices, *self.acquired_devices)
        }
        return sorted(vendors)

    """ Status tree display"""
    @property
    def all_device_status(self) -> list[DeviceInfoLine]:
        lines: list[DeviceInfoLine] = []

        for dev in self.available_devices:
            lines.append(
                DeviceInfoLine(
                    dev,
                    str(dev.vendor),
                    str(dev.device_id),
                    0,
                    True,
                    False,
                    False,
                )
            )

        for dev in self.acquired_devices:
            lines.append(
                DeviceInfoLine(
                    dev,
                    str(dev.vendor),
                    str(dev.device_id),
                    0,
                    False,
                    True,
                    False,
                )
            )

        return lines
    
    """ Combobox display"""
    @property
    def available_device_lists(self) -> list[str]:
        return [
            str(dev.device_id)
            for dev in self.available_devices
        ]

    @property
    def isHavingDevices(self) -> bool:
        return len(self.all_device_status) != 0