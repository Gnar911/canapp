from can_sdk.dbc_manager import CANDBManager
from can_sdk.connection_viewmodel import CANConnectManager, Handle
from can_sdk.logger_setup import LOG, setup_logger
from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QGroupBox, QVBoxLayout, QHBoxLayout,
    QLineEdit, QComboBox, QMessageBox, QLabel, QPushButton, QSizePolicy, 
    QApplication, QStyle, QToolButton
)
from PySide6.QtCore import Slot, Qt
from can_sdk.parser import LogParser
from ui_sdk.components.pyqt.TreeMonitorTable import TreeMonitorTable
# TEST module
from can_sdk.parser import LogParser
from can_sdk.connection_viewmodel import CANConnectManager, Handle, CANDeviceType, ChannelContext
from can_sdk.measurement import start_report_thread
import sys
"""
The steps to form a panel View-Model
1. The models it is using/components UI
2. The model function for View -> Model event
3. The event for Model-> View
"""
from typing import Optional, List, Tuple
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QToolButton,
    QComboBox, QApplication, QStyle, QFrame, QSizePolicy)
from can_sdk.logger_setup import LOG
from can_sdk.dbc_manager import CANDBManager
from can_sdk.data_object import CANLogLine  # your type
from ui_sdk.components.pyqt.TreeMonitorTable import TreeMonitorTable

