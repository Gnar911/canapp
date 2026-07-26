from __future__ import annotations

import pytest

from lw.test_event import wait
from canapp.vm.channel_view_model import ChannelViewModel
from canapp.ChannelsTab import ChannelsTab
from cansrv.test.fixture import CANService

pytest_plugins = ["fixture"]

TIMEOUT_QUERY_MS = 30


@pytest.fixture
def app_vm() -> ChannelViewModel:
    print("CS app_vm")
    return ChannelViewModel()


@pytest.mark.manual
def test_channels_tab_smoke_manual(
    qtbot,
    setup_vcan_devices: tuple[CANService, ChannelViewModel, int],
) -> None:
    _, vm, _ = setup_vcan_devices

    widget = ChannelsTab(vm, None)
    qtbot.addWidget(widget)

    widget.resize(780, 560)
    widget.show()

    qtbot.wait(50_000)
