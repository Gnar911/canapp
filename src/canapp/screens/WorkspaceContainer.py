from PySide6 import QtWidgets
from can_sdk.logger_setup import LOG, setup_logger
from ChannelsTab import ChannelsTab
from can_sdk.connection_viewmodel import CANConnectManager, CANChannelInfo, Handle
from ui_sdk.components.pyqt.basic_component.FloatingWindow import FloatingWindow
from PySide6.QtWidgets import (QApplication,QWidget,QMainWindow,QVBoxLayout,QLabel,)
from PySide6.QtCore import QTimer
from pathlib import Path
import time
from can_sdk.test_ultility import (
    TEST_set_up_all_channels,
    TEST_down_all_channels,
    TEST_get_channel_status,
)
from can_sdk.dbc_manager import CANDBManager
from CustomSendMessagePanel import CustomSendMessagePanel
from MonitorLogViewPanel import MonitorLogViewPanel

""" 20260311: Multi-channel perf test"""
if __name__ == "__main__":
    setup_logger(env="DEV")

    app = QApplication([])

    try:
        TEST_set_up_all_channels(5)
        LOG.info("VCAN setup complete")
        print(TEST_get_channel_status())
    except Exception as exc:
        QtWidgets.QMessageBox.warning(
            None,
            "VCAN Setup",
            f"Failed to setup vcan interfaces:\n{exc}",
        )

    manager = CANConnectManager()
    manager.start_scan()

    candb = CANDBManager()
    default_dbc = Path(__file__).resolve().parents[3] / "Database" / "EEA10_CANFD_R00c_withADAS_Main.dbc"
    try:
        candb.load_database(str(default_dbc))
    except Exception as exc:
        LOG.warning("Failed to load DBC file for send panel: %s", exc)

    window = QMainWindow()
    window.setWindowTitle("WorkspaceContainer Multi-Channel Test")
    window.resize(1000, 640)

    root = QWidget(window)
    layout = QVBoxLayout(root)
    layout.setContentsMargins(8, 8, 8, 8)
    layout.setSpacing(8)

    title = QLabel("WorkspaceContainer - Multi Channel Testing")
    title.setStyleSheet("font-size: 14pt; font-weight: bold;")
    layout.addWidget(title)

    channels_tab = ChannelsTab(model=manager, parent=root)
    layout.addWidget(channels_tab, 1)

    floating_windows: dict[str, FloatingWindow] = {}

    def _on_channel_locked(handle: Handle):
        if floating_windows:
            for floating in floating_windows.values():
                floating.show()
                floating.raise_()
                floating.activateWindow()
            return

        send_panel = CustomSendMessagePanel(
            parent=None,
            candb=candb,
            cnt_model=manager,
            handle=handle,
        )

        channel_name = getattr(handle, "native_handle", handle)

        send_floating = FloatingWindow(
            title=f"Send Panel - Channel {channel_name}",
            content=send_panel,
        )
        send_floating.resize(860, 620)


        #################  Multi channel Monitor ###################
        monitor_container = QWidget()
        monitor_layout = QtWidgets.QVBoxLayout(monitor_container)
        monitor_layout.setContentsMargins(0, 0, 0, 0)
        monitor_layout.setSpacing(6)

        monitor_panel = MonitorLogViewPanel(
            parent=monitor_container,
            candb=candb,
            cnt_model=manager,
            handle=handle,
        )
        monitor_layout.addWidget(monitor_panel, 1)

        controls = QtWidgets.QHBoxLayout()
        total_label = QtWidgets.QLabel("Total mmap rows: 0", monitor_container)

        def update_total_label():
            source_provider = getattr(getattr(monitor_panel, "tree", None), "_source_provider", None)
            try:
                total = max(0, int(source_provider.row_count())) if source_provider is not None else 0
            except Exception:
                total = 0
            total_label.setText(f"Total mmap rows: {total}")

        refresh_btn = QtWidgets.QPushButton("Refresh", monitor_container)

        def on_refresh():
            start = time.perf_counter()
            monitor_panel.tree.refresh_from_context()
            t1 = time.perf_counter()
            QApplication.processEvents()
            t2 = time.perf_counter()
            print(f"refresh: {t1 - start:.4f}s | render: {t2 - t1:.4f}s | total: {t2 - start:.4f}s")
            update_total_label()

        refresh_btn.clicked.connect(on_refresh)
        controls.addWidget(refresh_btn)

        tick_btn = QtWidgets.QPushButton("Visual Rows Tick", monitor_container)

        def on_visual_rows_tick():
            monitor_panel.tree._on_visual_rows_timer()
            update_total_label()

        tick_btn.clicked.connect(on_visual_rows_tick)
        controls.addWidget(tick_btn)

        mode_btn = QtWidgets.QPushButton("Mode: Read", monitor_container)

        def on_toggle_mode():
            toggle = getattr(monitor_panel.tree, "toggle_edit_mode", None)
            is_edit = bool(toggle()) if callable(toggle) else False
            mode_btn.setText("Mode: Edit" if is_edit else "Mode: Read")

        mode_btn.clicked.connect(on_toggle_mode)
        controls.addWidget(mode_btn)

        timer_toggle_btn = QtWidgets.QPushButton("Start Timer", monitor_container)

        def on_toggle_timer():
            timer = monitor_panel.tree._visual_rows_timer
            if timer.isActive():
                monitor_panel.tree.stop_visual_rows_timer()
                timer_toggle_btn.setText("Start Timer")
            else:
                monitor_panel.tree.start_visual_rows_timer()
                timer_toggle_btn.setText("Stop Timer")

        timer_toggle_btn.clicked.connect(on_toggle_timer)
        controls.addWidget(timer_toggle_btn)

        controls.addWidget(total_label)
        monitor_layout.addLayout(controls)

        monitor_panel.tree._visual_rows_timer.timeout.connect(update_total_label)
        update_total_label()

        monitor_floating = FloatingWindow(
            title=f"Monitor Panel - Channel {channel_name}",
            content=monitor_container,
        )
        monitor_floating.resize(980, 620)

        send_floating.show()
        monitor_floating.show()

        floating_windows["send"] = send_floating
        floating_windows["monitor"] = monitor_floating

        def _on_window_destroyed(*_):
            floating_windows.clear()

        send_floating.destroyed.connect(_on_window_destroyed)
        monitor_floating.destroyed.connect(_on_window_destroyed)

    channels_tab.channelLocked.connect(_on_channel_locked)

    window.setCentralWidget(root)
    window.show()

    refresh_timer = QTimer(window)
    refresh_timer.setInterval(500)
    refresh_timer.timeout.connect(channels_tab.on_event_channels_scan)
    refresh_timer.start()

    def _cleanup():
        try:
            for floating in list(floating_windows.values()):
                floating.close()
            manager.shutdown()
        finally:
            try:
                TEST_down_all_channels()
            except Exception as exc:
                LOG.warning("VCAN teardown warning: %s", exc)

    app.aboutToQuit.connect(_cleanup)
    app.exec()




