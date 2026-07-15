import os
from typing import Any, Optional, Set, List
from PySide6 import QtCore, QtWidgets
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget
from can_sdk.data_object import CANLogLine, SignalFilter
from can_sdk.dbc_manager import CANDBManager
from can_sdk.connection_viewmodel import CANConnectManager, Handle
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QMessageBox, QApplication)
from can_sdk.dbc_manager import CANDBManager
from can_sdk.canlog_viewmodel import LogContextViewModel, BasicFileLogContext
from can_sdk.connection_viewmodel import CANConnectManager, Handle
from can_sdk.replay_viewmodel import CANLogPlayer, ReplayStatus
from can_sdk.parser_manager import CANLogManager
from can_sdk.logger_setup import LOG, setup_logger
from can_sdk.measurement import start_report_thread
from ui_sdk.components.pyqt.basic_component.CollapsibleSection import CollapsibleSection 
from ui_sdk.components.pyqt.ReplayTimescopeSlider import ReplayTimescopeSlider
from ui_sdk.components.pyqt.ReplayMessageFilterCheckList import ReplayMessageFilterCheckList
from can_sdk.data_object import CANLogLine
from can_sdk.global_event import event_on_signal_select

# TEST module
from can_sdk.connection_viewmodel import CANConnectManager, Handle, CANDeviceType, ChannelContext
import sys
from FileLogViewPanel import FileLogViewPanel
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt

class DisconnectedPanel(QtWidgets.QWidget):
	def __init__(self, parent: Optional[QWidget] = None):
		super().__init__(parent)
		layout = QtWidgets.QVBoxLayout(self)
		layout.setContentsMargins(24, 24, 24, 24)
		layout.setAlignment(Qt.AlignCenter)
		title = QtWidgets.QLabel("Channel disconnected")
		title.setAlignment(Qt.AlignCenter)
		title.setStyleSheet("font-size: 18px; font-weight: 600;")
		desc = QtWidgets.QLabel("Reconnect channel to use replay panel")
		desc.setAlignment(Qt.AlignCenter)
		layout.addWidget(title)
		layout.addWidget(desc)

