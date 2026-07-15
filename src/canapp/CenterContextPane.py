
from PySide6 import QtWidgets
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout
from typing import Optional, List
from PySide6.QtWidgets import (
    QWidget, QGroupBox, QVBoxLayout, QHBoxLayout,
    QLineEdit, QComboBox, QMessageBox, QLabel, QProgressBar, QStackedLayout, QPushButton, QSizePolicy, QToolBox,
    QApplication
)
from can_sdk.canlog_viewmodel import BasicFileLogContext
from can_sdk.context_viewmodel import GeneralContextModel
from can_sdk.observer import ObservableEvent

class CenterContextManagerViewModel:
    def __init__(self, parent=None, model: GeneralContextModel = None):
        super().__init__()
        self._model = model
        self._widget_ctx_map: dict[QtWidgets.QWidget, Optional[BasicFileLogContext]] = {}
        self.event_on_target_context_changed = ObservableEvent(BasicFileLogContext)

    def bind_context(self, panel: QtWidgets.QWidget, ctx: Optional[BasicFileLogContext] = None):
        self._widget_ctx_map[panel] = ctx
        self._model.add_context(ctx)

    def unbind_context(self, panel: QtWidgets.QWidget):
        ctx = self._widget_ctx_map.pop(panel, None)
        self._model.remove_context(ctx)

    def on_tab_changed(self, panel: QtWidgets.QWidget):
        ctx = self._widget_ctx_map.get(panel)
        if not self._model.set_current_context(ctx):
            return

        self.event_on_target_context_changed.notify(ctx)

    def get_current_context(self) -> Optional[BasicFileLogContext]:
        return self._model.get_current_context()

    def get_contexts(self) -> list[BasicFileLogContext]:
        return self._model.get_contexts()

        
class CenterContextPane(QtWidgets.QWidget):
    def __init__(self, parent=None, model: GeneralContextModel = None):
        self.context_vm = CenterContextManagerViewModel(model=model)
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
            QtWidgets.QSizePolicy.Preferred )
        main_layout.addWidget(self.tabs)

        self.tabs.currentChanged.connect(self._on_tab_changed)
        self.tabs.tabCloseRequested.connect(self._on_tab_closed)

    # -----------------------------------
    # Add panel + context
    # -----------------------------------
    def add_panel(
        self,
        widget: QtWidgets.QWidget,
        title: str,
        model: Optional[BasicFileLogContext] = None
    ):
        widget.setWindowTitle(title)

        self.tabs.addTab(widget, title)

        # Bind externally-created context
        self.context_vm.bind_context(widget, model)

        # Activate immediately if first tab
        if self.tabs.count() == 1:
            self.context_vm.on_tab_changed(widget)

    # -----------------------------------
    # Tab changed
    # -----------------------------------
    def _on_tab_changed(self, index: int):
        panel = self.tabs.widget(index)
        if panel:
            self.context_vm.on_tab_changed(panel)

    # -----------------------------------
    # Tab closed
    # -----------------------------------
    def _on_tab_closed(self, index: int):
        panel = self.tabs.widget(index)
        if panel:
            self.context_vm.unbind_context(panel)
        self.tabs.removeTab(index)

if __name__ == "__main__":
    import sys
    from pathlib import Path
    from PySide6.QtWidgets import QApplication, QLabel
    from can_sdk.logger_setup import setup_logger
    from can_sdk.dbc_manager import CANDBManager
    from can_sdk.canlog_viewmodel import LogContextManager
    from can_sdk.parser_manager import CANLogManager

    setup_logger(env="DEV", backup_count=30)

    import subprocess
    vcan_script = Path(__file__).resolve().parents[2] / "packages" / "can_sdk" / "src" / "can_sdk" / "hal" / "socket" / "vcan0_up.sh"
    if vcan_script.exists():
        subprocess.run(["bash", str(vcan_script)], check=False)

    app = QApplication(sys.argv)

    model = GeneralContextModel()
    pane = CenterContextPane(model=model)
    pane.setWindowTitle("CenterContextPane Test")
    pane.resize(1200, 700)

    # Shared managers
    log_ctx_mgr = LogContextManager(CLM=CANLogManager())
    dbc_mgr = CANDBManager()

    dbc_path = (
        Path(__file__).resolve().parents[2]
        / "Database"
        / "EEA10_CANFD_R00c_withADAS_Main.dbc"
    )
    if dbc_path.exists():
        dbc_mgr.load_database(str(dbc_path))

    # Real panel 1: FileLogViewPanel
    from FileLogViewPanel import FileLogViewPanel
    panel1: QWidget = FileLogViewPanel(parent=pane, candb=dbc_mgr, log_ctx_mgr=log_ctx_mgr)

    # Real panel 2: MonitorLogViewPanel (requires acquired CAN channel)
    monitor_panel: QWidget
    acquired_handle = None
    conn_mgr = None
    from can_sdk.connection_viewmodel import CANConnectManager, CANDeviceType
    from MonitorLogViewPanel import MonitorLogViewPanel

    conn_mgr = CANConnectManager(CANDeviceType.SOCKETCAN)
    conn_mgr.start_scan()
    # first_handle = next(iter(conn_mgr.available_channels.keys()))
    # if conn_mgr.acquire(first_handle):
    # acquired_handle = first_handle
    monitor_panel = MonitorLogViewPanel(
        parent=pane,
        candb=dbc_mgr,
        cnt_model=conn_mgr,
        handle=None,
    )

    pane.add_panel(panel1, "File Log")
    pane.add_panel(monitor_panel, "Monitor")

    # Button to acquire first channel and set handle on MonitorLogViewPanel
    acquire_btn = QPushButton("Acquire First Channel")

    def on_acquire_first_channel():
        channels = conn_mgr.available_channels
        if not channels:
            QMessageBox.warning(pane, "No Channel", "No available channels found.")
            return
        first_handle = next(iter(channels.keys()))
        if conn_mgr.acquire(first_handle):
            monitor_panel.set_handle(first_handle)
            acquire_btn.setText(f"Acquired: {first_handle}")
            acquire_btn.setEnabled(False)
        else:
            QMessageBox.warning(pane, "Acquire Failed", f"Failed to acquire channel: {first_handle}")

    acquire_btn.clicked.connect(on_acquire_first_channel)
    pane.tabs.setCornerWidget(acquire_btn, Qt.TopRightCorner)

    pane.show()
    sys.exit(app.exec())