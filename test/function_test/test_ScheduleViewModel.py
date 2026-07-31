from __future__ import annotations

import logging
import pytest
from dependency_injector import providers
from typing import Generator

from lw.logger_setup import LOG
from lw.test_event import wait_evaluation
from cansrv.file_service import FileService
from canapp.vm.schedule_view_model import ScheduleViewModel
from cansrv.module.fs_core import LogRecord
from canapp.vm.schedule_view_model import CANPlayEntry
from cansrv.snd_contract import SndAdd
from canapp.vm.container import AppContainer

def test_send_msg_loop(
    setup_vcan_devices: tuple[AppContainer, int],
) -> None:
    app, num = setup_vcan_devices

    # assert app.record_vm().record_id_event.is_set()
    # 1: User lock a channel
    device = app.channel_vm().available_devices[0]
    """ 20260729 BUG:
        1. Singleton is not created instance until first call (), it only passing the providers 
        -> the viewmodel is not created after the fixture setup vcan, it only calls channel_vm()
    """
    assert app.schedule_vm().available_devices[0] is not None
    app.channel_vm().wait_ready(lambda: app.channel_vm().acquireDevice(device))
    assert app.schedule_vm().acquired_devices[0] is not None

    # 1: user create entry at send panel
    assert device is not None
    parsed = LogRecord()
    parsed.can_id = 0x123
    parsed.channel = "can0"
    parsed.data = bytes([0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88])

    """ 20260728 BUG: LogRecord data field is the fixed size 64 so that its len always 64
            parsed.data_len = len(parsed.data)
    """
    parsed.data_len = 8

    parsed.direction = 1          # RX or TX depending on your enum
    parsed.timestamp = 1.234567   # seconds
    entry = CANPlayEntry(device_info=device, entry=parsed, initial_periodic=0.5)

    # 2: User press send button 
    app.schedule_vm().wait_ready(lambda: app.schedule_vm().sendMsgLoop(entry))
    #vm.sendMsgLoop(entry)

    # 3: User wait 3 seconds
    app.schedule_vm().wait(5.0)

    #4: User press pause
    app.schedule_vm().wait_ready(lambda: app.schedule_vm().pauseMsg(entry))

    #5: Auto release device #TODO need to add
    app.channel_vm().wait_ready(lambda: app.channel_vm().releaseDevice(device))