class CustomReplayPanel(QtWidgets.QWidget):
	replay_status_signal = QtCore.Signal(object)

	def __init__(
		self,
		parent: QWidget,
		cnt_model: CANConnectManager, # connection_viewmodel
		handle: Handle,
		ctx_model: LogContextViewModel, # log_viewmodel
	):
		super().__init__(parent)
		self.handle = handle
		event_on_signal_select.subscribe(self.on_event_signal_select)
		self.cnt_model = cnt_model
		self.ctx_model = ctx_model
		self.cnt_model.event_on_channels_state_changed.subscribe(self.on_event_channel_disconnected)
		self.player: Optional[CANLogPlayer] = self.cnt_model.get_player()
		if self.player:
			self.player.event_on_replay_status_changed.subscribe(self.on_event_replay_status_changed)
		self._selected_signal_can_id: Optional[int] = None
		self._replay_lines: list[CANLogLine] = []
		self._replay_status: str = "IDLE"
		self._completed_cycles: int = 0
		self.replay_status_signal.connect(self._handle_replay_status_on_ui, Qt.QueuedConnection)
		self.ctx_model.event_on_context_changed.subscribe(self.on_event_target_logfile_changed)
		self.on_event_target_logfile_changed(self.ctx_model.cur_ctx)
		self._build_ui()
		self._connect_ui()
		self._refresh_loop_toggle_text()
		self._update_cycle_status_label()
		self._set_replay_inputs_enabled(True)
		self._apply_replay_config_to_player()
		self._update_disconnect_overlay()

	def _build_ui(self):
		root = QtWidgets.QStackedLayout(self)
		main_page = QtWidgets.QWidget(self)
		main_layout = QtWidgets.QVBoxLayout(main_page)
		main_layout.setContentsMargins(8, 8, 8, 8)
		main_layout.setSpacing(8)

		control_box = QtWidgets.QGroupBox("")
		control_layout = QtWidgets.QGridLayout(control_box)

		#control_layout.addWidget(QtWidgets.QLabel("Target log:"), 0, 0)
		#self.lb_target_log_name = QtWidgets.QLabel("Monitor log")
		#control_layout.addWidget(self.lb_target_log_name, 0, 1, 1, 5)

		self.btn_replay = QtWidgets.QPushButton("Replay")
		self.btn_stop = QtWidgets.QPushButton("Stop")
		self.tg_loop = QtWidgets.QCheckBox("LoopON")
		self.tg_loop.setChecked(False)
		self.lb_cycle_status = QtWidgets.QLabel("Completed: 0/∞")
		self.lb_target_logfile = QtWidgets.QLabel("Target logfile: -")
		self.lb_repeat = QtWidgets.QLabel("Repeat")
		self.spin_repeat = QtWidgets.QSpinBox()
		self.spin_repeat.setMinimum(1)
		self.spin_repeat.setValue(1)
		self.spin_repeat.setKeyboardTracking(True)

		self.repeat_widget = QtWidgets.QWidget(self)
		repeat_layout = QtWidgets.QHBoxLayout(self.repeat_widget)
		repeat_layout.setContentsMargins(0, 0, 0, 0)
		repeat_layout.setSpacing(4)
		repeat_layout.addWidget(self.lb_repeat)
		repeat_layout.addWidget(self.spin_repeat)

		replay_buttons_row = QtWidgets.QHBoxLayout()
		replay_buttons_row.setContentsMargins(0, 0, 0, 0)
		replay_buttons_row.setSpacing(6)
		replay_buttons_row.addWidget(self.btn_replay)
		replay_buttons_row.addWidget(self.btn_stop)
		replay_buttons_row.addSpacing(16)
		replay_buttons_row.addWidget(self.tg_loop)
		replay_buttons_row.addSpacing(16)
		replay_buttons_row.addWidget(self.repeat_widget)
		replay_buttons_row.addSpacing(16)
		replay_buttons_row.addWidget(self.lb_cycle_status)
		replay_buttons_row.addStretch(1)

		control_layout.addWidget(self.lb_target_logfile, 0, 0, 1, 5)
		control_layout.addLayout(replay_buttons_row, 1, 0, 1, 5)

		self.repeat_widget.setVisible(not self.tg_loop.isChecked())

		main_layout.addWidget(control_box)

		filter_container = QtWidgets.QWidget(self)
		filter_layout = QtWidgets.QVBoxLayout(filter_container)
		filter_layout.setContentsMargins(0, 0, 0, 0)
		filter_layout.setSpacing(8)

		msg_section = CollapsibleSection("Filter Message Replay", expanded=False)
		msg_section.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Maximum)
		msg_content_layout = QtWidgets.QVBoxLayout()
		msg_content_layout.setContentsMargins(0, 0, 0, 0)
		self.msg_check_list = ReplayMessageFilterCheckList(parent=self, ctx_model=self.ctx_model, player=self.player)
		self.msg_check_list.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
		msg_content_layout.addWidget(self.msg_check_list, 1)
		msg_section.setContentLayout(msg_content_layout)

		scope_section = CollapsibleSection("Time Scope Replay", expanded=False)
		scope_section.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Maximum)
		scope_content_layout = QtWidgets.QVBoxLayout()
		scope_content_layout.setContentsMargins(0, 0, 0, 0)
		scope_group = QtWidgets.QGroupBox("")
		scope_group_layout = QtWidgets.QVBoxLayout(scope_group)
		scope_group_layout.setContentsMargins(6, 6, 6, 6)
		self.scope_slider = ReplayTimescopeSlider(player=self.player, ctx_model=self.ctx_model)
		scope_group_layout.addWidget(self.scope_slider)

		scope_content_layout.addWidget(scope_group)
		scope_section.setContentLayout(scope_content_layout)

		filter_layout.addWidget(msg_section)
		filter_layout.addWidget(scope_section)
		filter_layout.addStretch(1)
		main_layout.addWidget(filter_container, 1)
		main_layout.addStretch(1)

		root.addWidget(main_page)
		#root.addWidget(self.disconnected_panel)
		self._stack = root
		self._stack.setCurrentIndex(0)

		self._disconnected_overlay = QtWidgets.QFrame(self)
		self._disconnected_overlay.setObjectName("replayDisconnectOverlay")
		self._disconnected_overlay.setStyleSheet(
			"QFrame#replayDisconnectOverlay { background: rgba(20, 20, 20, 110); }"
		)

		overlay_layout = QtWidgets.QVBoxLayout(self._disconnected_overlay)
		overlay_layout.setContentsMargins(16, 16, 16, 16)
		overlay_layout.setAlignment(Qt.AlignCenter)

		self._disconnected_label = QtWidgets.QLabel("Channel disconnected", self._disconnected_overlay)
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

	def _connect_ui(self):
		self.btn_replay.clicked.connect(self._on_click_replay_or_pause)
		self.btn_stop.clicked.connect(self._on_click_stop)
		self.tg_loop.toggled.connect(self._on_loop_toggled)
		self.spin_repeat.valueChanged.connect(self._on_repeat_changed)
		self.spin_repeat.textChanged.connect(self._on_repeat_text_changed)

		self.scope_slider.valueChanged.connect(self._on_time_scope_changed)
		self.scope_slider.handleIndexChanged.connect(self._on_handle_index_changed)

	def _selected_message_ids(self) -> list[int]:
		checklist = getattr(self, "msg_check_list", None)
		if checklist is None:
			return []
		getter = getattr(checklist, "_checked_can_ids", None)
		if callable(getter):
			try:
				return [int(can_id) for can_id in getter()]
			except Exception:
				return []
		return []

	def _refresh_loop_toggle_text(self):
		self.tg_loop.setText("LoopON" if self.tg_loop.isChecked() else "LoopOFF")

	def _update_cycle_status_label(self, total_override=None):
		if self.tg_loop.isChecked():
			total_text = "∞"
		else:
			if total_override not in (None, ""):
				try:
					total_text = str(max(1, int(total_override)))
				except Exception:
					total_text = str(self.spin_repeat.value())
			else:
				total_text = str(self.spin_repeat.value())
		self.lb_cycle_status.setText(f"Completed: {max(0, int(self._completed_cycles))}/{total_text}")

	def _set_replay_inputs_enabled(self, enabled: bool):
		self.tg_loop.setEnabled(enabled)
		self.spin_repeat.setEnabled(enabled)

	def _apply_replay_config_to_player(self):
		if not self.player:
			return
		self.player.set_loop(self.tg_loop.isChecked())
		self.player.set_repeat(self.spin_repeat.value())

	def _on_time_scope_changed(self, start_ts: float, end_ts: float):
		if self.player:
			self.player.set_time_scope(start_ts, end_ts)

	def _on_handle_index_changed(self, handle_id: int, index: int):
		if hasattr(self, "replay_logfile") and self.replay_logfile:
			self.replay_logfile.trigger_focus_to_row(index)

	def _on_click_replay_or_pause(self):
		if not self.player:
			LOG.warning("[ReplayPanel] click ignored: player is None")
			return
		process_alive = bool(getattr(self.player, "process", None) and self.player.process.is_alive())
		LOG.debug(
			"[ReplayPanel] click action state=%s process_alive=%s",
			self._replay_status,
			process_alive,
		)
		if not process_alive:
			LOG.error("[ReplayPanel] replay process is not alive; click ignored")
			return
		self._apply_replay_config_to_player()
		if self._replay_status in ("STARTED", "RESUMED"):
			self.player.pause()
			return
		if self._replay_status == "PAUSED":
			self.player.resume()
			return
		#row_indices = self._effective_row_indices_for_replay(from_filter)
		LOG.debug("_on_click_replay_or_pause")
		if not hasattr(self, "replay_logfile") or self.replay_logfile is None:
			LOG.warning("[ReplayPanel] click ignored: no replay target selected")
			return
		try:
			filter_can_ids = self._selected_message_ids() or None
			self.player.start_replay_context(self.replay_logfile, filter_can_ids=filter_can_ids)
		except Exception:
			LOG.exception("[ReplayPanel] failed to start replay context")

	def _on_click_stop(self):
		if self.player:
			self.player.stop()

	def _on_loop_toggled(self, enabled: bool):
		self._refresh_loop_toggle_text()
		if hasattr(self, "repeat_widget"):
			self.repeat_widget.setVisible(not enabled)
		self._completed_cycles = 0
		self._update_cycle_status_label()
		if self.player:
			self.player.set_loop(enabled)

	def _on_repeat_changed(self, value: int):
		self._completed_cycles = 0
		self._update_cycle_status_label(total_override=value)
		if self.player:
			self.player.set_repeat(value)

	def _on_repeat_text_changed(self, text: str):
		if self.tg_loop.isChecked():
			return
		try:
			num = int(text)
		except Exception:
			num = self.spin_repeat.value()
		self._update_cycle_status_label(total_override=max(1, num))

	def _on_filter_mode_changed(self):
		if self.player:
			msg_ids = self._selected_message_ids()
			self.player.set_msg_id_filter(msg_ids if msg_ids else None)

	def on_event_signal_select(self, data: Optional[SignalFilter]):
		if data is None:
			return
		self._selected_signal_can_id = data.can_id

	def on_event_channel_disconnected(self, *_):
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

	def on_event_target_logfile_changed(self, file: BasicFileLogContext):
		self.replay_logfile = file
		self._update_target_logfile_label(file)
		#self.on_event_filter_changed(self.replay_logfile.canlog_filter)

	def _resolve_target_logfile_name(self, file: Optional[BasicFileLogContext]) -> str:
		if file is None:
			return "-"

		file_name = getattr(file, "file_name", None)
		if file_name:
			return str(file_name)

		file_path = getattr(file, "file_path", None)
		if file_path:
			return os.path.basename(str(file_path))

		d_filelog = getattr(file, "d_filelog", None)
		if d_filelog is not None:
			name_from_datalog = getattr(d_filelog, "file_name", None)
			if name_from_datalog:
				return str(name_from_datalog)
			path_from_datalog = getattr(d_filelog, "file_path", None)
			if path_from_datalog:
				return os.path.basename(str(path_from_datalog))

		return "-"

	def _update_target_logfile_label(self, file: Optional[BasicFileLogContext]):
		if not hasattr(self, "lb_target_logfile"):
			return
		self.lb_target_logfile.setText(f"Target logfile: {self._resolve_target_logfile_name(file)}")

	def on_event_filter_changed(self, data: list[CANLogLine]):
		# Update time scope
		self._replay_lines = list(data)
		timestamps = self.replay_logfile.datalog.get_timestamps_of_target_log_line(self._replay_lines)
		self.scope_slider.set_timestamps(timestamps)

	# Statuses that represent an actual state change (used to track _replay_status)
	_STATE_STATUSES = frozenset((
		"STARTED", "RESUMED", "PAUSED", "STOPPED",
		"FINISHED", "TIME_SCOPE_FINISHED", "IDLE", "EXIT",
	))

	def on_event_replay_status_changed(self, status: ReplayStatus):
		if status.status == "PROGRESS":
			pass
		else:
			LOG.info("[ReplayPanel][STATUS] %s payload=%s", status.status, status.payload)
		self.replay_status_signal.emit(status)

	def _handle_replay_status_on_ui(self, status: ReplayStatus):

		# Only update _replay_status for real state transitions.
		# Informational statuses like PROGRESS, CYCLE_COMPLETED, LOOPED, etc.
		# must NOT overwrite the current state — otherwise pause/resume
		# checks against _replay_status will fail.
		if status.status in self._STATE_STATUSES:
			self._replay_status = status.status

		if status.status in ("STARTED", "RESUMED"):
			self.btn_replay.setText("Pause")
			if status.status == "STARTED":
				start_report_thread()
		elif status.status in ("PAUSED", "FINISHED", "TIME_SCOPE_FINISHED", "STOPPED"):
			self.btn_replay.setText("Replay")

		if status.status in ("STARTED", "RESUMED", "PAUSED"):
			self._set_replay_inputs_enabled(False)
		elif status.status in ("STOPPED", "FINISHED", "TIME_SCOPE_FINISHED", "IDLE", "EXIT"):
			self._set_replay_inputs_enabled(True)

		if status.status == "STARTED":
			self._completed_cycles = 0
			self._update_cycle_status_label()

		if status.status == "LOOPED":
			loop_enabled = bool(status.payload.get("enabled", self.tg_loop.isChecked()))
			self.tg_loop.blockSignals(True)
			self.tg_loop.setChecked(loop_enabled)
			self.tg_loop.blockSignals(False)
			self._refresh_loop_toggle_text()
			if hasattr(self, "repeat_widget"):
				self.repeat_widget.setVisible(not loop_enabled)
			self._update_cycle_status_label()

		if status.status == "REPEATED":
			count = int(status.payload.get("count", self.spin_repeat.value()))
			self.spin_repeat.blockSignals(True)
			self.spin_repeat.setValue(count)
			self.spin_repeat.blockSignals(False)
			self._update_cycle_status_label(total_override=count)

		if status.status == "CYCLE_COMPLETED":
			try:
				self._completed_cycles = int(status.payload.get("completed", self._completed_cycles))
			except Exception:
				pass
			self._update_cycle_status_label(total_override=status.payload.get("total"))

		if status.status == "FINISHED":
			try:
				self._completed_cycles = int(status.payload.get("completed", self._completed_cycles))
			except Exception:
				pass
			self._update_cycle_status_label()

		if status.status == "PROGRESS":
			self.scope_slider.set_progress_index(int(status.payload["current_index"]))

