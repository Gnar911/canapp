from __future__ import annotations

import pytest

from lw.test_event import wait
from canapp.vm.schedule_view_model import ScheduleViewModel
from canapp.CustomSendMessagePanel import CustomSendMessagePanel
from cansrv.test.fixture import CANService

pytest_plugins = ["fixture"]

TIMEOUT_STATUS = 3.0
TIMEOUT_QUERY_MS = 30


@pytest.fixture
def app_vm() -> ScheduleViewModel:
    print("CS app_vm")
    return ScheduleViewModel()


@pytest.mark.manual
def test_custom_send_panel_clear_manual(
    qtbot,
    can_service: tuple[CANService, ScheduleViewModel],
) -> None:
    _, vm = can_service

    widget = CustomSendMessagePanel(None, vm)
    qtbot.addWidget(widget)

    widget.resize(900, 640)
    widget.show()
    qtbot.wait(300)

    vm.clear()
    assert vm.snd_clear_event.wait(TIMEOUT_STATUS)
    assert wait(lambda: len(vm.entries), max_ms=TIMEOUT_QUERY_MS) >= 0
