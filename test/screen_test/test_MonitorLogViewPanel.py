from __future__ import annotations

import pytest
from PySide6.QtCore import QCoreApplication

# from lw.test_event import wait
from canapp.vm.record_viewmodel import RecordViewModel
from canapp.MonitorLogViewPanel import MonitorLogViewPanel
from cansrv.test.fixture import FileService
from canapp.vm.container import AppContainer
from lw.logger_setup import LOG
from lw.test_event import wait_evaluation
from cansrv.file_service import FileService, LogId
from canapp.vm.log_viewmodel import LogViewModel
from canapp.vm.record_viewmodel import (
    RecordViewModel,
)
from canapp.vm.schedule_view_model import (
    ScheduleViewModel, CANPlayEntry, LogRecord
)
from canapp.vm.replay_view_model import (
    ReplayViewModel,
)
from canapp.vm.container import AppContainer

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtCore import (
    Qt,
    QModelIndex,
    QAbstractListModel,
    QEventLoop,
)
from canapp.MonitorLogViewPanel import MonitorLogViewPanel


class _FakeRecordVM(QObject):
    progressChanged = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._total_rows = 0

    @property
    def totalRows(self) -> int:
        return int(self._total_rows)

    def add_rows(self, count: int) -> None:
        self._total_rows += int(count)
        self.progressChanged.emit()


def test_monitor_plain_tree_smoke(qtbot) -> None:
    vm = _FakeRecordVM()
    widget = MonitorLogViewPanel(vm)
    qtbot.addWidget(widget)

    widget.resize(640, 360)
    widget.show()

    model = widget.model_
    assert model.rowCount() == 0

    vm.add_rows(3)
    qtbot.wait(50)

    assert model.rowCount() == 3

    i0 = model.index(0, model.COL_LOG_MESSAGES)
    i1 = model.index(1, model.COL_LOG_MESSAGES)
    assert i0.isValid()
    assert i1.isValid()

    assert model.data(i0, Qt.ItemDataRole.DisplayRole) == "Row 1"
    assert model.data(i1, Qt.ItemDataRole.DisplayRole) == "Row 2"

    vm.add_rows(2)
    qtbot.wait(50)

    assert model.rowCount() == 5

    i4 = model.index(4, model.COL_LOG_MESSAGES)
    assert i4.isValid()
    assert model.data(i4, Qt.ItemDataRole.DisplayRole) == "Row 5"

    qtbot.wait(5000)



@pytest.mark.manual
def test_monitor_log_panel_record_flow_manual(
    qtbot,
    acquire_vcan_devices: AppContainer,
) -> None:
    app = acquire_vcan_devices

    widget = MonitorLogViewPanel(app.record_vm())
    qtbot.addWidget(widget)

    widget.resize(860, 640)
    widget.show()
    qtbot.wait(300)

    # 1: User create the entry from treeview on channel panel
    device = app.channel_vm().acquired_devices[0]
    parsed = LogRecord()
    parsed.can_id = 0x123
    parsed.channel = "can0"
    parsed.data = bytes([0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88])
    parsed.data_len = 8
    parsed.direction = 1          # RX or TX depending on your enum
    parsed.timestamp = 1.234567   # seconds
    entry = CANPlayEntry(device_info=device, entry=parsed, initial_periodic_second=0.5)

    # 2: User press send button on send panel
    app.schedule_vm().wait_ready(lambda: app.schedule_vm().sendMsgLoop(entry))
    
    # Keep the Qt event loop alive so progressChanged -> model insertions can run.
    qtbot.wait(3_000)
    display_entry = wait_evaluation(lambda: app.record_vm().entry, max_ms=16.7, name= "entry eval")
    assert display_entry is not None

    #qtbot.wait(3_000)
    # 7: User back and press pause send
    #app.schedule_vm().wait_ready(lambda: app.schedule_vm().pauseMsg(entry))

    #8: Auto release device #TODO need to add
    #app.channel_vm().wait_ready(lambda: app.channel_vm().releaseDevice(device))


    # Wait until the user closes the widget (manual test): run a local event loop
    loop = QEventLoop()
    widget.destroyed.connect(loop.quit)
    loop.exec()