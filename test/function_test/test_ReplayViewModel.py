from __future__ import annotations

import logging
import pytest

from lw.logger_setup import LOG
from lw.test_event import wait_evaluation
from cansrv.can_srv import CANService
from cansrv.file_service import LogId
from canapp.vm.replay_view_model import (
    ReplayViewModel,
)
from canapp.vm.log_viewmodel import (
    LogViewModel,
)
from canapp.vm.container import AppContainer

LOG.setLevel(logging.DEBUG)

pytest_plugins = ["fixture"]

TIMEOUT_QUERY_MS = 500
TIMEOUT_REPLAY = 15000
            
class ReplayTestMockVM(ReplayViewModel, LogViewModel):
    def __init__(self):
        print(ReplayTestMockVM.mro())
        """ 20260726 BUG: should use super to got MRO -> still not work
            QObject.__init__() does not call super() into arbitrary Python -> break MRO chain
                    super().__init__()

        ReplayStatusVM, ScannerVM, SendStatusVM, ParseModel, DBCModel
        """
        ReplayViewModel.__init__(self)
        LogViewModel.__init__(self)

    def reset(self):
        ReplayViewModel.reset(self)
        LogViewModel.reset(self)

@pytest.fixture
def app_vm() -> ReplayTestMockVM:
    print("CS app_vm")
    return ReplayTestMockVM()

@pytest.mark.parametrize(
    "file_path",
    [
        "/home/gnar911/Desktop/2025-02-11_11-14-53_仕様情報切替 1.asc",
    ],
)
def test_start_replay(
    acquire_vcan_devices: tuple[CANService, ReplayTestMockVM], file_path: str
) -> None:
    _, vm = acquire_vcan_devices

    """ 20260726 NOTE BUG: A common bug when set up test is the time we are arrange it to trigger the event
                        if action A happens before action B -> testing error

                vm.startParsing(file_path)
                assert wait(lambda: vm.targetLog != "Null", max_ms=TIMEOUT_QUERY_MS)
    """
    vm.startParsing(file_path)
    assert vm.parser_done_event.wait(timeout_seconds=TIMEOUT_REPLAY / 1000)
    assert vm.targetLog != "Null"

    vm.startReplay()
    assert vm.replay_started_event.wait(timeout=TIMEOUT_QUERY_MS / 1000)
    assert vm.isReplay

    """ BUG: Need time for replay, other wise test case end and unaccquired happens while replaying -> BUG"""
    finished_in_10s = vm.rpl_finished_event.wait(timeout=10.0)
    assert finished_in_10s or vm.isReplay

@pytest.mark.parametrize(
    "file_path",
    [
        "/home/gnar911/Desktop/2025-02-11_11-14-53_仕様情報切替 1.asc",
    ],
)
def test_script_start_replay(
    acquire_vcan_devices: tuple[CANService, ReplayTestMockVM], file_path: str
) -> None:
    _, vm = acquire_vcan_devices

    # 1: User drop a file into the widget
    #vm.startParsing(file_path)
    vm.startParsing(file_path)
    vm.wait_done()
    # assert vm.parser_done_event.wait(timeout_seconds=TIMEOUT_REPLAY / 1000)
    # assert vm.targetLog != "Null"

    # 2: User press start replay button
    vm.wait_ready(lambda: vm.startReplay())
    # assert vm.replay_started_event.wait(timeout=TIMEOUT_QUERY_MS / 1000)
    # assert vm.isReplay

    """ BUG: Need time for replay, other wise test case end and unaccquired happens while replaying -> BUG"""
    # finished_in_10s = vm.rpl_finished_event.wait(timeout=10.0)
    # assert finished_in_10s or vm.isReplay

    # 3: User wait for 3 seconds
    vm.wait(3.0)

    # 4: User press stop button
    vm.wait_ready(lambda: vm.stopReplay())


def test_pause_replay(
    acquire_vcan_devices: tuple[CANService, ReplayTestMockVM],
) -> None:
    can_srv, vm = acquire_vcan_devices
    wait(lambda: vm.set_source(LogId.new()), max_ms=TIMEOUT_QUERY_MS)
    assert wait(lambda: vm.targetLog != "Null", max_ms=TIMEOUT_QUERY_MS)
    wait(lambda: vm.startReplay(), max_ms=TIMEOUT_QUERY_MS)
    assert wait(lambda: vm.isReplay is True, max_ms=TIMEOUT_QUERY_MS)

    wait(lambda: vm.pauseReplay(), max_ms=TIMEOUT_QUERY_MS)

    assert wait(lambda: vm.isPause is True, max_ms=TIMEOUT_QUERY_MS)


