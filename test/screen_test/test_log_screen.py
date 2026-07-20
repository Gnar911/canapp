from __future__ import annotations

import pytest
from PySide6.QtCore import QEventLoop, Qt

# from canapp.widgets.TreeLogMessage import TreeLogMessage
from canapp.TreeLogView import TreeLogView
from cansrv.test.fixture import CANService, FileService, TestServices, all_service

PARSE_TIMEOUT = 15.0




@pytest.mark.parametrize(
    "file_path",
    [
        "/home/gnar911/Desktop/2025-02-11_11-14-53_仕様情報切替 1.asc",
    ],
)
@pytest.mark.manual
def test_tree_log_message_manual(
    qtbot,
    all_service: tuple[CANService, FileService, TestServices],
    file_path: str,
) -> None:
    _, _, vm = all_service

    widget = TreeLogView()
    qtbot.addWidget(widget)

    widget.resize(1400, 900)
    widget.show()

    # Simulate waiting 3 seconds before pressing Parse.
    qtbot.wait(3000)

    vm.startParsing(file_path)

    qtbot.waitUntil(
        lambda: vm.parser_done_event.is_set(),
        timeout=PARSE_TIMEOUT * 1000,
    )

    # Manual inspection time.
    qtbot.wait(30_000)

    # Test returns here.
    # pytest-qt cleans up widget because of addWidget().
