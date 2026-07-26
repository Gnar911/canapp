from __future__ import annotations

import pytest

from lw.test_event import wait
from canapp.vm.dbc_view_model import DbcViewModel
from canapp.DBCPanel import CANDBCPanel
from cansrv.test.fixture import FileService

pytest_plugins = ["fixture"]

TIMEOUT_STATUS = 3.0
TIMEOUT_QUERY_MS = 30


@pytest.fixture
def app_vm() -> DbcViewModel:
    print("CS app_vm")
    return DbcViewModel()


@pytest.mark.parametrize(
    "dbc_path",
    [
        "/home/gnar911/Desktop/20260516_JOBS_INSPECTOR/project/canapp/src/canapp/widgets/db_temp.dbc",
    ],
)
@pytest.mark.manual
def test_candbc_panel_load_manual(
    qtbot,
    file_service: tuple[FileService, DbcViewModel],
    dbc_path: str,
) -> None:
    _, vm = file_service

    widget = CANDBCPanel(None, vm)
    qtbot.addWidget(widget)

    widget.resize(900, 640)
    widget.show()
    qtbot.wait(300)

    vm.loadDBC(dbc_path)
    assert vm.dbc_loaded_event.wait(TIMEOUT_STATUS)
