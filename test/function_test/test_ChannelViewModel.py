from __future__ import annotations

import logging
import pytest
import time

from lw.logger_setup import LOG
# from lw.test_event import wait
from cansrv.test.fixture import CANService
from canapp.vm.channel_view_model import ChannelViewModel
from canapp.vm.container import AppContainer

def test_channel_view_model_call_vm_functions(
    setup_vcan_devices: tuple[AppContainer, int],
) -> None:
    app , _ = setup_vcan_devices

    selected_id = app.channel_vm()[0]
    device = next(
        d for d in app.channel_vm().available_devices
        if str(d.device_id) == selected_id
    )

    acquired = app.channel_vm().acquireDevice(device)
    assert isinstance(acquired, bool)

    time.sleep(5)

    app.channel_vm().releaseDevice(device)
