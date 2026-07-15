import sys
from PySide6 import QtWidgets, QtCore, QtGui
from can_sdk.logger_setup import LOG, setup_logger
from can_sdk.dbc_manager import CANDBManager
from can_sdk.parser_manager import CANLogManager
from can_sdk.observer import ObservableEvent
import platform
import subprocess
from icon.icon import icontext
import base64
import tempfile
import sys
import os
from tkinter import PhotoImage
from numpy import pad
from can_sdk.logger_setup import LOG
from can_sdk.canlog_viewmodel import LogContextManager
from version import __version__, __author__, __build_date__
from WorkspaceContainer import WorkspaceContainer
from WorkspaceTab import WorkspaceTab
from ChannelsTab import ChannelsTab
from FileLogViewPanel import FileLogViewPanel
from MessageFilterPanel import MessageFilterPanel
from SignalFilterPanel import SignalFilterPanel
from FiltersPanel import ChannelFilterPanel
from can_license.license_model import LicenseModel
from can_license.activation_client import LicenseServerClient
from can_license.activate_dialog import ActivateLicenseDialog
from can_sdk.connection_viewmodel import CANConnectManager, CANChannelInfo
from can_sdk.hal.device_factory import CANDeviceType
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout

class CBCMSimulatorApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CBCM Simulator")
        self.resize(1200, 800)
        self.set_theme()
        # ---- backend (unchanged)
        self.candb = CANDBManager()
        self.canlog_model = CANLogManager()
        self.context_model = LogContextManager(self.canlog_model)
        self.connect_model = CANConnectManager(CANDeviceType.SOCKETCAN, self.context_model)

        # self.candb.load_database(
        # "/home/gnar911/Desktop/20260122 APP WEBSITE - CAN ANALYZER 3.0 CBCM TOOL APP ARC/CAN_Analyzer_MVVM/Database/EEA10_CANFD_R00c_withADAS_Main.dbc")

        self.win = QWidget()
        # self.layout = QVBoxLayout(self.win)
        self.create_view()
        # tree = FileLogViewPanel(parent=self, candb=self.candb, log_ctx_mgr=self.context_model)
        # layout.addWidget(tree)
        # self.win.resize(800, 500)
        self.win.show()
        #self._open_filter_windows()
        print("FileLogViewPanel thread:", QtCore.QThread.currentThread())
        print("GUI thread:", QtWidgets.QApplication.instance().thread())

    def create_view(self):
        self.mother_tab = ChannelsTab(model=self.connect_model)
        self.host = WorkspaceContainer(parent=self.win,
                                       model=self.connect_model, 
                                       workspace_factory=self.workspace_tab_factory,
                                       mother_widget=self.mother_tab)
        self.setCentralWidget(self.host)

    def workspace_tab_factory(self, parent, name):
        return QWidget(parent)
        #return WorkspaceTab(parent, name, self.connect_model)

    def closeEvent(self, event: QtGui.QCloseEvent):
        # Put your shutdown logic here (stop threads, close CAN, et4dc9e9c6-ea3a-4dac-b993-c45a2eec92c5|ADAS Channelc.)
        event.accept()

    
    def set_theme(self):
        # Minimal “theme”: you can replace with a real Qt stylesheet
        self.setStyleSheet("""
            QMainWindow { background: #1e1e1e; }
            QLabel { color: #dddddd; }
            QTabWidget::pane { border: 1px solid #333; }
            QTabBar::tab { padding: 6px 10px; }
        """)


# ---------------------------
# Entry point
# ---------------------------
def main():
    setup_logger(env="DEV", backup_count=30)
    app = QtWidgets.QApplication(sys.argv)
    win = CBCMSimulatorApp()
    # win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()