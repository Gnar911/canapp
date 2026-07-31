from __future__ import annotations

import pytest

from canapp.vm.replay_view_model import ReplayViewModel
from canapp.CustomReplayPanel import CustomReplayPanel
from cansrv.test.fixture import CANService
from canapp.vm.container import AppContainer

@pytest.mark.manual
def test_custom_replay_panel_controls_manual(
    qtbot,
    acquire_vcan_devices: AppContainer,
) -> None:
    app = acquire_vcan_devices

    # 1: User open the application
    widget = CustomReplayPanel(app.replay_vm())
    qtbot.addWidget(widget)

    widget.resize(920, 680)
    widget.show()
    qtbot.wait(300)

    from PySide6.QtCore import QEventLoop
    loop = QEventLoop()
    widget.destroyed.connect(loop.quit)
    loop.exec()