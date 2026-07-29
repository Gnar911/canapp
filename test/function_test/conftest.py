import logging
import pytest
from dependency_injector import providers
from typing import Generator
from canapp.container import AppContainer
from lw.logger_setup import LOG

LOG.setLevel(logging.DEBUG)

pytest_plugins = ["fixture"]

@pytest.fixture
def container():
    c = AppContainer()
    """ 20260729 BUG:
        1. Singleton is not created instance until first call (), it only passing the providers 
        -> the viewmodel is not created after the fixture setup vcan, it only calls channel_vm()
    """
    c.can_service().start()
    c.file_service().start()

    c.channel_vm()
    c.schedule_vm()
    c.record_vm()
    c.log_vm()
    c.dbc_vm()
    c.replay_vm()

    yield c

    c.can_service().stop()
    c.file_service().stop()
    c.channel_vm().reset()
    c.schedule_vm().reset()
    c.record_vm().reset()
    c.log_vm().reset()
    c.dbc_vm().reset()
    c.replay_vm().reset()