from __future__ import annotations

import pytest

# from lw.test_event import wait
from canapp.vm.channel_view_model import ChannelViewModel
from canapp.ChannelsTab import ChannelsTab
from cansrv.test.fixture import CANService
from canapp.vm.container import AppContainer
from PySide6.QtCore import (
    Qt,
    QModelIndex,
    QAbstractListModel,
)

@pytest.mark.manual
def test_channels_tab_smoke_manual(
    qtbot,
    setup_vcan_devices: tuple[AppContainer, int],
) -> None:
    app, _ = setup_vcan_devices

    widget = ChannelsTab(app.channel_vm())
    widget.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
    qtbot.addWidget(widget)

    widget.resize(780, 560)
    widget.show()

    qtbot.wait(200)

    device = app.channel_vm().available_devices[0]
    app.channel_vm().wait_ready(lambda: app.channel_vm().acquireDevice(device))
    qtbot.wait(30_000)

    app.channel_vm().wait_ready(lambda: app.channel_vm().releaseDevice(device))
    from PySide6.QtCore import QEventLoop
    loop = QEventLoop()
    widget.destroyed.connect(loop.quit)
    loop.exec()