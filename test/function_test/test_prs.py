from __future__ import annotations

import threading
import time
import subprocess
from pathlib import Path
import pytest

from cansrv.application_events import (
    DBCLoadedEvent,
    ParserStatusEvent,
)
# from file_service.record_id import RecordId
from cansrv.file_service import FileService, get_file_service
from cansrv.metadata_id import LogId as RecordId
from cansrv.status import ParserStatus
from mock_vm import ParseModel
from lw.test_event import wait
from canapp.vm.log_viewmodel import LogViewModel

pytest_plugins = ["fixture"]

@pytest.fixture
def app_vm() -> LogViewModel:
	print("CS app_vm")
	return LogViewModel()

TIMEOUT_QUERY_MS = 30
TIMEOUT = 0.8
PARSE_TIMEOUT = 15.0
POLL_INTERVAL = 0.1

@pytest.mark.parametrize(
    "file_path",
    [
        "/home/gnar911/Desktop/2025-02-11_11-14-53_仕様情報切替 1.asc",
    ],
)
def test_05_parse_log(file_service: tuple[FileService, LogViewModel], file_path: str) -> None:
    _, vm = file_service

    """ NOTE: using the ViewModel function instead"""
    #assert file_srv.parse_log(file_path)
    vm.startParsing(file_path)
    assert vm.parser_done_event.wait(PARSE_TIMEOUT)

    visible_entries = wait(lambda: vm.entries, max_ms=TIMEOUT_QUERY_MS)
    total = wait(lambda: vm.totalLines, max_ms=TIMEOUT_QUERY_MS)
    assert vm.log_id is not None
    log_id = vm.log_id
    print(total)