class MonitorLogViewPanel(QWidget):
    """
    Live CAN monitor panel:
    - Start: poll received_messages_buffer every 2s, render into TreeLogTable
    - Stop: stop rendering, keep what already shown
    - Full mode: append all messages (like log), auto-scroll to bottom
    - Compact mode: one row per CAN ID, if changed highlight for 5s
    - Toolbox only available when Stop
    """
    def __init__(
        self,
        parent: QWidget,
        candb: CANDBManager,
        cnt_model: CANConnectManager,                  # CANConnectManager
        handle: Optional[Handle] = None,           # ChannelContext (preferred)
    ):
        super().__init__(parent)

        self.handle: Optional[Handle] = handle
        self.candb = candb
        self.cnt_model = cnt_model
        self.chl_ctx: Optional[ChannelContext] = None
        self._started_once = False
        self._last_progress_rows: int = -1
        self._last_progress_segment: int = -1
        self._mock_progress_rows: int = 50000
        self._mock_current_segment: int = 0
        self._bind_channel_context(self.handle)
        self.cnt_model.event_on_channels_state_changed.subscribe(self._on_channels_state_changed)

        # runtime
        self._running = False
        self._build_ui()
        self._connect_signals()
        self._apply_running_state(False)
        self._update_disconnect_overlay()

    def _bind_channel_context(self, handle: Optional[Handle]):
        self.handle = handle
        self.chl_ctx = self.cnt_model.get_context(handle) if handle is not None else None
        self._last_progress_rows = -1
        self._last_progress_segment = -1
        if self.chl_ctx:
            self.chl_ctx.event_on_filter_state_changed.subscribe(self.on_filter_changed)
        if hasattr(self, "tree"):
            self.tree.set_channel_handle(handle)

    def set_handle(self, handle: Optional[Handle]):
        self._bind_channel_context(handle)
        if hasattr(self, "tree"):
            self.tree.set_channel_handle(handle)
        self._update_disconnect_overlay()

    def on_filter_changed(self, filtered_lines: List[CANLogLine]):
        if self._running:
            return
        self.tree.refresh_from_context()

    # -------------------------------------------------
    # UI
    # -------------------------------------------------
    def _build_ui(self):
        main = QVBoxLayout(self)
        main.setContentsMargins(6, 2, 6, 6)
        main.setSpacing(4)

        self.cmb_mode = QComboBox()
        self.cmb_mode.addItems(["Full mode", "Compact mode"])
        self.cmb_mode.setCurrentIndex(0)  # default full

        # ---------- toolbox container (header + tools) ----------
        self.toolbox_container = QFrame(self)
        self.toolbox_container.setContentsMargins(0, 0, 0, 0)
        self.toolbox_container.setFrameStyle(QFrame.StyledPanel | QFrame.Plain)
        self.toolbox_container.setStyleSheet(
            "QFrame { border: 1px solid #444; border-radius: 3px; }"
        )

        toolbox_container_layout = QVBoxLayout(self.toolbox_container)
        toolbox_container_layout.setContentsMargins(0, 0, 0, 0)
        toolbox_container_layout.setSpacing(4)

        header_row = QWidget(self.toolbox_container)
        header_layout = QHBoxLayout(header_row)
        header_layout.setContentsMargins(6, 4, 6, 4)
        header_layout.setSpacing(6)

        self.display_group = QWidget(self.toolbox_container)
        display_layout = QHBoxLayout(self.display_group)
        display_layout.setContentsMargins(0, 0, 0, 0)
        display_layout.setSpacing(6)
        self.lbl_display = QLabel("Display:")
        display_layout.addWidget(self.lbl_display)
        display_layout.addWidget(self.cmb_mode)

        self.btn_toggle_toolbox = QToolButton(self.toolbox_container)
        self.btn_toggle_toolbox.setCheckable(True)
        self.btn_toggle_toolbox.setChecked(True)
        self.btn_toggle_toolbox.setArrowType(Qt.DownArrow)
        self.btn_toggle_toolbox.setToolTip("Show / hide tools")

        header_layout.addWidget(self.display_group)
        header_layout.addStretch(1)
        header_layout.addWidget(self.btn_toggle_toolbox)
        toolbox_container_layout.addWidget(header_row)

        # ---------- toolbox row (only when STOP) ----------
        self.toolbox_tools = QFrame(self.toolbox_container)
        self.toolbox_tools.setContentsMargins(0, 0, 0, 0)

        toolbox_layout = QHBoxLayout(self.toolbox_tools)
        toolbox_layout.setContentsMargins(6, 4, 6, 4)
        toolbox_layout.setSpacing(4)

        style = QApplication.style()

        def themed_icon(theme_name: str, fallback_sp: QStyle.StandardPixmap) -> QIcon:
            # "Google icon" try: on many Linux desktops, Material icons may exist in theme.
            # Fallback: Qt standard icon (always works).
            icon = QIcon.fromTheme(theme_name)
            if icon.isNull():
                icon = style.standardIcon(fallback_sp)
            return icon

        # Google-ish theme names (Material / freedesktop). Fallback to Qt SP_*
        icon_refresh = themed_icon("view-refresh", QStyle.SP_BrowserReload)
        icon_edit    = themed_icon("document-edit", QStyle.SP_FileDialogDetailedView)
        icon_clear   = themed_icon("edit-clear", QStyle.SP_DialogResetButton)
        icon_save    = themed_icon("document-save", QStyle.SP_DialogSaveButton)

        self.btn_refresh = QPushButton(icon_refresh, "Reset")
        self.btn_edit    = QPushButton(icon_edit,    "Edit")
        self.btn_clear   = QPushButton(icon_clear,   "Clear")
        self.btn_save    = QPushButton(icon_save,    "Save")

        toolbox_layout.addWidget(self.btn_refresh)
        toolbox_layout.addWidget(self.btn_edit)
        toolbox_layout.addWidget(self.btn_clear)
        toolbox_layout.addWidget(self.btn_save)
        toolbox_layout.addStretch(1)

        toolbox_container_layout.addWidget(self.toolbox_tools)

        self.header_label = QLabel("Monitor (Stopped)")
        self.header_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        main.addWidget(self.header_label)
        main.addWidget(self.toolbox_container)

        # ---------- controls row (Start/Stop) ----------
        ctrl_row = QWidget(self)
        ctrl_layout = QHBoxLayout(ctrl_row)
        ctrl_layout.setContentsMargins(0, 0, 0, 0)
        ctrl_layout.setSpacing(6)

        self.btn_start_stop = QPushButton("Start A Record")
        self.btn_start_stop.setCheckable(True)
        self.btn_start_stop.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        ctrl_layout.addWidget(self.btn_start_stop, 1)

        main.addWidget(ctrl_row)

        # ---------- tree ----------
        self.tree = TreeMonitorTable(
            self,
            connection_model=self.cnt_model,
            channel_handle=self.handle,
            model=self.candb,
        )
        main.addWidget(self.tree, 1)

        self._disconnected_overlay = QFrame(self)
        self._disconnected_overlay.setObjectName("monitorDisconnectOverlay")
        self._disconnected_overlay.setStyleSheet(
            "QFrame#monitorDisconnectOverlay { background: rgba(20, 20, 20, 110); }"
        )

        overlay_layout = QVBoxLayout(self._disconnected_overlay)
        overlay_layout.setContentsMargins(16, 16, 16, 16)
        overlay_layout.setAlignment(Qt.AlignCenter)

        self._disconnected_label = QLabel("Channel disconnected", self._disconnected_overlay)
        self._disconnected_label.setAlignment(Qt.AlignCenter)
        self._disconnected_label.setStyleSheet(
            "QLabel { color: white; font-size: 18px; font-weight: 600; }"
        )
        overlay_layout.addWidget(self._disconnected_label)

        self._disconnected_overlay.hide()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "_disconnected_overlay"):
            self._disconnected_overlay.setGeometry(self.rect())
            if self._disconnected_overlay.isVisible():
                self._disconnected_overlay.raise_()

    def _connect_signals(self):
        self.btn_start_stop.toggled.connect(self._on_start_stop_toggled)
        self.btn_toggle_toolbox.toggled.connect(self._on_toolbox_toggled)
        self.cmb_mode.currentIndexChanged.connect(self._on_mode_changed)

        # toolbox button handlers (empty for now)
        self.btn_refresh.clicked.connect(self.on_btn_refresh_clicked)
        self.btn_edit.clicked.connect(self.on_btn_edit_clicked)
        self.btn_clear.clicked.connect(self.on_btn_clear_clicked)
        self.btn_save.clicked.connect(self.on_btn_save_clicked)

    def _on_channels_state_changed(self, *_):
        self._update_disconnect_overlay()

    def _is_channel_disconnected(self) -> bool:
        if self.handle is None:
            return True

        checker = getattr(self.cnt_model, "is_channel_disconnected", None)
        if checker is None:
            return False

        try:
            return bool(checker(self.handle))
        except TypeError:
            return bool(checker())

    def _update_disconnect_overlay(self):
        if not hasattr(self, "_disconnected_overlay"):
            return
        disconnected = self._is_channel_disconnected()
        if disconnected:
            self._disconnected_overlay.setGeometry(self.rect())
            self._disconnected_overlay.show()
            self._disconnected_overlay.raise_()
        else:
            self._disconnected_overlay.hide()

    # -------------------------------------------------
    # Mode / state
    # -------------------------------------------------
    def _on_start_stop_toggled(self, checked: bool):
        if checked:
            self.start_monitor()
        else:
            self.stop_monitor()

    def start_monitor(self):
        if self._running:
            return

        if self.handle is None or self.chl_ctx is None:
            if hasattr(self, "tree"):
                self.tree.stop_visual_rows_timer()
            self._update_disconnect_overlay()
            return

        rx = self.cnt_model.get_receiver()
        if rx is not None:
            try:
                rx.reset_runtime_record()
            except Exception:
                pass

            try:
                rx.resume()
            except Exception:
                pass

        self._started_once = True
        self._last_progress_rows = -1
        self._last_progress_segment = -1
        self._mock_progress_rows = 50000
        self._mock_current_segment = 0
        self.tree.refresh_from_context()
        self.tree.start_visual_rows_timer()

        self._running = True
        self.btn_start_stop.setText("Stop Record")
        self.header_label.setText("Monitor (Running)")
        self._apply_running_state(True)

    def stop_monitor(self):
        if not self._running:
            if hasattr(self, "tree"):
                self.tree.stop_visual_rows_timer()
            return

        rx = self.cnt_model.get_receiver() if self.handle is not None else None
        if rx is not None:
            try:
                rx.pause()
            except Exception:
                pass

        self._running = False
        self.tree.stop_visual_rows_timer()
        self.btn_start_stop.setText("Start A Record")
        self.header_label.setText("Monitor (Stopped)")
        if self._is_compact_mode():
            self.cmb_mode.setCurrentIndex(0)
        self._apply_running_state(False)

    def _apply_running_state(self, running: bool):
        # Toolbox rules:
        # - Only available when STOP
        # - The ▼ toggle is only meaningful when STOP
        self.btn_toggle_toolbox.setEnabled(not running)
        self.display_group.setVisible(running)

        if running:
            self.toolbox_tools.setVisible(False)
        else:
            # restore toolbox visibility by toggle state
            self.toolbox_tools.setVisible(self.btn_toggle_toolbox.isChecked())

    def _on_toolbox_toggled(self, checked: bool):
        # Only when stopped
        if self._running:
            return
        self.toolbox_tools.setVisible(checked)
        self.btn_toggle_toolbox.setArrowType(Qt.DownArrow if checked else Qt.RightArrow)

    def _on_mode_changed(self, _):
        if self._is_full_mode():
            self.tree.enable_auto_scroll()
        else:
            self.tree.disable_auto_scroll()
        self.tree.refresh_from_context()


    def _poll_and_render(self):
        rx = self.cnt_model.get_receiver() if self.handle is not None else None
        if rx is not None:
            try:
                _ = rx.get_disk_logfile()
                # progress_rows, current_segment = disk_file.get_progress_index()
                # MOCK for testability:
                progress_rows = self._mock_progress_rows
                current_segment = self._mock_current_segment
                self._mock_progress_rows += 1000
                progress_rows = max(0, int(progress_rows))
                current_segment = int(current_segment)

                # Idle ticks: do nothing to avoid accumulating UI work/CPU.
                if (
                    progress_rows == self._last_progress_rows
                    and current_segment == self._last_progress_segment
                ):
                    return

                self._last_progress_rows = progress_rows
                self._last_progress_segment = current_segment

                LOG.debug(
                    f"[MONITOR][POLL] progress_rows={progress_rows}, "
                    #f"segment={current_segment}, "
                    #f"progress_path={_.progress_mmap_path}"
                )
            except Exception as e:
                LOG.debug(f"[MONITOR][POLL] progress_rows read failed: {e}")

    def _is_full_mode(self) -> bool:
        return self.cmb_mode.currentIndex() == 0

    def _is_compact_mode(self) -> bool:
        return self.cmb_mode.currentIndex() == 1

    # -------------------------------------------------
    # Toolbox button handlers (EMPTY for now)
    # -------------------------------------------------
    def on_btn_refresh_clicked(self):
        # TODO implement later
        LOG.debug("Refresh clicked (TODO)")
        if self._running:
            return

    def on_btn_edit_clicked(self):
        # TODO implement later
        LOG.debug("Edit clicked (TODO)")
        if self._running:
            return

    def on_btn_clear_clicked(self):
        # TODO implement later
        LOG.debug("Clear clicked (TODO)")
        if self._running:
            return

    def on_btn_save_clicked(self):
        # TODO implement later
        LOG.debug("Save clicked (TODO)")
        if self._running:
            return


