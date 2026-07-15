from PySide6 import QtWidgets, QtCore
from can_sdk.connection_viewmodel import CANConnectManager, CANChannelInfo, LogContextViewModel
import sys
import os
os.environ["QT_QPA_PLATFORM"] = "xcb"
from PySide6 import QtCore, QtWidgets
from PySide6.QtCore import Qt, QSignalBlocker
from PySide6.QtWidgets import (QPlainTextEdit, QInputDialog, QToolBar, QVBoxLayout,)
import PySide6QtAds as QtAds

"""
20260207: FUCK QT
Top / Bottom docking still works because it does NOT require a central widget.
Left / Right docking DOES require a central widget.
This asymmetry is by design in Qt.
"""
class ConnectionBar(QtWidgets.QWidget):
    def __init__(self, parent=None, model: CANConnectManager = None):
        super().__init__(parent)
        self.my_model = model
        self.create_ui()
        if self.my_model:
            self.my_model.event_on_channels_state_changed.subscribe(
                self.on_event_channels_scan
            )

    def create_ui(self):
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)

        # --- labels
        layout.addWidget(QtWidgets.QLabel("Channel:"))
        self.channel_label = QtWidgets.QLabel("—")
        self.channel_label.setMinimumWidth(80)
        layout.addWidget(self.channel_label)

        layout.addSpacing(12)

        layout.addWidget(QtWidgets.QLabel("Vendor:"))
        self.vendor_label = QtWidgets.QLabel("—")
        self.vendor_label.setMinimumWidth(100)
        layout.addWidget(self.vendor_label)

        layout.addSpacing(12)

        layout.addWidget(QtWidgets.QLabel("Status:"))
        self.status_label = QtWidgets.QLabel("Disconnected")
        self.status_label.setMinimumWidth(120)
        layout.addWidget(self.status_label)

        # spacer
        layout.addStretch(1)

        # disconnect button (UI only)
        self.disconnect_btn = QtWidgets.QPushButton("Disconnect")
        layout.addWidget(self.disconnect_btn)

    def set_state(self, channel_name: str, vendor: str, connected: bool):
        if not hasattr(self, "vendor_label"):
            return

        self.channel_label.setText(channel_name or "—")
        self.vendor_label.setText(vendor or "—")

        if connected:
            self.status_label.setText("Connected")
            self.status_label.setStyleSheet("color: green;")
        else:
            self.status_label.setText("Disconnected")
            self.status_label.setStyleSheet("color: red;")

    # ---------------------------------------------------------
    # Backend event
    # ---------------------------------------------------------
    def on_event_channels_scan(self):
        """
        Update connection bar state here when model changes.
        """
        channels = self.my_model.all_channels.values()
        active = next(
            (
                ch
                for ch in channels
                if getattr(getattr(ch, "state", None), "name", "") == "ACQUIRED"
            ),
            None,
        )

        if active:
            vendor = getattr(
                getattr(active.config, "vendor", None),
                "name",
                "—",
            )
            self.set_state(
                channel_name=active.name,
                vendor=vendor,
                connected=True,
            )
        else:
            self.set_state("—", "—", False)


class WorkspaceTab(QtWidgets.QWidget):
    def __init__(self, master, workspace_name: str, model=None, central_widget: QtWidgets.QWidget = None):
        super().__init__(master)
        self.workspace_name = workspace_name
        self.model = model
        self.central_widget = central_widget
        self._build_ui()

    # ---------------------------------------------------------
    # UI
    # ---------------------------------------------------------
    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # connection bar
        self.connection_bar = ConnectionBar(self, model=self.model)
        layout.addWidget(self.connection_bar)

        # --- empty workspace placeholder
        self.dock_container = WorkspaceDockContainer(self, central_widget=self.central_widget)
        layout.addWidget(self.dock_container, stretch=1)

        #self._add_test_docks()

    def _add_test_docks(self):
        # Dock 1 - Left
        w1 = QtWidgets.QWidget()
        w1.setStyleSheet("background: #2b2b2b;")
        self.dock_container.add_dock_widget(
            "Dock A",
            w1,
            QtAds.DockWidgetArea.LeftDockWidgetArea,
            self.dock_container.central_dock_area,
        )

        # Dock 2 - Right
        w2 = QtWidgets.QWidget()
        w2.setStyleSheet("background: #333333;")
        self.dock_container.add_dock_widget(
            "Dock B",
            w2,
            QtAds.DockWidgetArea.RightDockWidgetArea,
            self.dock_container.central_dock_area,
        )

        # Dock 3 - Bottom
        w3 = QtWidgets.QWidget()
        w3.setStyleSheet("background: #3b3b3b;")
        self.dock_container.add_dock_widget(
            "Dock C",
            w3,
            QtAds.DockWidgetArea.BottomDockWidgetArea,
            self.dock_container.central_dock_area,
        )

        # Dock 4 - Tabbed with Dock C
        w4 = QtWidgets.QWidget()
        w4.setStyleSheet("background: #444444;")
        self.dock_container.add_dock_widget(
            "Dock D",
            w4,
            as_tab=True,
            relative_to_area=self.dock_container.central_dock_area,
        )

