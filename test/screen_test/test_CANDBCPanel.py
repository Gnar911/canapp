from __future__ import annotations

import pytest

""" 20260729 BUG: One of big shortage of the VSCode is the auto refactor
        when rename a library or a variable
        Using F2 when rename a symbol
    """
from canapp.vm.dbc_view_model import DbcViewModel
from canapp.DBCPanel import CANDBCPanel
from cansrv.test.fixture import FileService
from canapp.vm.container import AppContainer
from PySide6.QtCore import (
    Qt,
    QModelIndex,
    QAbstractListModel,
    QEventLoop,
)
from lw.logger_setup import LOG
from pathlib import Path


@pytest.mark.parametrize(
    "dbc_path",
    [
        Path(
            "/home/gnar911/Desktop/20260122 APP WEBSITE - CAN ANALYZER 3.0 "
            "CBCM TOOL APP ARC/CAN_Analyzer_MVVM/Database/"
            "EEA10_CANFD_R00c_withADAS_Main.dbc"
        ),
    ],
)
@pytest.mark.manual
def test_candbc_panel_load_manual(
    qtbot,
    acquire_vcan_devices: AppContainer,
    dbc_path: Path,
) -> None:
    app = acquire_vcan_devices

    # 1: User open the application
    widget = CANDBCPanel(app.dbc_vm())
    widget.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
    qtbot.addWidget(widget)

    widget.resize(900, 640)
    widget.show()
    qtbot.wait(300)

    # 2: User press DBC button
    app.dbc_vm().wait_ready(lambda: app.dbc_vm().loadDBC(str(dbc_path)))

    # Wait until the user closes the widget (manual test): run a local event loop
    from PySide6.QtCore import QEventLoop
    loop = QEventLoop()
    widget.destroyed.connect(loop.quit)
    loop.exec()