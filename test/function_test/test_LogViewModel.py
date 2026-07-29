from __future__ import annotations

import pytest
import logging
from lw.logger_setup import LOG
LOG.setLevel(logging.DEBUG)
# from file_service.record_id import RecordId
from cansrv.file_service import FileService, get_file_service
from cansrv.metadata_id import LogId as RecordId
from cansrv.status import ParserStatus
from mock_vm import ParseModel
from lw.test_event import wait_evaluation
from canapp.vm.log_viewmodel import (
    LogViewModel,
    MsgFilter,
    ChannelFilter,
    TimeFilter,
)
from canapp.vm.data_object import CANLogLine
from canapp.container import AppContainer

pytest_plugins = ["fixture"]

TIMEOUT_LOADPAGE_MS = 1000
TIMEOUT_QUERY_MS = 30
TIMEOUT = 0.8
PARSE_TIMEOUT = 15.0
POLL_INTERVAL = 0.1
TEST_ASC_PATH = "/home/gnar911/Desktop/2025-02-11_11-14-53_仕様情報切替 1.asc"


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
        TEST_ASC_PATH,
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


@pytest.mark.parametrize("file_path", [TEST_ASC_PATH])
def test_06_page_size_and_page_num(file_service: tuple[FileService, LogViewModel], file_path: str) -> None:
    _, vm = file_service

    vm.startParsing(file_path)
    assert vm.parser_done_event.wait(PARSE_TIMEOUT)

    total = wait(lambda: vm.totalLines, max_ms=TIMEOUT_QUERY_MS)
    assert total > 0

    vm.pageSize = 100
    assert vm.pageNum == 0

    first_page = wait(lambda: vm.entries, max_ms=TIMEOUT_LOADPAGE_MS)
    assert first_page is not None
    assert len(first_page) <= 100

    vm.pageNum = 1
    second_page = wait(lambda: vm.entries, max_ms=TIMEOUT_LOADPAGE_MS)
    assert second_page is not None
    assert len(second_page) <= 100

    if total > 100:
        assert len(second_page) > 0
        assert second_page[0].line_number != first_page[0].line_number


@pytest.mark.parametrize("file_path", [TEST_ASC_PATH])
def test_07_total_pages_formula(file_service: tuple[FileService, LogViewModel], file_path: str) -> None:
    _, vm = file_service

    vm.startParsing(file_path)
    assert vm.parser_done_event.wait(PARSE_TIMEOUT)

    total = wait(lambda: vm.totalLines, max_ms=TIMEOUT_QUERY_MS)
    assert total > 0

    for page_size in (1, 10, 128, 1000):
        vm.pageSize = page_size
        expected = (total + page_size - 1) // page_size
        assert vm.totalPages == expected


@pytest.mark.parametrize("file_path", [TEST_ASC_PATH])
def test_08_close_log_clears_state(file_service: tuple[FileService, LogViewModel], file_path: str) -> None:
    _, vm = file_service

    vm.startParsing(file_path)
    assert vm.parser_done_event.wait(PARSE_TIMEOUT)

    entries = wait(lambda: vm.entries, max_ms=TIMEOUT_LOADPAGE_MS)
    total = wait(lambda: vm.totalLines, max_ms=TIMEOUT_QUERY_MS)
    assert entries is not None
    assert total > 0

    assert vm.metadata is not None
    assert vm.progressBarIsActive is True

    vm.closeLog()

    assert vm.metadata is None
    assert vm.progressBarIsActive is False
    assert vm.entries is None
    assert vm.totalLines == 0
    assert vm.filterMessageList == []
    assert vm.filterChannelList == []


