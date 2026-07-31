from __future__ import annotations

import logging
import pytest
from dependency_injector import providers
import time

from lw.logger_setup import LOG
from lw.test_event import wait_evaluation
from cansrv.file_service import FileService, LogId
from canapp.vm.log_viewmodel import LogViewModel
from canapp.vm.record_viewmodel import (
    RecordViewModel,
)
from canapp.vm.schedule_view_model import (
    ScheduleViewModel, CANPlayEntry, LogRecord
)
from canapp.vm.replay_view_model import (
    ReplayViewModel,
)
from canapp.vm.container import AppContainer

def test_record_view_model_call_vm_functions(
    setup_vcan_devices: tuple[AppContainer, int],
) -> None:
    app, num = setup_vcan_devices

    device = app.channel_vm().available_devices[0]
    app.channel_vm().wait_ready(lambda: app.channel_vm().acquireDevice(device))

    # 1: User create the entry from treeview on channel panel
    device = app.channel_vm().acquired_devices[0]
    parsed = LogRecord()
    parsed.can_id = 0x123
    parsed.channel = "can0"
    parsed.data = bytes([0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88])
    parsed.data_len = 8
    parsed.direction = 1          # RX or TX depending on your enum
    parsed.timestamp = 1.234567   # seconds

    """ NOTE: this 500.0 is 500 seconds, and it cost 1 day to debug it !!!!!!!!!11"""
    entry = CANPlayEntry(device_info=device, entry=parsed, initial_periodic_second=0.5)

    # 2: User press send button on send panel
    app.schedule_vm().wait_ready(lambda: app.schedule_vm().sendMsgLoop(entry))

    # 6: The send loop process keep running at the background for 3 seconds
    time.sleep(20.0)
    # display_entry = wait_evaluation(lambda: app.record_vm().entry, max_ms=16.7, name= "entry eval")
    # assert display_entry is not None
    assert app.record_vm().totalRows > 5

    # 7: User back and press pause send
    app.schedule_vm().wait_ready(lambda: app.schedule_vm().pauseMsg(entry))

    #8: Auto release device #TODO need to add
    app.channel_vm().wait_ready(lambda: app.channel_vm().releaseDevice(device))