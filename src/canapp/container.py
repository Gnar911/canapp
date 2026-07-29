from __future__ import annotations

from dependency_injector import containers, providers

from lw.qt.QtMainThreadDispatcher import QtMainThreadDispatcher
from cansrv.file_service import FileService
from cansrv.can_srv import CANService
from cansrv.test.fixture import ServiceContainer

from canapp.vm.channel_view_model import ChannelViewModel
from canapp.vm.dbc_view_model import DbcViewModel
from canapp.vm.log_viewmodel import LogViewModel
from canapp.vm.record_viewmodel import RecordViewModel
from canapp.vm.replay_view_model import ReplayViewModel
from canapp.vm.schedule_view_model import ScheduleViewModel


class AppContainer(ServiceContainer):
    dispatcher = providers.Singleton(QtMainThreadDispatcher)

    file_service = providers.Singleton(
        FileService,
        main_dispatcher=dispatcher,
    )

    can_service = providers.Singleton(CANService)

    """ NOTE: Using Factory if many instances, using Singleton if only one"""
    """ NOTE: Factory returns a new VM each call.
        can_service fixture gets one VM instance and subscribes it.
        Later, setup_vcan_devices gets app_vm again, which can be a different VM instance.
        """
    log_vm = providers.Singleton(LogViewModel, can_service=can_service, file_service=file_service)
    schedule_vm = providers.Singleton(ScheduleViewModel, can_service=can_service, file_service=file_service)
    replay_vm = providers.Singleton(ReplayViewModel, can_srv=can_service, file_srv = file_service)
    record_vm = providers.Singleton(RecordViewModel, file_srv=file_service, can_srv = can_service)
    channel_vm = providers.Singleton(ChannelViewModel, can_service=can_service)
    dbc_vm = providers.Singleton(DbcViewModel, can_service=can_service, file_service=file_service,)

    # Optional bridge for existing tests that expect container.app_vm to exist.
    #app_vm = providers.Dependency(instance_of=object)