@pytest.mark.parametrize("file_path", [TEST_ASC_PATH])
def test_09_message_filter_list_and_entries(file_service: tuple[FileService, LogViewModel], file_path: str) -> None:
    _, vm = file_service

    vm.startParsing(file_path)
    assert vm.parser_done_event.wait(PARSE_TIMEOUT)

    entries = wait(lambda: vm.entries, max_ms=TIMEOUT_LOADPAGE_MS)
    total = wait(lambda: vm.totalLines, max_ms=TIMEOUT_QUERY_MS)
    assert entries is not None
    assert total > 0

    all_messages = vm.filterMessageList
    assert len(all_messages) > 0

    selected_can_id = int(all_messages[0].data.can_id)
    vm.messageFilter = MsgFilter(can_id=selected_can_id)

    filtered_messages = vm.filterMessageList
    checked_messages = [m for m in filtered_messages if m.checked]
    assert len(checked_messages) == 1
    assert int(checked_messages[0].data.can_id) == selected_can_id

    filtered_entries = wait(lambda: vm.entries, max_ms=TIMEOUT_LOADPAGE_MS)
    assert filtered_entries is not None
    assert len(filtered_entries) > 0
    assert all(int(e.can_id) == selected_can_id for e in filtered_entries)


@pytest.mark.parametrize("file_path", [TEST_ASC_PATH])
def test_10_channel_filter_list_and_entries(file_service: tuple[FileService, LogViewModel], file_path: str) -> None:
    _, vm = file_service

    vm.startParsing(file_path)
    assert vm.parser_done_event.wait(PARSE_TIMEOUT)

    entries = wait(lambda: vm.entries, max_ms=TIMEOUT_LOADPAGE_MS)
    total = wait(lambda: vm.totalLines, max_ms=TIMEOUT_QUERY_MS)
    assert entries is not None
    assert total > 0

    all_channels = vm.filterChannelList
    assert len(all_channels) > 0

    selected_channel = str(all_channels[0].data.channel)
    vm.messageFilter = ChannelFilter(channel=selected_channel)

    filtered_channels = vm.filterChannelList
    checked_channels = [c for c in filtered_channels if c.checked]
    assert len(checked_channels) == 1
    assert str(checked_channels[0].data.channel) == selected_channel

    filtered_entries = wait(lambda: vm.entries, max_ms=TIMEOUT_LOADPAGE_MS)
    assert filtered_entries is not None
    assert len(filtered_entries) > 0
    assert all(str(e.channel) == selected_channel for e in filtered_entries)


@pytest.mark.parametrize("file_path", [TEST_ASC_PATH])
def test_11_time_filter_entries(file_service: tuple[FileService, LogViewModel], file_path: str) -> None:
    _, vm = file_service

    vm.startParsing(file_path)
    assert vm.parser_done_event.wait(PARSE_TIMEOUT)

    entries = wait(lambda: vm.entries, max_ms=TIMEOUT_LOADPAGE_MS)
    total = wait(lambda: vm.totalLines, max_ms=TIMEOUT_QUERY_MS)
    assert entries is not None
    assert total > 0

    assert len(entries) > 2

    first_ts = float(entries[0].timestamp)
    last_ts = float(entries[min(len(entries) - 1, 50)].timestamp)
    if last_ts < first_ts:
        first_ts, last_ts = last_ts, first_ts

    vm.messageFilter = TimeFilter(first_ts=first_ts, last_ts=last_ts)

    filtered_entries = wait(lambda: vm.entries, max_ms=TIMEOUT_LOADPAGE_MS)
    assert filtered_entries is not None
    assert len(filtered_entries) > 0
    for row in filtered_entries:
        assert first_ts <= float(row.timestamp) <= last_ts


@pytest.mark.parametrize("file_path", [TEST_ASC_PATH])
def test_12_editing_line_overrides_row(file_service: tuple[FileService, LogViewModel], file_path: str) -> None:
    _, vm = file_service

    vm.startParsing(file_path)
    assert vm.parser_done_event.wait(PARSE_TIMEOUT)

    entries = wait(lambda: vm.entries, max_ms=TIMEOUT_LOADPAGE_MS)
    total = wait(lambda: vm.totalLines, max_ms=TIMEOUT_QUERY_MS)
    assert entries is not None
    assert total > 0

    original = entries[0]

    edited = CANLogLine.from_parsed_entry(original.to_parsed_entry())
    edited.message_name = "OVERRIDE_MSG"

    vm.editingLine = {int(original.line_number): edited}

    refreshed = wait(lambda: vm.entries, max_ms=TIMEOUT_LOADPAGE_MS)
    assert refreshed is not None
    row = next(r for r in refreshed if int(r.line_number) == int(original.line_number))
    assert row.message_name == "OVERRIDE_MSG"


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