def main():
    setup_logger(env="PRD", backup_count=30)

    app = QApplication(sys.argv)

    win = QWidget()
    win.setWindowTitle("CAN Test Panel (PySide6)")
    win.resize(500, 500)

    layout = QVBoxLayout(win)

    # ---------------- Sample log lines ----------------
    test_lines = [
        "2132132 CANFD   1 Rx        417                                   1 0 8 8  14 3C 40 00 00 00 09 BC",
        "2132133 CANFD   1 Rx        48E                                   1 0 8 8  40 92 49 60 80 4D 00 00",
        "2132132 CANFD   1 Rx        100                                   1 0 8 8  14 3C 40 00 00 00 10 BC",
        "2132135 CANFD   1 Rx         84                                   1 0 8 8  3F 85 3E 76 81 02 2F 3F",
        "2132137 CANFD   1 Rx        41E                                   1 0 8 8  40 92 14 60 80 4D 00 00",
        "2132138 CANFD   1 Rx        38E                                   1 0 8 8  40 80 49 60 80 4D 00 00",
        "2132139 CANFD   1 Rx        18E                                   1 0 8 8  40 92 49 10 80 4D 00 00",
        "2132135 CANFD   1 Rx         85                                   1 0 8 8  3F 85 3E 76 81 02 2F 3F",
        "2132137 CANFD   1 Rx         86                                   1 0 8 8  40 92 14 60 80 4D 00 00",
        "2132138 CANFD   1 Rx         87                                   1 0 8 8  40 80 49 60 80 4D 00 00",
        "2132139 CANFD   1 Rx         88                                   1 0 8 8  40 92 49 10 80 4D 00 00",
    ]

   # ---------------- Test data ----------------
    parser = LogParser()
    parsed_lines = [parser._various_parse_line_test(l, i) for i, l in enumerate(test_lines)]
    model = CANDBManager()
    model.load_database(
        "/home/gnar911/Desktop/20260122 APP WEBSITE - CAN ANALYZER 3.0 CBCM TOOL APP ARC/CAN_Analyzer_MVVM/Database/EEA10_CANFD_R00c_withADAS_Main.dbc")

    # ---------------- Connection Manager ----------------
    m = CANConnectManager(CANDeviceType.SOCKETCAN)
    m.start_scan()

    state = {
        "handle": None,
        "monitor": None,
        "monitors": {},
        "send_idx": 0,
        "periodic_idx": 0,
    }

    # ---------------- Button Actions ----------------

    def test_acquire_chnl():
        if not m.available_channels:
            QMessageBox.warning(win, "Warning", "No available channels")
            return

        handle, channel = next(iter(m.available_channels.items()))

        if m.acquire(handle):
            start_report_thread()
            state["handle"] = handle
            print(f"Acquired: {channel.name}")

            # Create monitor panel
            monitor = MonitorLogViewPanel(
                parent=win,
                candb=model,
                cnt_model=m,
                handle=handle
            )

            layout.addWidget(monitor)
            state["monitor"] = monitor
            state["monitors"][handle] = monitor
        else:
            QMessageBox.warning(win, "Warning", "Acquire failed")

    def test_release_chnl():
        handle = state["handle"]
        if handle is None:
            # If no active handle in state, release any remaining acquired channel.
            acquired = list(m.acquired_channels.keys())
            if not acquired:
                return
            handle = acquired[0]

        m.release(handle)
        print("Released channel")

        if state["handle"] == handle:
            state["handle"] = None

        # Destroy monitor panel safely (for the released handle)
        monitor = state.get("monitors", {}).pop(handle, None)
        if monitor:
            monitor.setParent(None)
            monitor.deleteLater()
            if state.get("monitor") is monitor:
                state["monitor"] = None

    def test_send_once():
        if state["handle"] is None:
            print("No channel acquired")
            return

        sender = m.get_sender()
        if not sender:
            return

        sender.send_once_from_entry(parsed_lines[0])
        print("Send once")

    PERIODIC_SEQ_MS = [10, 9, 8, 7, 6, 5]

    def test_send_loop():
        if state["handle"] is None:
            print("No channel acquired")
            return

        sender = m.get_sender()
        if not sender:
            return

        # ---- rotate log line ----
        line_idx = state["send_idx"] % len(parsed_lines)
        state["send_idx"] += 1


        per_idx = state["periodic_idx"] % len(PERIODIC_SEQ_MS)
        state["periodic_idx"] += 1

        periodic_ms = PERIODIC_SEQ_MS[per_idx]
        periodic_sec = periodic_ms / 1000.0

        print(f"Send loop started | periodic={periodic_ms} ms")

        sender.send_msg_loop_from_line(
            parsed_lines[line_idx],
            periodic_sec
        )

        print(
            f"Send loop started | "
            f"line={line_idx}, "
            f"periodic={periodic_ms} ms"
        )

    # ---------------- UI Buttons ----------------

    btn_acquire = QPushButton("Acquire Channel")
    btn_release = QPushButton("Release Channel")
    btn_send_once = QPushButton("Send Once")
    btn_send_loop = QPushButton("Send Loop")

    btn_acquire.clicked.connect(test_acquire_chnl)
    btn_release.clicked.connect(test_release_chnl)
    btn_send_once.clicked.connect(test_send_once)
    btn_send_loop.clicked.connect(test_send_loop)

    layout.addWidget(btn_acquire)
    layout.addWidget(btn_release)
    layout.addWidget(btn_send_once)
    layout.addWidget(btn_send_loop)
    layout.addStretch(1)

    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()