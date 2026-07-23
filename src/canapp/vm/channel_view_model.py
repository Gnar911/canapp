from __future__ import annotations

from typing import Any

from PySide6.QtCore import Property, Signal, Slot, QObject

# from .base_view_model import BaseViewModel
from cs_test.mock_vm import *
from cansrv.can_srv import CANDeviceInfo
from cansrv.can_srv import get_can_service
# from canapp.data_object import DeviceInfoLine
from lw.srv_event import SrvEvent
from PySide6.QtCore import (
    Qt,
    QModelIndex,
    QAbstractListModel,
)

@dataclass(frozen=True)
class DeviceInfoLine:
    vendor_name: str
    channel_name: str
    channel_index: int

    is_available: bool
    is_acquired: bool
    is_disconnected: bool

class ListModel(QAbstractListModel):
    ItemRole = Qt.UserRole + 1

    def __init__(
        self,
        viewmodel: ChannelViewModel,
        parent=None,
    ):
        super().__init__(parent)
        self._items = viewmodel._available_devices

    def rowCount(
        self,
        parent: QModelIndex = QModelIndex(),
    ) -> int:
        if parent.isValid():
            return 0

        return len(self._items)

    def data(
        self,
        index: QModelIndex,
        role: int = Qt.DisplayRole,
    ):
        if not index.isValid():
            return None

        row = index.row()

        if not 0 <= row < len(self._items):
            return None

        item = self._items[row]

        if role == Qt.DisplayRole:
            return item.show

        if role == self.ItemRole:
            return item

        return None

    def roleNames(self):
        return {
            self.ItemRole: b"item",
        }
    
class ChannelViewModel(QObject, ScannerVM):
    deviceStateChanged = Signal()

    def __init__(self):
        super().__init__()
        self._can_service = get_can_service()
        self._available_devices: list[CANDeviceInfo] = []
        self._cbx_model = ListModel(self)

        self._acquired_devices: list[CANDeviceInfo] = []

    """ State Machine"""
    # @property
    # def available_devices(self):
    #     return self._available_devices
    # @property
    # def acquired_devices(self):
    #     return self._acquired_devices
    
    # @acquired_devices.setter
    # def acquired_devices(self, value):
    #     if self._acquired_devices == value:
    #         return

    #     self._acquired_devices = value
    #     self.deviceStateChanged.emit()

    # @available_devices.setter
    # def available_devices(self, value):
    #     if self._available_devices == value:
    #         return

    #     self._available_devices = value
    #     self.deviceStateChanged.emit()
    """"""

    def on_scan_status(self, payload: SrvEvent) -> None:
        if isinstance(payload, ScanDevicePluggedStatus):
            # NOTE: avoid duplicate add when repeated plug notifications arrive
            if payload.device_info not in self.available_devices:
                self.available_devices.append(payload.device_info)
            return

        if isinstance(payload, ScanDeviceUnpluggedStatus):
            device = payload.device_info

            self.available_devices = [
                d for d in self.available_devices
                if d.device_id != device.device_id
            ]

            self.acquired_devices = [
                d for d in self.acquired_devices
                if d.device_id != device.device_id
            ]
            return

        if isinstance(payload, ScanChannelAcquiredStatus):
            device = payload.device_info
            self.available_devices.remove(device)
            self.acquired_devices.append(device)
            return

        if isinstance(payload, ScanChannelReleasedStatus):
            device = payload.device_info
            self.acquired_devices.remove(device)
            self.available_devices.append(device)
            return
            
    @Slot(object, result=bool)
    def acquireDevice(
        self,
        device: CANDeviceInfo,
    ) -> bool:
        return bool(
            self._can_service.acquire(device)
        )

    @Slot(object)
    def releaseDevice(self, device: CANDeviceInfo) -> None:
        self._can_service.release(device)

    """ Vendor list box"""
    @property
    def vendor_list(self) -> list[str]:
        vendors = {
            dev.vendor
            for dev in (*self._available_devices, *self._acquired_devices)
        }
        return sorted(vendors)

    """ Status tree display"""
    @property
    def all_device_status(self) -> list[DeviceInfoLine]:
        lines: list[DeviceInfoLine] = []

        for dev in self._available_devices:
            lines.append(
                DeviceInfoLine(
                    device=dev,
                    status="Available",
                )
            )

        for dev in self._acquired_devices:
            lines.append(
                DeviceInfoLine(
                    device=dev,
                    status="Acquired",
                )
            )

        return lines
    
    """ Combobox display"""
    @property
    def available_device_lists(self) -> list[str]:
        return [
            str(dev.device_id)
            for dev in self._available_devices
        ]