class WorkspaceDockContainer(QtWidgets.QWidget):
    """
    A QWidget that embeds a QtAds CDockManager.
    This is the 'second part' of WorkspaceTab.
    """
    def __init__(self, parent=None, central_widget: QtWidgets.QWidget = None):
        super().__init__(parent)

        # ---- layout: optional toolbar + dock manager ----
        self._toolbar = QToolBar(self)
        self._toolbar.setMovable(False)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._toolbar)

        # 4️⃣ NOW it is safe to configure the dock manager
        QtAds.CDockManager.setConfigFlag(
            QtAds.CDockManager.OpaqueSplitterResize, True
        )
        QtAds.CDockManager.setConfigFlag(
            QtAds.CDockManager.XmlCompressionEnabled, False
        )
        QtAds.CDockManager.setConfigFlag(
            QtAds.CDockManager.FocusHighlighting, True
        )

       # 2️⃣ Create dock manager (NO config calls yet)
        self.dock_manager = QtAds.CDockManager(self)

        # Set central widget
        text_edit = central_widget
        if text_edit is None:
            text_edit = QPlainTextEdit()
            text_edit.setPlaceholderText("This is the central editor. Enter your text here.")
        self.central_dock_widget = QtAds.CDockWidget(
            self.dock_manager,
            "CenterContextPane",
            self.dock_manager,
        )
        self.central_dock_widget.setWidget(text_edit)
        self.central_dock_area = self.dock_manager.setCentralWidget(self.central_dock_widget)
        self.central_dock_area.setAllowedAreas(QtAds.DockWidgetArea.OuterDockAreas)

        # 5️⃣ Add dock manager to layout LAST
        layout.addWidget(self.dock_manager)


    def _save_perspective(self):
        perspective_name, ok = QInputDialog.getText(self, "Save Perspective", "Enter unique name:")
        if not ok or not perspective_name:
            return

        self.dock_manager.addPerspective(perspective_name)
        self._refresh_perspective_list(select=perspective_name)

    def _refresh_perspective_list(self, select: str | None = None):
        blocker = QSignalBlocker(self.perspective_combo_box)
        self.perspective_combo_box.clear()
        self.perspective_combo_box.addItems(self.dock_manager.perspectiveNames())
        if select:
            self.perspective_combo_box.setCurrentText(select)

    # -------------------------
    # Add / remove dock widgets API (use this from WorkspaceTab)
    # -------------------------
    def add_dock_widget(
        self,
        title: str,
        widget: QtWidgets.QWidget,
        area=QtAds.DockWidgetArea.LeftDockWidgetArea,
        relative_to_area=None,
        as_tab: bool = False,
    ):
        dw = QtAds.CDockWidget(
            self.dock_manager,
            title,
            self.dock_manager,
        )
        dw.setWidget(widget)
        dw.setMinimumSizeHintMode(QtAds.CDockWidget.MinimumSizeHintFromDockWidget)

        if as_tab and relative_to_area is not None:
            self.dock_manager.addDockWidgetTabToArea(dw, relative_to_area)
        elif relative_to_area is not None:
            self.dock_manager.addDockWidget(area, dw, relative_to_area)
        else:
            self.dock_manager.addDockWidget(area, dw)

        return dw

    def _add_demo_widgets(self):
        # ---- Empty Pane A (left) ----
        pane1 = QtWidgets.QWidget()
        pane1.setStyleSheet("background: #2b2b2b;")

        dw1 = QtAds.CDockWidget(
            self.dock_manager,
            "Pane A",
            self.dock_manager,
        )
        dw1.setObjectName("Dock_Pane_A")
        dw1.setWidget(pane1)

        table_area = self.dock_manager.addDockWidget(
            QtAds.DockWidgetArea.LeftDockWidgetArea,
            dw1,
            self.central_dock_area,
        )

        # ---- Empty Pane B (bottom) ----
        pane2 = QtWidgets.QWidget()
        pane2.setStyleSheet("background: #333333;")

        dw2 = QtAds.CDockWidget(
            self.dock_manager,
            "Pane B",
            self.dock_manager,
        )
        dw2.setObjectName("Dock_Pane_B")
        dw2.setWidget(pane2)

        self.dock_manager.addDockWidget(
            QtAds.DockWidgetArea.BottomDockWidgetArea,
            dw2,
            table_area,
        )

        # ---- Empty Pane C (right) ----
        pane3 = QtWidgets.QWidget()
        pane3.setStyleSheet("background: #3b3b3b;")

        dw3 = QtAds.CDockWidget(
            self.dock_manager,
            "Pane C",
            self.dock_manager,
        )
        dw3.setObjectName("Dock_Pane_C")
        dw3.setWidget(pane3)

        self.dock_manager.addDockWidget(
            QtAds.DockWidgetArea.RightDockWidgetArea,
            dw3,
            self.central_dock_area,
        )

        # ---- Empty Pane D (tabbed with C) ----
        pane4 = QtWidgets.QWidget()
        pane4.setStyleSheet("background: #444444;")

        dw4 = QtAds.CDockWidget(
            self.dock_manager,
            "Pane D",
            self.dock_manager,
        )
        dw4.setObjectName("Dock_Pane_D")
        dw4.setWidget(pane4)

        self.dock_manager.addDockWidgetTabToArea(
            dw4,
            self.central_dock_area,
        )


