import sys
from PySide6 import QtWidgets, QtCore, QtGui
from lw.logger_setup import LOG, setup_logger
# from can_sdk.dbc_manager import CANDBManager
# from can_sdk.parser_manager import CANLogManager
# from can_sdk.observer import ObservableEvent
from icon.icon import icontext
import base64
import tempfile
import sys
from tkinter import PhotoImage
from numpy import pad
#TODO: Develop lisence model
"""
from can_license.license_model import LicenseModel
from can_license.activation_client import LicenseServerClient
from can_license.activate_dialog import ActivateLicenseDialog
"""
# from can_sdk.connection_viewmodel import CANConnectManager, CANChannelInfo
from canapp.vm.container import AppContainer
from canapp.MainScreen import MainScreen

class CBCMSimulatorApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Vucan")
        self.resize(1200, 800)
        self.set_theme()

        app = AppContainer()

        self.main_screen = MainScreen(app)
        self.setCentralWidget(self.main_screen)

        print("MainScreen thread:", self.main_screen.thread())
        print("MainWindow thread:", self.thread())
        print("GUI thread:", QtWidgets.QApplication.instance().thread())

        self.show()

    # def create_view(self):
    #     self.mother_tab = ChannelsTab(model=self.connect_model)
    #     self.host = WorkspaceContainer(parent=self.win,
    #                                    model=self.connect_model, 
    #                                    workspace_factory=self.workspace_tab_factory,
    #                                    mother_widget=self.mother_tab)
    #     self.setCentralWidget(self.host)

    # def workspace_tab_factory(self, parent, name):
    #     return QWidget(parent)
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