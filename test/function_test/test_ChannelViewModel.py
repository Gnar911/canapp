from __future__ import annotations

import logging
import pytest

from lw.logger_setup import LOG
from lw.test_event import wait
from cansrv.test.fixture import CANService
from canapp.vm.channel_view_model import ChannelViewModel
from canapp.container import AppContainer

LOG.setLevel(logging.DEBUG)

pytest_plugins = ["fixture"]

TIMEOUT_QUERY_MS = 1000


@pytest.fixture
def app_vm() -> ChannelViewModel:
    print("CS app_vm")
    return ChannelViewModel()

def test_channel_view_model_defaults(
    setup_vcan_devices: tuple[CANService, ChannelViewModel, int],
) -> None:
    _, vm, _ = setup_vcan_devices

    assert wait(lambda: isinstance(vm.vendor_list, list), max_ms=TIMEOUT_QUERY_MS)
    assert wait(lambda: isinstance(vm.available_device_lists, list), max_ms=TIMEOUT_QUERY_MS,)

def test_channel_view_model_call_vm_functions(
    setup_vcan_devices: tuple[CANService, ChannelViewModel, int],
) -> None:
    _, vm, _ = setup_vcan_devices

    listed = wait(lambda: vm.available_device_lists, max_ms=TIMEOUT_QUERY_MS,)
    assert listed, "No available devices found from viewmodel"

    selected_id = listed[0]
    device = next(
        d for d in vm.available_devices
        if str(d.device_id) == selected_id
    )

    acquired = vm.acquireDevice(device)
    assert isinstance(acquired, bool)

    vm.releaseDevice(device)
