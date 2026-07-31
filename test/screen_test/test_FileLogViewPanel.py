from __future__ import annotations

import pytest
from PySide6.QtCore import QEventLoop, Qt

# from canapp.widgets.TreeLogMessage import TreeLogMessage
from canapp.vm.log_viewmodel import LogViewModel
from canapp.FileLogViewPanel import FileLogViewPanel
# from canapp.widgets.TreeLogView import TreeLogView
# from canapp.widgets.TreeLogLazyLoad import TreeLogLazyLoad
from cansrv.test.fixture import CANService, FileService
from canapp.vm.container import AppContainer

# PARSE_TIMEOUT = 15.0

# pytest_plugins = ["fixture"]

# @pytest.fixture
# def app_vm() -> LogViewModel:
# 	print("CS app_vm")
# 	return LogViewModel()

@pytest.mark.parametrize(
    "file_path",
    [
        "/home/gnar911/Desktop/2025-02-11_11-14-53_仕様情報切替 1.asc",
    ],
)
@pytest.mark.manual
def test_screen_log_view(
    qtbot,
    acquire_vcan_devices: AppContainer, file_path: str,
) -> None:
    app = acquire_vcan_devices

    widget = FileLogViewPanel(app.log_vm())
    qtbot.addWidget(widget)

    widget.resize(860, 640)
    widget.show()

    # Simulate waiting 3 seconds before pressing Parse.
    qtbot.wait(2000)

    # vm.startParsing(file_path)
    # qtbot.waitUntil(
    #     lambda: vm.parser_done_event.is_set(),
    #     timeout=PARSE_TIMEOUT * 1000,
    # )

    # Manual inspection time.
    from PySide6.QtCore import QEventLoop
    loop = QEventLoop()
    widget.destroyed.connect(loop.quit)
    loop.exec()

    # Test returns here.
    # pytest-qt cleans up widget because of addWidget().
