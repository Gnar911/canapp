from __future__ import annotations

import pytest

from canapp.vm.schedule_view_model import ScheduleViewModel
from canapp.CustomSendMessagePanel import CustomSendMessagePanel
from cansrv.test.fixture import CANService
from canapp.vm.container import AppContainer

def test_custom_send_panel_clear_manual(
    qtbot,
    acquire_vcan_devices: AppContainer,
) -> None:
    app = acquire_vcan_devices

    widget = CustomSendMessagePanel(app.schedule_vm())
    qtbot.addWidget(widget)

    widget.resize(900, 640)
    widget.show()
    qtbot.wait(300)

    from PySide6.QtCore import QEventLoop
    loop = QEventLoop()
    widget.destroyed.connect(loop.quit)
    loop.exec()