from __future__ import annotations

import pytest

from lw.test_event import wait
from canapp.vm.log_viewmodel import LogViewModel
from canapp.FiltersPanel import FiltersPanel
from cansrv.test.fixture import FileService

pytest_plugins = ["fixture"]

TIMEOUT_STATUS = 3.0
TIMEOUT_QUERY_MS = 30
PARSE_TIMEOUT = 15.0
TEST_ASC_PATH = "/home/gnar911/Desktop/2025-02-11_11-14-53_仕様情報切替 1.asc"


@pytest.fixture
def app_vm() -> LogViewModel:
    print("CS app_vm")
    return LogViewModel()


@pytest.mark.parametrize("file_path", [TEST_ASC_PATH])
@pytest.mark.manual
def test_filters_panel_build_and_refresh_manual(
    qtbot,
    file_service: tuple[FileService, LogViewModel],
    file_path: str,
) -> None:
    _, vm = file_service

    widget = FiltersPanel(None, vm)
    qtbot.addWidget(widget)

    widget.resize(900, 700)
    widget.show()
    qtbot.wait(300)

    vm.startParsing(file_path)
    assert vm.parser_done_event.wait(PARSE_TIMEOUT)

    assert wait(lambda: vm.totalLines, max_ms=TIMEOUT_QUERY_MS) > 0

    vm.commonStateChanged.emit()
    qtbot.wait(100)

    assert widget.section_message is not None
    assert widget.section_channel is not None
    assert widget.section_dir is not None

    assert widget.message_filter.model() is widget.message_proxy
    assert widget.channel_filter.model() is widget.channel_proxy

    assert widget.message_proxy.rowCount() >= 0
    assert widget.channel_proxy.rowCount() >= 0
