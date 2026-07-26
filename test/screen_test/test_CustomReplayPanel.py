from __future__ import annotations

import pytest

from lw.test_event import wait
from canapp.vm.replay_view_model import ReplayViewModel
from canapp.CustomReplayPanel import CustomReplayPanel
from cansrv.test.fixture import CANService

pytest_plugins = ["fixture"]

TIMEOUT_STATUS = 3.0
TIMEOUT_QUERY_MS = 30


@pytest.fixture
def app_vm() -> ReplayViewModel:
    print("CS app_vm")
    return ReplayViewModel()


@pytest.mark.manual
def test_custom_replay_panel_controls_manual(
    qtbot,
    can_service: tuple[CANService, ReplayViewModel],
) -> None:
    _, vm = can_service

    widget = CustomReplayPanel(vm, None)
    qtbot.addWidget(widget)

    widget.resize(920, 680)
    widget.show()
    qtbot.wait(300)

    vm.setLoop(True)
    assert vm.replay_loop_set_event.wait(TIMEOUT_STATUS)
    assert wait(lambda: vm.isLoopOn, max_ms=TIMEOUT_QUERY_MS) is True

    vm.setRepeat(2)
    assert vm.replay_repeat_set_event.wait(TIMEOUT_STATUS)
    assert wait(lambda: vm.setCycle, max_ms=TIMEOUT_QUERY_MS) == 2

    vm.setTimeScope(0.0, 1.0)
    assert vm.replay_timescope_set_event.wait(TIMEOUT_STATUS)
    assert wait(lambda: vm.hasTimeScope, max_ms=TIMEOUT_QUERY_MS) is True