if __name__ == "__main__":
    #################### WORKSPACE TAB TEST ALL SCREEN ###################
    ############## start date: 20260103
    from pathlib import Path
    from can_sdk.logger_setup import setup_logger
    from can_sdk.context_viewmodel import GeneralContextModel
    from can_sdk.dbc_manager import CANDBManager
    from can_sdk.canlog_viewmodel import LogContextManager
    from can_sdk.parser_manager import CANLogManager
    from can_sdk.connection_viewmodel import CANConnectManager, CANDeviceType
    from CenterContextPane import CenterContextPane
    from FiltersPanel import FiltersPanel
    from FileLogViewPanel import FileLogViewPanel
    from MonitorLogViewPanel import MonitorLogViewPanel
    from CustomSendMessagePanel import CustomSendMessagePanel
    from CustomReplayPanel import CustomReplayPanel
    from SignalGraphPanel import SignalGraphPanel
    from DBC_panel import CANDBCPanel

    setup_logger(env="DEV", backup_count=30)

    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(
        """
        QTabBar::tab {
            color: #E8E8E8;
            background: #3D3D3D;
            padding: 4px 10px;
        }
        QTabBar::tab:selected {
            color: #FFFFFF;
            background: #F26A21;
        }
        QTabBar::tab:hover:!selected {
            background: #4A4A4A;
        }
        """
    )

    win = QtWidgets.QMainWindow()
    win.setWindowTitle("WorkspaceTab QtAds Test (Real Panels)")
    win.resize(1400, 900)

    # Shared managers
    ctx_model = GeneralContextModel()
    center_pane = CenterContextPane(model=ctx_model)
    conn_mgr = CANConnectManager(CANDeviceType.SOCKETCAN)
    conn_mgr.start_scan()

    candb = CANDBManager()
    candb.load_database("/home/gnar911/Desktop/20260122 APP WEBSITE - CAN ANALYZER 3.0 CBCM TOOL APP ARC/CAN_Analyzer_MVVM/Database/EEA10_CANFD_R00c_withADAS_Main.dbc")
    log_ctx_mgr = LogContextViewModel(DBM = candb)
    FILELOG = "/home/gnar911/Desktop/2025-02-11_11-14-53_仕様情報切替 1_x10.asc"
    #FILELOG = "/home/gnar911/Desktop/2025-02-11_11-14-53_仕様情報切替 1.asc"
    log_ctx_mgr.request_verify_file(FILELOG)

    # Acquire first available channel for send/replay panels
    acquired_handle = None
    second_acquired_handle = None
    if conn_mgr.available_channels:
        available_handles = list(conn_mgr.available_channels.keys())
        first_handle = available_handles[0]
        if conn_mgr.acquire(first_handle):
            acquired_handle = first_handle

        if len(available_handles) > 1:
            second_handle = available_handles[1]
            if conn_mgr.acquire(second_handle):
                second_acquired_handle = second_handle

    ##### Expected: 20260310
    ############################## FULL TEST PANELS ##########################
    # workspace = WorkspaceTab(
    #     master=win,
    #     workspace_name="ADAS Channel",
    #     model=conn_mgr,
    #     central_widget=center_pane,
    # )

    # # Real center tabs (so CenterContextPane is visibly populated)
    # file_panel = FileLogViewPanel(
    #     parent=center_pane,
    #     candb=candb,
    #     log_ctx_mgr=log_ctx_mgr,
    # )
    # monitor_panel = MonitorLogViewPanel(
    #     parent=center_pane,
    #     candb=candb,
    #     cnt_model=conn_mgr,
    #     handle=acquired_handle,
    # )
    # center_pane.add_panel(file_panel, "File Log")
    # center_pane.add_panel(monitor_panel, "Monitor")

    # # Bottom dock tabs with real panels
    # filters_panel = FiltersPanel(
    #     parent=workspace,
    #     ctx_model=center_pane.context_vm,
    #     candb=candb,
    #     log_ctx_mgr=log_ctx_mgr,
    # )

    # signal_graph_panel = SignalGraphPanel(
    #     parent=workspace,
    #     model=ctx_model,
    # )

    # if acquired_handle is not None:
    #     send_panel_widget = CustomSendMessagePanel(
    #         parent=workspace,
    #         candb=candb,
    #         cnt_model=conn_mgr,
    #         handle=acquired_handle,
    #     )
    #     replay_panel_widget = CustomReplayPanel(
    #         parent=workspace,
    #         candb=candb,
    #         cnt_model=conn_mgr,
    #         handle=acquired_handle,
    #         ctx_model=center_pane.context_vm,
    #     )
    # else:
    #     send_panel_widget = QtWidgets.QLabel("No acquired channel for CustomSendMessagePanel")
    #     replay_panel_widget = QtWidgets.QLabel("No acquired channel for CustomReplayPanel")

    # dock_manager = workspace.dock_container.dock_manager
    # central_area = workspace.dock_container.central_dock_area
    # dock_manager.setStyleSheet(
    #     """
    #     ads--CDockWidgetTab {
    #         background: #3D3D3D;
    #         border: none;
    #         min-height: 22px;
    #         max-height: 22px;
    #         padding: 0px 10px;
    #     }
    #     ads--CDockWidgetTab:hover {
    #         background: #4A4A4A;
    #     }
    #     ads--CDockWidgetTab[activeTab="true"] {
    #         background: #F26A21;
    #     }

    #     ads--CDockWidgetTabLabel,
    #     ads--CDockWidgetTab QLabel {
    #         color: #E8E8E8;
    #     }
    #     ads--CDockWidgetTab[activeTab="true"] ads--CDockWidgetTabLabel,
    #     ads--CDockWidgetTab[activeTab="true"] QLabel {
    #         color: #FFFFFF;
    #         font-weight: 600;
    #     }
    #     """
    # )

    # dbc_panel = CANDBCPanel(
    #     parent=workspace,
    #     model=candb,
    # )

    # dw_dbc = QtAds.CDockWidget(
    #     dock_manager,
    #     "DBC_Panel",
    #     dock_manager,
    # )
    # dw_dbc.setWidget(dbc_panel)
    # dock_manager.addDockWidget(
    #     QtAds.DockWidgetArea.LeftDockWidgetArea,
    #     dw_dbc,
    #     central_area,
    # )

    # dw_filters = QtAds.CDockWidget(
    #     dock_manager,
    #     "FiltersPanel",
    #     dock_manager,
    # )
    # dw_filters.setWidget(filters_panel)
    # bottom_area = dock_manager.addDockWidget(
    #     QtAds.DockWidgetArea.BottomDockWidgetArea,
    #     dw_filters,
    #     central_area,
    # )

    # dw_send = QtAds.CDockWidget(
    #     dock_manager,
    #     "CustomSendMessagePanel",
    #     dock_manager,
    # )
    # dw_send.setWidget(send_panel_widget)
    # dock_manager.addDockWidgetTabToArea(dw_send, bottom_area)

    # dw_replay = QtAds.CDockWidget(
    #     dock_manager,
    #     "CustomReplayPanel",
    #     dock_manager,
    # )
    # dw_replay.setWidget(replay_panel_widget)
    # dock_manager.addDockWidgetTabToArea(dw_replay, bottom_area)

    # dw_signal = QtAds.CDockWidget(
    #     dock_manager,
    #     "SignalGraphPanel",
    #     dock_manager,
    # )
    # dw_signal.setWidget(signal_graph_panel)
    # dock_manager.addDockWidgetTabToArea(dw_signal, bottom_area)

    # win.setCentralWidget(workspace)
    # win.show()


    ######################## TEST SEND PANEL ######################
    # Separate window: send panel on first acquired channel
    # send_window = None
    # if acquired_handle is not None:
    #     send_window = QtWidgets.QMainWindow()
    #     send_window.setWindowTitle("CustomSendMessagePanel - Channel 1")
    #     send_window.resize(1000, 700)

    #     send_panel = CustomSendMessagePanel(
    #         parent=send_window,
    #         candb=candb,
    #         cnt_model=conn_mgr,
    #         handle=acquired_handle,
    #     )
    #     send_window.setCentralWidget(send_panel)
    #     send_window.show()

    ######################## TEST FILE PANEL ######################
    file_window = QtWidgets.QMainWindow()
    file_window.setWindowTitle("File Log Window")
    file_window.resize(1200, 800)

    file_panel = FileLogViewPanel(
        parent=file_window,
        log_ctx_mgr=log_ctx_mgr,
    )
    file_window.setCentralWidget(file_panel)
    file_window.show()

    ######################## OTHER FILTER PANEL #####################
    # other_filter_window = QtWidgets.QMainWindow()
    # other_filter_window.setWindowTitle("Other Filter Window")
    # other_filter_window.resize(1000, 800)

    # other_filter_panel = FiltersPanel(
    #     parent=other_filter_window,
    #     ctx_model=center_pane.context_vm,
    #     candb=candb,
    #     log_ctx_mgr=log_ctx_mgr,
    # )
    # other_filter_window.setCentralWidget(other_filter_panel)
    # other_filter_window.show()

    ######################## TEST REPLAY PANEL ######################
    # replay_windows = []
    # replay_handles = [h for h in (acquired_handle, second_acquired_handle) if h is not None]

    # for idx, replay_handle in enumerate(replay_handles, start=1):
    #     replay_window = QtWidgets.QMainWindow()
    #     replay_window.setWindowTitle(f"Replay Window - Channel {idx}")
    #     replay_window.resize(1200, 800)

    #     replay_root = QtWidgets.QWidget(replay_window)
    #     replay_layout = QtWidgets.QVBoxLayout(replay_root)
    #     replay_layout.setContentsMargins(8, 8, 8, 8)
    #     replay_layout.setSpacing(8)

    #     replay_panel = CustomReplayPanel(
    #         parent=replay_root,
    #         cnt_model=conn_mgr,
    #         handle=replay_handle,
    #         ctx_model=log_ctx_mgr,
    #     )
    #     replay_layout.addWidget(replay_panel, 1)
    #     replay_window.setCentralWidget(replay_root)
    #     replay_window.show()
    #     replay_windows.append(replay_window)
    #     break

    ######################## TEST MONITOR PANEL ######################
    # Separate windows: two monitor panels (one per acquired handle)
    # monitor_windows = []
    # monitor_handles = [h for h in (acquired_handle, second_acquired_handle) if h is not None]

    # for idx, monitor_handle in enumerate(monitor_handles, start=1):
    #     monitor_window = QtWidgets.QMainWindow()
    #     monitor_window.setWindowTitle(f"Monitor Window - Channel {idx}")
    #     monitor_window.resize(1000, 700)

    #     monitor_panel = MonitorLogViewPanel(
    #         parent=monitor_window,
    #         candb=candb,
    #         cnt_model=conn_mgr,
    #         handle=monitor_handle,
    #     )
    #     monitor_window.setCentralWidget(monitor_panel)
    #     monitor_window.show()
    #     monitor_windows.append(monitor_window)
    #     break

    # if len(monitor_handles) == 0:
    #     print("[TEST SETUP] Monitor is disabled: no acquired channel available.")
    # elif len(monitor_handles) == 1:
    #     print("[TEST SETUP] Only one monitor shown. Acquire a second channel to show 2 MonitorLogViewPanel windows.")

    sys.exit(app.exec())