def test_resume_replay(
    acquire_vcan_devices: tuple[CANService, ReplayTestMockVM],
) -> None:
    can_srv, vm = acquire_vcan_devices
    wait(lambda: vm.set_source(LogId.new()), max_ms=TIMEOUT_QUERY_MS)
    assert wait(lambda: vm.targetLog != "Null", max_ms=TIMEOUT_QUERY_MS)
    wait(lambda: vm.startReplay(), max_ms=TIMEOUT_QUERY_MS)
    assert wait(lambda: vm.isReplay is True, max_ms=TIMEOUT_QUERY_MS)

    wait(lambda: vm.pauseReplay(), max_ms=TIMEOUT_QUERY_MS)
    assert wait(lambda: vm.isPause is True, max_ms=TIMEOUT_QUERY_MS)

    wait(lambda: vm.resumeReplay(), max_ms=TIMEOUT_QUERY_MS)

    assert wait(lambda: vm.isReplay is True, max_ms=TIMEOUT_QUERY_MS)


def test_set_loop(
    acquire_vcan_devices: tuple[CANService, ReplayTestMockVM],
) -> None:
    _, vm = acquire_vcan_devices

    wait(lambda: vm.setLoop(True), max_ms=TIMEOUT_QUERY_MS)

    assert wait(lambda: vm.isLoopOn is True, max_ms=TIMEOUT_QUERY_MS)


def test_set_repeat(
    acquire_vcan_devices: tuple[CANService, ReplayTestMockVM],
) -> None:
    _, vm = acquire_vcan_devices

    wait(lambda: vm.setRepeat(3), max_ms=TIMEOUT_QUERY_MS)

    assert wait(
        lambda: vm.isLoopOn is False and vm.setCycle == 3,
        max_ms=TIMEOUT_QUERY_MS,
    )


def test_set_msg_id_filter(
    acquire_vcan_devices: tuple[CANService, ReplayTestMockVM],
) -> None:
    _, vm = acquire_vcan_devices

    wait(lambda: vm.setMsgIdFilter(0x123), max_ms=TIMEOUT_QUERY_MS)

    assert wait(
        lambda: vm.hasMsgFilter is True and 0x123 in vm.config.ignored_msg_ids,
        max_ms=TIMEOUT_QUERY_MS,
    )


def test_clear_msg_id_filter(
    acquire_vcan_devices: tuple[CANService, ReplayTestMockVM],
) -> None:
    _, vm = acquire_vcan_devices
    wait(lambda: vm.setMsgIdFilter(0x123), max_ms=TIMEOUT_QUERY_MS)
    assert wait(lambda: vm.hasMsgFilter is True, max_ms=TIMEOUT_QUERY_MS)

    wait(lambda: vm.clearMsgIdFilter(), max_ms=TIMEOUT_QUERY_MS)

    assert wait(lambda: vm.hasMsgFilter is False, max_ms=TIMEOUT_QUERY_MS)


def test_set_time_scope(
    acquire_vcan_devices: tuple[CANService, ReplayTestMockVM],
) -> None:
    _, vm = acquire_vcan_devices

    wait(lambda: vm.setTimeScope(1.5, 4.0), max_ms=TIMEOUT_QUERY_MS)

    assert wait(
        lambda: vm.hasTimeScope is True and vm.timeRange == (1.5, 4.0),
        max_ms=TIMEOUT_QUERY_MS,
    )


def test_clear_time_scope(
    acquire_vcan_devices: tuple[CANService, ReplayTestMockVM],
) -> None:
    _, vm = acquire_vcan_devices
    wait(lambda: vm.setTimeScope(1.5, 4.0), max_ms=TIMEOUT_QUERY_MS)
    assert wait(lambda: vm.hasTimeScope is True, max_ms=TIMEOUT_QUERY_MS)

    wait(lambda: vm.clearTimeScope(), max_ms=TIMEOUT_QUERY_MS)

    assert wait(lambda: vm.hasTimeScope is False, max_ms=TIMEOUT_QUERY_MS)
