from __future__ import annotations

import logging
import pytest

from lw.logger_setup import LOG
from lw.test_event import wait
from cansrv.file_service import FileService
from canapp.vm.dbc_view_model import DbcViewModel

LOG.setLevel(logging.DEBUG)

pytest_plugins = ["fixture"]

TIMEOUT_LOADPAGE_MS = 15000
TIMEOUT = 0.5

@pytest.fixture
def app_vm() -> DbcViewModel:
    print("CS app_vm")
    return DbcViewModel()

@pytest.mark.parametrize(
    "dbc_file_path",
    [
        "/home/gnar911/Desktop/20260122 APP WEBSITE - CAN ANALYZER 3.0 CBCM TOOL APP ARC/CAN_Analyzer_MVVM/Database/"
        "EEA10_CANFD_R00c_withADAS_Main.dbc",
    ],
)
def test_06_parse_dbc(
    file_service: tuple[FileService, DbcViewModel],
    dbc_file_path: str,
) -> None:
    _, vm = file_service

    wait(lambda: vm.loadDBC(dbc_file_path), max_ms=TIMEOUT_LOADPAGE_MS)
    assert vm.dbc_loaded_event.wait(TIMEOUT*2)
    assert vm.dbc_id is not None

    assert vm.hasDbc is True
    assert vm.dbcNum >= 1
    assert vm.dbcMessagesCount > 0