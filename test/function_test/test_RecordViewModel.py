from __future__ import annotations

import logging
import pytest

from lw.logger_setup import LOG
from lw.test_event import wait
from cansrv.file_service import FileService, LogId
from cansrv.application_events import RecorderStatusEvent
from cansrv.status import RecorderStatus
from canapp.vm.record_viewmodel import RecordViewModel

LOG.setLevel(logging.DEBUG)

pytest_plugins = ["fixture"]

TIMEOUT_QUERY_MS = 1000


@pytest.fixture
def app_vm() -> RecordViewModel:
    print("CS app_vm")
    return RecordViewModel()


def test_record_view_model_call_vm_functions(
    file_service: tuple[FileService, RecordViewModel],
) -> None:
    _, vm = file_service

    vm.startNewRecording()
    vm.stopRecording()
    vm.row = 1

    assert vm.saveRecord("sample") is False
    assert wait(lambda: vm.row == 1, max_ms=TIMEOUT_QUERY_MS)
