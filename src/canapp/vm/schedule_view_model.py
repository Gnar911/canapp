from __future__ import annotations

from PySide6.QtCore import Signal, Slot, QObject

from cs_test.mock_vm import SendStatusVM
from cansrv.can_srv import CANService, CANDeviceInfo
from cansrv.snd_contract import (
    SndAdd,
    SndClear,
    SndPause,
    SndRemove,
    SndResume,
    SndUpdateData,
    SndUpdatePeriod,
    SndDeviceAccquired,
    SndDeviceUnaccquired,
)
from lw.srv_event import SrvEvent
from cansrv.module.fs_core import ParsedEntry


class ScheduleViewModel(QObject, SendStatusVM):
    scheduleStateChanged = Signal()

    def __init__(self):
        super().__init__()
        self._can_service = CANService()
        self._is_active = False
        self._active_count = 0

    @property
    def isActive(self) -> bool:
        return self._is_active

    @isActive.setter
    def isActive(self, value: bool) -> None:
        if self._is_active == value:
            return
        self._is_active = value
        self.scheduleStateChanged.emit()

    @property
    def isStop(self) -> bool:
        return not self._is_active

    @property
    def activeCount(self) -> int:
        return int(self._active_count)

    @activeCount.setter
    def activeCount(self, value: int) -> None:
        value = max(0, int(value))
        if self._active_count == value:
            return
        self._active_count = value
        self.scheduleStateChanged.emit()

    @Slot("QVariant", "QVariant", float)
    def sendMsgLoop(self, device_info: CANDeviceInfo, entry: ParsedEntry, initial_periodic: float) -> None:
        self._can_service.send_msg_loop(device_info, entry, initial_periodic)
        return None

    @Slot("QVariant", "QVariant")
    def sendOnce(self, device_info: CANDeviceInfo, entry: ParsedEntry) -> None:
        self._can_service.send_once(device_info, entry)
        return None

    @Slot("QVariant", "QVariant")
    def pauseMsg(self, device_info: CANDeviceInfo, entry: ParsedEntry) -> None:
        self._can_service.pause_msg(device_info, entry)
        return None

    @Slot("QVariant", "QVariant")
    def resumeMsg(self, device_info: CANDeviceInfo, entry: ParsedEntry) -> None:
        self._can_service.resume_msg(device_info, entry)
        return None

    @Slot("QVariant", "QVariant")
    def removeMsg(self, device_info: CANDeviceInfo, entry: ParsedEntry) -> None:
        self._can_service.remove_msg(device_info, entry)
        return None

    @Slot()
    def clear(self) -> None:
        self._can_service.clear()
        return None

    @Slot("QVariant", "QVariant", float)
    def updatePeriodic(self, device_info: CANDeviceInfo, entry: ParsedEntry, period: float) -> None:
        self._can_service.update_periodic(device_info, entry, period)
        return None

    def on_send_status(self, event: SrvEvent) -> None:
        SendStatusVM.on_send_status(self, event)

        evt = event

        if isinstance(evt, SndAdd):
            self.activeCount = self.activeCount + 1
            self.isActive = True
        elif isinstance(evt, SndRemove):
            self.activeCount = max(0, self.activeCount - 1)
            self.isActive = self.activeCount > 0
        elif isinstance(evt, SndClear):
            self.activeCount = 0
            self.isActive = False
        elif isinstance(evt, SndPause):
            self.isActive = False
        elif isinstance(evt, SndResume):
            self.isActive = self.activeCount > 0
        elif isinstance(evt, SndUpdatePeriod):
            self.isActive = self.activeCount > 0
        elif isinstance(evt, SndUpdateData):
            self.isActive = self.activeCount > 0
        elif isinstance(evt, SndDeviceAccquired):
            self.isActive = self.activeCount > 0
        elif isinstance(evt, SndDeviceUnaccquired):
            # conservative reset on device detach to avoid stale active counters
            self.activeCount = 0
            self.isActive = False
