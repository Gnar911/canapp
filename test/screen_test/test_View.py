from __future__ import annotations

import pytest
from PySide6.QtCore import (
    Qt,
    QModelIndex,
    QAbstractListModel,
)
import PySide6QtAds as QtAds
from pathlib import Path

from cansrv.module.fs_core import LogRecord
from canapp.vm.schedule_view_model import CANPlayEntry
from canapp.WorkspaceTab import WorkspaceDockContainer
from canapp.vm.container import AppContainer
from canapp.MainScreen import MainScreen
from canapp.vm.log_viewmodel import MsgFilter, NoFilter


""" BUG: 
QLayout: Attempting to add QLayout "" to FileLogViewPanel "", which already has a layout
QLayout: Attempting to add QLayout "" to CustomSendMessagePanel "", which already has a layout
"""
@pytest.mark.manual
def test_workspace_dock_container_builds_screen_manual(
    qtbot,
    acquire_vcan_devices: AppContainer,
    ) -> None:
    app = acquire_vcan_devices

    widget = WorkspaceDockContainer(app)
    qtbot.addWidget(widget)

    widget.resize(1200, 800)
    widget.show()
    qtbot.wait(300)

    qtbot.wait(10**9)

@pytest.mark.parametrize(
    "dbc_file_path",
    [
        Path(
            "/home/gnar911/Desktop/20260122 APP WEBSITE - CAN ANALYZER 3.0 "
            "CBCM TOOL APP ARC/CAN_Analyzer_MVVM/Database/"
            "EEA10_CANFD_R00c_withADAS_Main.dbc"
        ),
    ],
)
@pytest.mark.parametrize(
    "file_path",
    [
        Path("/home/gnar911/Desktop/2025-02-11_11-14-53_仕様情報切替 1.asc"),
    ],
)
@pytest.mark.manual
def test_main_screen(
    qtbot,
    setup_vcan_devices: tuple[AppContainer, int],
    dbc_file_path: Path, file_path: Path
    ) -> None:
    app, num = setup_vcan_devices

    widget = MainScreen(app)
    widget.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
    qtbot.addWidget(widget)

    widget.resize(1200, 800)
    widget.show()

    qtbot.wait(3000)

    # 0. Lock a channel
    device = app.channel_vm().available_devices[0]
    app.channel_vm().wait_ready(lambda: app.channel_vm().acquireDevice(device))

    # 1. Load DBC
    app.dbc_vm().wait_ready(lambda: app.dbc_vm().loadDBC(dbc_file_path))

    qtbot.wait(3000)
    # 2. Load Log
    app.log_vm().wait_ready(lambda: app.log_vm().startParsing(file_path))

    qtbot.wait(3000)

    # 3. Send a message loop 
    assert device is not None
    parsed = LogRecord()
    parsed.can_id = 0x123
    parsed.channel = "can0"
    parsed.data = bytes([0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88])
    parsed.data_len = 8
    parsed.direction = 1          # RX or TX depending on your enum
    parsed.timestamp = 1.234567   # seconds
    entry = CANPlayEntry(device_info=device, entry=parsed, initial_periodic_second=0.5)
    app.schedule_vm().editing_entry = entry
    app.schedule_vm().wait_ready(lambda: app.schedule_vm().sendMsgLoop(entry))

    qtbot.wait(5000)

    app.schedule_vm().wait_ready(lambda: app.schedule_vm().pauseMsg(entry))
    qtbot.wait(3000)

    # 4. Replay a log file 
    app.replay_vm().wait_ready(lambda: app.replay_vm().startReplay())
    qtbot.wait(5000)
    #app.replay_vm().wait_ready(lambda: app.replay_vm().stopReplay())

    # 5. Filter message
    app.log_vm().messageFilter = MsgFilter(0x48E)
    qtbot.wait(5000)

    app.log_vm().messageFilter = NoFilter()
    qtbot.wait(3000)

    # 6. Close current Log file
    app.log_vm().closeLog()

    from PySide6.QtCore import QEventLoop
    loop = QEventLoop()
    widget.destroyed.connect(loop.quit)
    loop.exec()

    # 20260731 NOTE: This is the end of the course, the app will push to maintain state

    """
    pytest -q test/screen_test/test_View.py::test_main_screen -o log_cli=true -o log_cli_level=DEBUG -s

    pytest -q test/screen_test/test_MonitorLogViewPanel.py::test_monitor_log_panel_record_flow_manual -o log_cli=true -o log_cli_level=DEBUG -s

    pytest -q test/screen_test/test_View.py::test_main_screen -o log_cli=true -o log_cli_level=DEBUG -s

    pytest -q test/screen_test/test_CANDBCPanel.py::test_candbc_panel_load_manual -o log_cli=true -o log_cli_level=DEBUG -s    
    """