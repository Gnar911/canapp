from __future__ import annotations

import logging
import pytest

from lw.logger_setup import LOG
from lw.test_event import wait
from cansrv.file_service import FileService
from canapp.vm.schedule_view_model import ScheduleViewModel

LOG.setLevel(logging.DEBUG)

pytest_plugins = ["fixture"]

TIMEOUT_QUERY_MS = 1000


@pytest.fixture
def app_vm() -> ScheduleViewModel:
    print("CS app_vm")
    return ScheduleViewModel()

