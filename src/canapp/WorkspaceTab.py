from PySide6 import QtWidgets, QtCore
# from can_sdk.connection_viewmodel import CANConnectManager, CANChannelInfo, LogContextViewModel
import sys
import os
os.environ.setdefault("QT_QPA_PLATFORM", "xcb")
from PySide6 import QtCore, QtWidgets
from PySide6.QtCore import Qt, QSignalBlocker
from PySide6.QtWidgets import (QPlainTextEdit, QInputDialog, QToolBar, QVBoxLayout,)
import PySide6QtAds as QtAds
from canapp.DBCPanel import CANDBCPanel
from canapp.FileLogViewPanel import FileLogViewPanel
from canapp.FiltersPanel import FiltersPanel
from canapp.MonitorLogViewPanel import MonitorLogViewPanel
from canapp.CustomReplayPanel import CustomReplayPanel
from canapp.CustomSendMessagePanel import CustomSendMessagePanel
from canapp.vm.container import AppContainer
from PySide6QtAds import *

"""
QtAds.CDockManager.setConfigFlag(
    QtAds.CDockManager.OpaqueSplitterResize, True
)
QtAds.CDockManager.setConfigFlag(
    QtAds.CDockManager.XmlCompressionEnabled, False
)
QtAds.CDockManager.setConfigFlag(
    QtAds.CDockManager.FocusHighlighting, True
)
"""
class WorkspaceDockContainer(QtWidgets.QWidget):
    """
    A QWidget that embeds a QtAds CDockManager.
    This is the 'second part' of WorkspaceTab.
    """
    def __init__(self, app: AppContainer, parent=None):
        super().__init__(parent)

        self.dbc_vm = app.dbc_vm()
        self.file_log_vm = app.log_vm()
        self.monitor_vm = app.record_vm()
        self.replay_vm = app.replay_vm()
        self.send_vm = app.schedule_vm()

        # ---- layout: optional toolbar + dock manager ----
        self._toolbar = QToolBar(self)
        self._toolbar.setMovable(False)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._toolbar)


       # 2️⃣ Create dock manager (NO config calls yet)
        self.dock_manager = QtAds.CDockManager(self)
        self.dock_manager.setStyleSheet(
            """
            /* Dock tab bar - modern dark style */
            QTabBar {
                qproperty-drawBase: 0;
                spacing: 6px;
            }

            QTabBar::tab {
                background: transparent;
                color: #E6E6E6;
                padding: 8px 14px;
                margin: 2px;
                border-radius: 6px;
                font-weight: 600;
                min-width: 96px;
            }

            QTabBar::tab:hover {
                background: rgba(255,255,255,0.04);
                color: #FFFFFF;
            }

            QTabBar::tab:selected {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #3a7bd5, stop:1 #2b6fb3);
                color: #FFFFFF;
                border: 1px solid rgba(255,255,255,0.08);
                padding: 9px 14px;
            }

            QTabBar::tab:!selected {
                background: transparent;
                color: #CFCFCF;
            }

            QTabBar::tab:disabled {
                color: #7F7F7F;
            }

            QTabWidget::pane {
                border: none;
                background: transparent;
            }
            """
        )

        self.central_dock_widget = QtAds.CDockWidget(
            self.dock_manager,
            "File Log",
            self.dock_manager,
        )
        self.central_dock_widget.setWidget(FileLogViewPanel(self.file_log_vm, self))
        self.central_dock_area = self.dock_manager.setCentralWidget(self.central_dock_widget)
        self.central_dock_area.setAllowedAreas(QtAds.DockWidgetArea.OuterDockAreas)

        # 5️⃣ Add dock manager to layout LAST
        layout.addWidget(self.dock_manager)

        # ---- DBC --------------------------------------------------------
        dbc_dock = QtAds.CDockWidget(
            self.dock_manager,
            "DBC",
            self.dock_manager,
        )
        dbc_dock.setObjectName("Dock_DBC")
        dbc_dock.setWidget(CANDBCPanel(self.dbc_vm, self))
        # Allow docking movement and floating; but prevent closing
        dbc_dock.setFeature(QtAds.CDockWidget.DockWidgetFeature.DockWidgetMovable, True)
        dbc_dock.setFeature(QtAds.CDockWidget.DockWidgetFeature.DockWidgetFloatable, True)
        dbc_dock.setFeature(QtAds.CDockWidget.DockWidgetFeature.DockWidgetClosable, False)

        self.dock_manager.addDockWidget(
            QtAds.DockWidgetArea.LeftDockWidgetArea,
            dbc_dock,
            self.central_dock_area,
        )

        # ---- Filters ----------------------------------------------------

        filters_dock = QtAds.CDockWidget(
            self.dock_manager,
            "Filters",
            self.dock_manager,
        )
        filters_dock.setObjectName("Dock_Filters")
        filters_dock.setWidget(FiltersPanel(self.file_log_vm, self))
        # Allow moving and floating of bottom panels; keep them non-closable
        filters_dock.setFeature(QtAds.CDockWidget.DockWidgetFeature.DockWidgetMovable, True)
        filters_dock.setFeature(QtAds.CDockWidget.DockWidgetFeature.DockWidgetFloatable, True)
        filters_dock.setFeature(QtAds.CDockWidget.DockWidgetFeature.DockWidgetClosable, False)

        # Create a bottom dock area and put filters there (shared for bottom panels)
        bottom_area = self.dock_manager.addDockWidget(
            QtAds.DockWidgetArea.BottomDockWidgetArea,
            filters_dock,
            self.central_dock_area,
        )

        # ---- Monitor ----------------------------------------------------

        monitor_dock = QtAds.CDockWidget(
            self.dock_manager,
            "Monitor",
            self.dock_manager,
        )
        monitor_dock.setObjectName("Dock_Monitor")
        monitor_dock.setWidget(MonitorLogViewPanel(self.monitor_vm, self))
        # Allow user to redock/move/float the monitor dock, but keep closable flag off
        monitor_dock.setFeature(QtAds.CDockWidget.DockWidgetFeature.DockWidgetMovable, True)
        monitor_dock.setFeature(QtAds.CDockWidget.DockWidgetFeature.DockWidgetFloatable, True)
        monitor_dock.setFeature(QtAds.CDockWidget.DockWidgetFeature.DockWidgetClosable, False)

        # Add Monitor as a tab in the bottom area
        self.dock_manager.addDockWidgetTabToArea(
            monitor_dock,
            bottom_area,
        )
        monitor_area = bottom_area

        # ---- Replay -----------------------------------------------------

        replay_dock = QtAds.CDockWidget(
            self.dock_manager,
            "Replay",
            self.dock_manager,
        )
        replay_dock.setObjectName("Dock_Replay")
        replay_dock.setWidget(CustomReplayPanel(self.replay_vm, self))
        replay_dock.setFeature(QtAds.CDockWidget.DockWidgetFeature.DockWidgetMovable, True)
        replay_dock.setFeature(QtAds.CDockWidget.DockWidgetFeature.DockWidgetFloatable, True)
        replay_dock.setFeature(QtAds.CDockWidget.DockWidgetFeature.DockWidgetClosable, False)

        # Add Replay as a tab in the bottom area
        self.dock_manager.addDockWidgetTabToArea(
            replay_dock,
            bottom_area,
        )

        # ---- Send Message -----------------------------------------------
        send_dock = QtAds.CDockWidget(
            self.dock_manager,
            "Send Message",
            self.dock_manager,
        )
        send_dock.setObjectName("Dock_SendMessage")
        send_dock.setWidget(CustomSendMessagePanel(self.send_vm, self))
        send_dock.setFeature(QtAds.CDockWidget.DockWidgetFeature.DockWidgetMovable, True)
        send_dock.setFeature(QtAds.CDockWidget.DockWidgetFeature.DockWidgetFloatable, True)

        # Add Send Message as a tab in the bottom area
        self.dock_manager.addDockWidgetTabToArea(
            send_dock,
            bottom_area,
        )
        # Prevent send dock from being closed
        send_dock.setFeature(QtAds.CDockWidget.DockWidgetFeature.DockWidgetClosable, False)


    # def _save_perspective(self):
    #     perspective_name, ok = QInputDialog.getText(self, "Save Perspective", "Enter unique name:")
    #     if not ok or not perspective_name:
    #         return

    #     self.dock_manager.addPerspective(perspective_name)
    #     self._refresh_perspective_list(select=perspective_name)

    # def _refresh_perspective_list(self, select: str | None = None):
    #     blocker = QSignalBlocker(self.perspective_combo_box)
    #     self.perspective_combo_box.clear()
    #     self.perspective_combo_box.addItems(self.dock_manager.perspectiveNames())
    #     if select:
    #         self.perspective_combo_box.setCurrentText(select)

    # -------------------------
    # Add / remove dock widgets API (use this from WorkspaceTab)
    # -------------------------
    # def add_dock_widget(
    #     self,
    #     title: str,
    #     widget: QtWidgets.QWidget,
    #     area=QtAds.DockWidgetArea.LeftDockWidgetArea,
    #     relative_to_area=None,
    #     as_tab: bool = False,
    # ):
    #     dw = QtAds.CDockWidget(
    #         self.dock_manager,
    #         title,
    #         self.dock_manager,
    #     )
    #     dw.setWidget(widget)
    #     dw.setMinimumSizeHintMode(QtAds.CDockWidget.MinimumSizeHintFromDockWidget)

        # if as_tab and relative_to_area is not None:
        #     self.dock_manager.addDockWidgetTabToArea(dw, relative_to_area)
        # elif relative_to_area is not None:
        #     self.dock_manager.addDockWidget(area, dw, relative_to_area)
        # else:
        #     self.dock_manager.addDockWidget(area, dw)

        #return dw