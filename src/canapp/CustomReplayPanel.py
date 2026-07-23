import os
from typing import Any, Optional, Set, List
from PySide6 import QtCore, QtWidgets
from PySide6.QtCore import Qt, QSortFilterProxyModel
from PySide6.QtWidgets import QWidget
from canapp.data_object import CANLogLine, SignalFilter
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QMessageBox, QApplication)
from canapp.vm.replay_view_model import ReplayViewModel
from lw.logger_setup import LOG, setup_logger
from lw.qt.declarative import bind
from canapp.widgets.basic_component.CollapsibleSection import CollapsibleSection 
from canapp.widgets.ReplayTimescopeSlider import ReplayTimescopeSlider
#from canapp.widgets.basic_component.CheckListSearch import CheckListSearch 
# from canapp.data_object import CANLogLine
from PySide6.QtGui import QStandardItemModel, QStandardItem

# from canapp.global_event import event_on_signal_select

class CustomReplayPanel(QtWidgets.QWidget):
	replay_status_signal = QtCore.Signal(object)

	def __init__(
		self,
		vm: ReplayViewModel,
		parent: QWidget,
	):
		super().__init__(parent)
		self.vm = vm
		#self._selected_signal_can_id: Optional[int] = None
		#self._replay_lines: list[CANLogLine] = []
		#self._replay_status: str = "IDLE"
		self._completed_cycles: int = 0
		self.replay_status_signal.connect(self._handle_replay_status_on_ui, Qt.QueuedConnection)

		self._build_ui()

		""" NOTE: Viewmodel do not understand the if the UI using toggle -> we can not make self.vm.toggleReplay"""
		# self.btn_replay.clicked.connect(self._on_click_replay_or_pause)
		self.btn_replay.clicked.connect(
			lambda: self.vm.pauseReplay()
			if self.vm.isReplay
			else 
			#NOTE: Otherwise at stop or pause state, simply reset to initial action
			self.vm.startReplay()
		)
		self.btn_stop.clicked.connect(lambda: self.vm.stopReplay())

		""" NOTE: QCheckBox.toggled already emits a bool
		User checks checkbox
			↓
		toggled(True)
			↓
		vm.setLoop(True)

		User unchecks checkbox
			↓
		toggled(False)
			↓
		vm.setLoop(False)
		"""
		self.tg_loop.toggled.connect(self.vm.setLoop)
		""" NOTE: Do not need self.spin_repeat.value()"""
		self.spin_repeat.valueChanged.connect(self.vm.setRepeat)
		self.spin_repeat.textChanged.connect(self._on_repeat_text_changed)
		self.msg_model.itemChanged.connect(
		lambda item: self.vm.setMsgIdFilter(
			item.data(Qt.UserRole),
		)
		)
		""" NOTE: Time scope is on developing"""
		# self.scope_slider.valueChanged.connect(self.vm.setTimeScope)
		# self.scope_slider.handleIndexChanged.connect(self._on_handle_index_changed)

		""" NOTE:  
			QML has a real binding engine:
			Button {
				enabled: vm.isHavingDevice && vm.isHavingRecord
				text: vm.isReplay ? "Pause" : "Replay"

				onClicked: vm.toggleReplay()
			}
			You don't manually call:
			button.setText(...)

			That's called declarative UI

				DECLARATIVE UI PARADIGM
						   │
			┌──────────────┼──────────────────┐
			▼              ▼                  ▼
		QML         Jetpack Compose       SwiftUI
		Qt             Android             Apple

			▼              ▼                  ▼
		XAML           React              Flutter
	.NET/WPF/etc.       Web               Dart

		"""
		""" NOTE: isStop or isPause => Replay
			if self.vm.isReplay:
				self.btn_replay.setText("Pause")

			elif self.vm.isPause:
				self.btn_replay.setText("Replay")

			elif self.vm.isStop:
				self.btn_replay.setText("Replay")
		"""
		bind(
			self.vm.replayStateChanged,
			self.btn_replay.setText,
			lambda: "Pause" if self.vm.isReplay else "Replay",
		)

		bind(
			self.vm.replayStateChanged,
			self.btn_replay.setEnabled,
			lambda: (
				self.vm.isHavingDevice
				and self.vm.isHavingRecord
			),
		)

		bind(
			self.vm.replayStateChanged,
			self.tg_loop.setChecked,
			lambda: self.vm.isLoopOn,
		)

		bind(
			self.vm.replayStateChanged,
			self.tg_loop.setText,
			lambda: "LoopON" if self.vm.isLoopOn else "LoopOFF",
		)

		bind(
			self.vm.replayStateChanged,
			self.lb_cycle_status.setText, 
			f"Completed: {self.vm.currentCycle}/∞",
		)

		""" NOTE: it could be callable at binding time -> lambda
		bind(
			self.vm.replayStateChanged,
			self.lb_target_logfile.setText, 
			f"Target logfile: {self.vm.targetLog}",
		)
		"""
		bind(
			self.vm.replayStateChanged,
			self.lb_target_logfile.setText,
			lambda: f"Target logfile: {self.vm.targetLog}",
		)

		self.vm.replayStateChanged.connect(
			lambda: (
				self.msg_model.clear(),
				self.msg_model.invisibleRootItem().appendRows(
    			self.vm.inLogMessageLists)
				)
		)

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

		self.btn_replay = QtWidgets.QPushButton()
		self.btn_stop = QtWidgets.QPushButton("Stop")
		self.tg_loop = QtWidgets.QCheckBox()
		""" NOTE: Initial UI state should be bind with the VM state at runtime"""
		self.lb_cycle_status = QtWidgets.QLabel()
		self.lb_target_logfile = QtWidgets.QLabel()
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

		self.repeat_widget.setVisible(True)

		main_layout.addWidget(control_box)

		filter_container = QtWidgets.QWidget(self)
		filter_layout = QtWidgets.QVBoxLayout(filter_container)
		filter_layout.setContentsMargins(0, 0, 0, 0)
		filter_layout.setSpacing(8)

		msg_section = CollapsibleSection("Filter Message Replay", expanded=False)
		msg_section.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Maximum)
		msg_content_layout = QtWidgets.QVBoxLayout()
		msg_content_layout.setContentsMargins(0, 0, 0, 0)

		self.msg_search = QtWidgets.QLineEdit()
		self.msg_search.setPlaceholderText("Search…")
		self.msg_list = QtWidgets.QListView()
		self.msg_model = QStandardItemModel(self)
		self.msg_proxy = QSortFilterProxyModel(self)
		self.msg_proxy.setSourceModel(self.msg_model)
		self.msg_proxy.setFilterCaseSensitivity(
			Qt.CaseSensitivity.CaseInsensitive
		)
		self.msg_list.setModel(self.msg_proxy)
		self.msg_search.textChanged.connect(
			self.msg_proxy.setFilterFixedString
		)
		self.msg_list.setSelectionMode(
			QtWidgets.QAbstractItemView.SelectionMode.NoSelection
		)
		self.msg_list.setSizePolicy(
			QtWidgets.QSizePolicy.Policy.Expanding,
			QtWidgets.QSizePolicy.Policy.Preferred,
		)
		msg_content_layout.addWidget(self.msg_list, 1)
		msg_section.setContentLayout(msg_content_layout)

		""" NOTE: Time scope is on developing"""
		# scope_section = CollapsibleSection("Time Scope Replay", expanded=False)
		# scope_section.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Maximum)
		# scope_content_layout = QtWidgets.QVBoxLayout()
		# scope_content_layout.setContentsMargins(0, 0, 0, 0)
		# scope_group = QtWidgets.QGroupBox("")
		# scope_group_layout = QtWidgets.QVBoxLayout(scope_group)
		# scope_group_layout.setContentsMargins(6, 6, 6, 6)
		# self.scope_slider = ReplayTimescopeSlider(player=self.player, ctx_model=self.ctx_model)
		# scope_group_layout.addWidget(self.scope_slider)
		# scope_content_layout.addWidget(scope_group)
		# scope_section.setContentLayout(scope_content_layout)

		filter_layout.addWidget(msg_section)
		# filter_layout.addWidget(scope_section)
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

	# def _selected_message_ids(self) -> list[int]:
	# 	checklist = getattr(self, "msg_check_list", None)
	# 	if checklist is None:
	# 		return []
	# 	getter = getattr(checklist, "_checked_can_ids", None)
	# 	if callable(getter):
	# 		try:
	# 			return [int(can_id) for can_id in getter()]
	# 		except Exception:
	# 			return []
	# 	return []

	# def _refresh_loop_toggle_text(self):
	# 	self.tg_loop.setText("LoopON" if self.tg_loop.isChecked() else "LoopOFF")

	# def _update_cycle_status_label(self, total_override=None):
	# 	if self.tg_loop.isChecked():
	# 		total_text = "∞"
	# 	else:
	# 		if total_override not in (None, ""):
	# 			try:
	# 				total_text = str(max(1, int(total_override)))
	# 			except Exception:
	# 				total_text = str(self.spin_repeat.value())
	# 		else:
	# 			total_text = str(self.spin_repeat.value())
	# 	self.lb_cycle_status.setText(f"Completed: {max(0, int(self._completed_cycles))}/{total_text}")

	def _set_replay_inputs_enabled(self, enabled: bool):
		self.tg_loop.setEnabled(enabled)
		self.spin_repeat.setEnabled(enabled)

	# def _apply_replay_config_to_player(self):
	# 	if not self.player:
	# 		return
	# 	self.player.set_loop(self.tg_loop.isChecked())
	# 	self.player.set_repeat(self.spin_repeat.value())

	# def _on_time_scope_changed(self, start_ts: float, end_ts: float):
	# 	if self.player:
	# 		self.player.set_time_scope(start_ts, end_ts)

	# def _on_handle_index_changed(self, handle_id: int, index: int):
	# 	if hasattr(self, "replay_logfile") and self.replay_logfile:
	# 		self.replay_logfile.trigger_focus_to_row(index)

	# def _on_click_replay_or_pause(self):
	# 	if not self.player:
	# 		LOG.warning("[ReplayPanel] click ignored: player is None")
	# 		return
	# 	process_alive = bool(getattr(self.player, "process", None) and self.player.process.is_alive())
	# 	LOG.debug(
	# 		"[ReplayPanel] click action state=%s process_alive=%s",
	# 		self._replay_status,
	# 		process_alive,
	# 	)
	# 	if not process_alive:
	# 		LOG.error("[ReplayPanel] replay process is not alive; click ignored")
	# 		return
	# 	self._apply_replay_config_to_player()
	# 	if self._replay_status in ("STARTED", "RESUMED"):
	# 		self.player.pause()
	# 		return
	# 	if self._replay_status == "PAUSED":
	# 		self.player.resume()
	# 		return
	# 	#row_indices = self._effective_row_indices_for_replay(from_filter)
	# 	LOG.debug("_on_click_replay_or_pause")
	# 	if not hasattr(self, "replay_logfile") or self.replay_logfile is None:
	# 		LOG.warning("[ReplayPanel] click ignored: no replay target selected")
	# 		return
	# 	try:
	# 		filter_can_ids = self._selected_message_ids() or None
	# 		self.player.start_replay_context(self.replay_logfile, filter_can_ids=filter_can_ids)
	# 	except Exception:
	# 		LOG.exception("[ReplayPanel] failed to start replay context")

	# def _on_loop_toggled(self, enabled: bool):
	# 	self._refresh_loop_toggle_text()
	# 	if hasattr(self, "repeat_widget"):
	# 		self.repeat_widget.setVisible(not enabled)
	# 	self._completed_cycles = 0
	# 	self._update_cycle_status_label()
	# 	if self.player:
	# 		self.player.set_loop(enabled)

	def _on_repeat_text_changed(self, text: str):
		if self.tg_loop.isChecked():
			return
		try:
			num = int(text)
		except Exception:
			num = self.spin_repeat.value()
		self._update_cycle_status_label(total_override=max(1, num))

	# def _on_filter_mode_changed(self):
	# 	if self.player:
	# 		msg_ids = self._selected_message_ids()
	# 		self.player.set_msg_id_filter(msg_ids if msg_ids else None)

	def on_event_signal_select(self, data: Optional[SignalFilter]):
		if data is None:
			return
		self._selected_signal_can_id = data.can_id

	# def on_event_filter_changed(self, data: list[CANLogLine]):
	# 	# Update time scope
	# 	self._replay_lines = list(data)
	# 	timestamps = self.replay_logfile.datalog.get_timestamps_of_target_log_line(self._replay_lines)
	# 	self.scope_slider.set_timestamps(timestamps)

	# # Statuses that represent an actual state change (used to track _replay_status)
	# _STATE_STATUSES = frozenset((
	# 	"STARTED", "RESUMED", "PAUSED", "STOPPED",
	# 	"FINISHED", "TIME_SCOPE_FINISHED", "IDLE", "EXIT",
	# ))
