from canapp.vm.container import AppContainer
from PySide6 import QtWidgets
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout
from typing import Optional, List
from PySide6.QtWidgets import (
    QWidget, QGroupBox, QVBoxLayout, QHBoxLayout,
    QLineEdit, QComboBox, QMessageBox, QLabel, QProgressBar, QStackedLayout, QPushButton, QSizePolicy, QToolBox,
    QApplication
    )
# from can_sdk.canlog_viewmodel import BasicFileLogContext
# from can_sdk.context_viewmodel import GeneralContextModel
# from can_sdk.observer import ObservableEvent

from canapp.ChannelsTab import ChannelsTab
from canapp.WorkspaceTab import WorkspaceDockContainer

class MainScreen(QtWidgets.QWidget):
    def __init__(self, app: AppContainer, parent=None):
        self.app = app
        super().__init__(parent)
        self.setMinimumSize(320, 240)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Expanding,
        )
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        """ NOT WORK FOR SET TABBAR EXAMPLE """
        # tabbar = QtWidgets.QTabBar(self)
        # self.tabs.setTabBar(tabbar)
        """ WORK EXAMPLE """
        self.tabs = QtWidgets.QTabWidget(self)
        tabbar = self.tabs.tabBar() 

        self.tabs.setDocumentMode(True) 
        self.tabs.setMovable(True) 
        self.tabs.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Expanding,
        )
        tabbar.setExpanding(True) 
        tabbar.setSizePolicy( 
            QtWidgets.QSizePolicy.Expanding, 
            QtWidgets.QSizePolicy.Preferred)
        main_layout.addWidget(self.tabs)

        widget_1 = ChannelsTab(self.app.channel_vm())

        widget = WorkspaceDockContainer(app)

        self.tabs.addTab(widget_1, "Connection")
        self.tabs.addTab(widget, "Analyzer")