from __future__ import annotations

import pytest
import logging
from lw.logger_setup import LOG
LOG.setLevel(logging.DEBUG)
# from file_service.record_id import RecordId
from cansrv.file_service import FileService, get_file_service
from cansrv.metadata_id import LogId as RecordId
# from cansrv.status import ParserStatus
from mock_vm import ParseModel
from lw.test_event import wait_evaluation
from canapp.vm.log_viewmodel import (
    LogViewModel,
    MsgFilter,
    ChannelFilter,
    TimeFilter,
)
from canapp.vm.data_object import CANLogLine
from canapp.vm.container import AppContainer

pytest_plugins = ["fixture"]

TIMEOUT_LOADPAGE_MS = 1000
TIMEOUT_QUERY_MS = 30
TIMEOUT = 0.8
PARSE_TIMEOUT = 15.0
POLL_INTERVAL = 0.1

# @pytest.fixture
# def app_vm() -> LogViewModel:
# 	print("CS app_vm")
# 	return LogViewModel()

@pytest.fixture
def container():
	yield AppContainer()

@pytest.mark.parametrize(
    "file_path",
    [
        "/home/gnar911/Desktop/2025-02-11_11-14-53_仕様情報切替 1.asc",
    ],
)
def test_05_parse_log(can_service: AppContainer, file_path: str) -> None:
    vm = can_service.log_vm()

    vm.startParsing(file_path)
    assert vm.parser_done_event.wait(PARSE_TIMEOUT)

    page_entries = wait_evaluation(lambda: vm.entries, max_ms=TIMEOUT_LOADPAGE_MS)
    total = wait_evaluation(lambda: vm.totalLines, max_ms=TIMEOUT_QUERY_MS)

    assert page_entries is not None
    assert total > 0
    assert vm.log_id is not None
    assert len(page_entries) > 0
    print(total)


def test_viewbrowser(tmp_path):
    from cansrv.module import fs_core

    base = str(tmp_path / "fs_test_pybind")
    # Use MetaDataStorageInterface to write and browse entries
    storage = fs_core.MetaDataStorageInterface(base)

    p = fs_core.ParsedEntry()
    p.timestamp = 1.234
    p.can_id = 0xABC
    p.direction = 0
    p.data_len = 3
    p.data = b"\x01\x02\x03"
    p.channel = "can0"

    # write_entries expects a sequence of LogRecord/ParsedEntry
    storage.write_entries([p])

    # obtain a ViewBrowser from the storage and validate
    vb = storage.browse_all()
    assert vb.size() >= 1
    first = vb.at(0)
    assert int(first.can_id) == 0xABC


def test_viewbrowser_two_instances(tmp_path):
    from cansrv.module import fs_core
    import gc

    base = str(tmp_path / "fs_test_pybind_two")

    # Create first storage and write one parsed entry
    s1 = fs_core.MetaDataStorageInterface(base)
    p = fs_core.ParsedEntry()
    p.timestamp = 2.345
    p.can_id = 0xABC
    p.direction = 0
    p.data_len = 3
    p.data = b"\x04\x05\x06"
    p.channel = "can0"

    s1.write_entries([p])

    # Destroy first instance and force GC to ensure resources are released
    del s1
    gc.collect()

    # Reopen via a second MetaDataStorageInterface and obtain a ViewBrowser
    s2 = fs_core.MetaDataStorageInterface(base)
    vb2 = s2.browse_all()
    assert vb2.size() >= 1
    first2 = vb2.at(0)
    assert int(first2.can_id) == 0xABC