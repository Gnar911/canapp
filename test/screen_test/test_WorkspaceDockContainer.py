from __future__ import annotations

import pytest
from PySide6 import QtWidgets
import PySide6QtAds as QtAds

from canapp.WorkspaceTab import WorkspaceDockContainer
from canapp.vm.dbc_view_model import DbcViewModel
from canapp.vm.log_viewmodel import LogViewModel
from canapp.vm.record_viewmodel import RecordViewModel
from canapp.vm.replay_view_model import ReplayViewModel
from canapp.vm.schedule_view_model import ScheduleViewModel


@pytest.mark.manual
def test_workspace_dock_container_builds_screen_manual(qtbot) -> None:
    central = QtWidgets.QPlainTextEdit()
    central.setPlainText("center")

    widget = WorkspaceDockContainer(None, central)
    qtbot.addWidget(widget)

    widget.resize(1200, 800)
    widget.show()
    qtbot.wait(300)

    assert widget.dock_manager is not None
    assert widget.central_dock_widget is not None
    assert widget.central_dock_area is not None

    assert isinstance(widget.dbc_vm, DbcViewModel)
    assert isinstance(widget.file_log_vm, LogViewModel)
    assert isinstance(widget.monitor_vm, RecordViewModel)
    assert isinstance(widget.replay_vm, ReplayViewModel)
    assert isinstance(widget.send_vm, ScheduleViewModel)

    dbc_dock = widget.findChild(QtAds.CDockWidget, "Dock_DBC")
    file_log_dock = widget.findChild(QtAds.CDockWidget, "Dock_FileLog")
    monitor_dock = widget.findChild(QtAds.CDockWidget, "Dock_Monitor")
    replay_dock = widget.findChild(QtAds.CDockWidget, "Dock_Replay")
    send_dock = widget.findChild(QtAds.CDockWidget, "Dock_SendMessage")

    assert dbc_dock is not None
    assert file_log_dock is not None
    assert monitor_dock is not None
    assert replay_dock is not None
    assert send_dock is not None