def main():
    setup_logger(env="DEV", backup_count=30)
    app = QApplication(sys.argv)
    win = QWidget()
    win.setWindowTitle("TreeLogTable Test")
    layout = QVBoxLayout(win)

    candb = CANDBManager()
    candb.load_database(
        "/home/gnar911/Desktop/20260122 APP WEBSITE - CAN ANALYZER 3.0 CBCM TOOL APP ARC/CAN_Analyzer_MVVM/Database/EEA10_CANFD_R00c_withADAS_Main.dbc")

    clm = CANLogManager()
    ctx = LogContextViewModel(DBM = candb, CLM= clm)
    
    # ---------------- Connection Manager ----------------
    m = CANConnectManager(CANDeviceType.SOCKETCAN)
    
    m.start_scan()

    tree = FileLogViewPanel(parent=win, candb= candb, log_ctx_mgr= ctx)
    layout.addWidget(tree)


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
            # start_report_thread()
            state["handle"] = handle
            print(f"Acquired: {channel.name}")

            # Create monitor panel
            monitor = CustomReplayPanel(
                parent=win,
                cnt_model=m,
                handle=handle,
				ctx_model=ctx
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

    # ---------------- UI Buttons ----------------

    btn_acquire = QPushButton("Acquire Channel")
    btn_release = QPushButton("Release Channel")

    btn_acquire.clicked.connect(test_acquire_chnl)
    btn_release.clicked.connect(test_release_chnl)

    layout.addWidget(btn_acquire)
    layout.addWidget(btn_release)
    layout.addStretch(1)

    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()