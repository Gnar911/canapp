from __future__ import annotations

import pytest

# from lw.test_event import wait
from canapp.vm.log_viewmodel import LogViewModel
from canapp.FiltersPanel import FiltersPanel
from cansrv.test.fixture import FileService
from canapp.vm.container import AppContainer

# pytest_plugins = ["fixture"]

# TIMEOUT_STATUS = 3.0
# TIMEOUT_QUERY_MS = 30
# PARSE_TIMEOUT = 15.0
# TEST_ASC_PATH = "/home/gnar911/Desktop/2025-02-11_11-14-53_仕様情報切替 1.asc"


# @pytest.fixture
# def app_vm() -> LogViewModel:
#     print("CS app_vm")
#     return LogViewModel()


@pytest.mark.parametrize(
    "file_path",
    [
        "/home/gnar911/Desktop/2025-02-11_11-14-53_仕様情報切替 1.asc",
    ],
)
@pytest.mark.manual
def test_filters_panel_build_and_refresh_manual(
    qtbot,
    acquire_vcan_devices: AppContainer,
    file_path: str,
) -> None:
    app = acquire_vcan_devices

    widget = FiltersPanel(app.log_vm())
    qtbot.addWidget(widget)

    widget.resize(900, 700)
    widget.show()
    qtbot.wait(300)

    from PySide6.QtCore import QEventLoop
    loop = QEventLoop()
    widget.destroyed.connect(loop.quit)
    loop.exec()
