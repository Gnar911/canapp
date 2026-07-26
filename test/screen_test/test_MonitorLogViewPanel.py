from __future__ import annotations

import pytest

from lw.test_event import wait
from canapp.vm.record_viewmodel import RecordViewModel
from canapp.MonitorLogViewPanel import MonitorLogViewPanel
from cansrv.test.fixture import FileService

pytest_plugins = ["fixture"]

TIMEOUT_STATUS = 3.0
TIMEOUT_QUERY_MS = 30


@pytest.fixture
def app_vm() -> RecordViewModel:
    print("CS app_vm")
    return RecordViewModel()


@pytest.mark.manual
def test_monitor_log_panel_record_flow_manual(
    qtbot,
    file_service: tuple[FileService, RecordViewModel],
) -> None:
    _, vm = file_service

    widget = MonitorLogViewPanel(None, vm)
    qtbot.addWidget(widget)

    widget.resize(860, 640)
    widget.show()
    qtbot.wait(300)

    vm.startNewRecording()
    assert vm.recorder_wait_ring_event.wait(TIMEOUT_STATUS)
    assert wait(lambda: vm.isRecording, max_ms=TIMEOUT_QUERY_MS) is True

    vm.stopRecording()
    assert vm.recorder_stopped_event.wait(TIMEOUT_STATUS)
    assert wait(lambda: vm.isRecording, max_ms=TIMEOUT_QUERY_MS) is False
