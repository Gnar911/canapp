from __future__ import annotations

import pytest
from PySide6.QtCore import QEventLoop, Qt

# from canapp.widgets.TreeLogMessage import TreeLogMessage
from canapp.vm.log_viewmodel import LogViewModel
from canapp.widgets.TreeLogView import TreeLogView
from cansrv.test.fixture import CANService, FileService

PARSE_TIMEOUT = 15.0

pytest_plugins = ["fixture"]

@pytest.fixture
def app_vm() -> LogViewModel:
	print("CS app_vm")
	return LogViewModel()

@pytest.mark.parametrize(
    "file_path",
    [
        "/home/gnar911/Desktop/2025-02-11_11-14-53_仕様情報切替 1.asc",
    ],
)
@pytest.mark.manual
def test_tree_log_manual(
    qtbot,
    file_service: tuple[FileService, LogViewModel], file_path: str,
) -> None:
    _, vm = file_service

    widget = TreeLogView(vm)
    qtbot.addWidget(widget)

    widget.resize(860, 640)
    widget.show()

    # Simulate waiting 3 seconds before pressing Parse.
    qtbot.wait(2000)

    vm.startParsing(file_path)
    qtbot.waitUntil(
        lambda: vm.parser_done_event.is_set(),
        timeout=PARSE_TIMEOUT * 1000,
    )

    # Manual inspection time.
    qtbot.wait(10_000)

    # Test returns here.
    # pytest-qt cleans up widget because of addWidget().
