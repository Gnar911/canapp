from typing import Optional, List, Union

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QListWidgetItem

from can_sdk.canlog_viewmodel import LogContextManager, LogContext, DecodeStatusChangedInfo
from can_sdk.data_object import SignalFilter
from lw.logger_setup import LOG
from ui_sdk.components.pyqt.basic_component.CheckListSearch import CheckListSearch

DataX = List[float]
DataY = List[Union[float, int]]
Identity = SignalFilter

class SignalGraphCheckList(CheckListSearch):
	"""
	PySide didn’t accept those typing aliases/custom class types in the signal declaration, 
	so it registered as a 0-arg signal; then emit(a, b, c) raised only accepts 0 argument(s), 3 given.
	"""
	valueSignalDataReady = Signal(object, object, object)
	choiceSignalDataReady = Signal(object, object, object)

	def __init__(self, parent=None, ctx_model: LogContextManager | None = None):
		super().__init__()
		if parent is not None:
			self.setParent(parent)

		self._ctx_model = ctx_model
		self._current_ctx: Optional[LogContext] = None
		self._entries: list[tuple[int, int, str]] = []
		self._rebuilding = False
		self._ui_syncing = False
		self._emitting = False

		self.search.setPlaceholderText("No context selected..")
		self.list.itemChanged.connect(self._on_item_toggled)

		if self._ctx_model is not None:
			self._ctx_model.event_on_context_changed.subscribe(self._on_context_changed)
			self._ctx_model.event_on_decode_status_changed.subscribe(self._on_decode_status_changed)
			self._on_context_changed(self._ctx_model.cur_ctx)
		else:
			self._rebuild_items([])

	def _on_context_changed(self, ctx: Optional[LogContext]):
		self._current_ctx = ctx
		self._reload_from_context(ctx)

	def _on_decode_status_changed(self, info: DecodeStatusChangedInfo):
		if info is None:
			return
		if not getattr(info, "completed", False):
			return
		if self._current_ctx is None:
			return
		if info.context is not self._current_ctx:
			return
		self._reload_from_context(self._current_ctx)

	def _reload_from_context(self, ctx: Optional[LogContext]):
		if ctx is None:
			self._entries = []
			self._rebuild_items([])
			return

		entries: list[tuple[int, int, str]] = []
		try:
			decode_pairs = list(getattr(ctx.dd_filelog, "decode_signal_list", []) or [])
			dbm = getattr(self._ctx_model, "mDBM", None) if self._ctx_model is not None else None

			if dbm is None or not decode_pairs:
				self._entries = []
				self._rebuild_items([])
				return

			seen: set[tuple[int, int]] = set()
			for can_id_raw, signal_id_raw in decode_pairs:
				try:
					can_id = int(can_id_raw)
					signal_id = int(signal_id_raw)
				except Exception:
					continue

				key = (can_id, signal_id)
				if key in seen:
					continue
				seen.add(key)

				_msg_info, sig_info = dbm.get_message_and_signal_info_by_signal_id(can_id, signal_id)
				if sig_info is None:
					continue

				signal_name = str(getattr(sig_info, "name", "") or "")
				if not signal_name:
					signal_name = f"0x{int(can_id):X}:{int(signal_id)}"
				entries.append((can_id, signal_id, signal_name))
		except Exception:
			LOG.exception("Failed to reload SignalGraphCheckList entries from context")
			entries = []

		entries.sort(key=lambda item: (item[2].lower(), item[0], item[1]))
		self._entries = entries
		self._rebuild_items(entries)

	def _rebuild_items(self, entries: list[tuple[int, int, str]]):
		self._rebuilding = True
		self._ui_syncing = True
		self._reordering = True
		try:
			self.list.clear()
			if not entries:
				if self._ctx_model is None or self._ctx_model.cur_ctx is None:
					self.search.setPlaceholderText("No context selected..")
				else:
					self.search.setPlaceholderText("0 decoded signals in context..")
				return

			self.search.setPlaceholderText(f"{len(entries)} decoded signals in context..")
			for can_id, signal_id, signal_name in entries:
				item = QListWidgetItem(signal_name)
				item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
				item.setCheckState(Qt.Unchecked)
				item.setData(Qt.UserRole, (int(can_id), int(signal_id), str(signal_name)))
				self._apply_item_visual_state(item)
				self.list.addItem(item)
		finally:
			self._reordering = False
			self._ui_syncing = False
			self._rebuilding = False

	def _on_item_toggled(self, item: QListWidgetItem):
		if self._rebuilding or self._ui_syncing or self._reordering or self._emitting:
			return

		payload = item.data(Qt.UserRole)
		if payload is None:
			return

		self._emitting = True
		try:
			can_id, signal_id, _signal_name = payload
			checked = item.checkState() == Qt.Checked
			if not checked:
				return

			can_id_i = int(can_id)
			signal_id_i = int(signal_id)
			msg_info, sig_info = self._resolve_signal_info(can_id_i, signal_id_i)
			is_choice = bool(getattr(sig_info, "choices", None)) if sig_info is not None else False
			signal_filter = SignalFilter(
				_signal_info=sig_info,
				_msg_info=msg_info,
				_rawvalue=None,
			)

			# ── Get timestamps from raw file by can_id ──
			timestamps = self._get_timestamps_by_can_id(can_id_i)

			if is_choice:
				raw_values = self._get_rawvalues(can_id_i, signal_id_i)
				LOG.debug(
					"SignalGraphCheckList tick -> choice signal=%s can_id=0x%X signal_id=%d x_len=%d y_len=%d",
					getattr(signal_filter, "sig_name", None),
					can_id_i,
					signal_id_i,
					len(timestamps),
					len(raw_values),
				)
				self.choiceSignalDataReady.emit(signal_filter, timestamps, raw_values)
			else:
				values = self._get_values(can_id_i, signal_id_i)
				LOG.debug(
					"SignalGraphCheckList tick -> value signal=%s can_id=0x%X signal_id=%d x_len=%d y_len=%d",
					getattr(signal_filter, "sig_name", None),
					can_id_i,
					signal_id_i,
					len(timestamps),
					len(values),
				)
				self.valueSignalDataReady.emit(signal_filter, timestamps, values)
		except Exception:
			LOG.exception("Failed to emit signal data from SignalGraphCheckList")
		finally:
			self._emitting = False

	def _resolve_signal_info(self, can_id: int, signal_id: int):
		dbm = getattr(self._ctx_model, "mDBM", None) if self._ctx_model is not None else None
		if dbm is None:
			return None, None
		try:
			return dbm.get_message_and_signal_info_by_signal_id(int(can_id), int(signal_id))
		except Exception:
			LOG.exception(
				"Failed to resolve signal info for can_id=%s signal_id=%s",
				can_id,
				signal_id,
			)
			return None, None

	# ────────────────────────────────────────────────────────────────────
	#  Data fetchers — decode file for values, raw file for timestamps
	# ────────────────────────────────────────────────────────────────────

	def _get_values(self, can_id: int, signal_id: int) -> list[float]:
		"""Get value list from decode file only."""
		ctx = self._current_ctx
		if ctx is None:
			return []
		decoded = getattr(ctx, "dd_filelog", None)
		if decoded is None:
			return []
		try:
			return decoded.get_signal_value_list_by_key(int(can_id), int(signal_id))
		except Exception:
			LOG.exception("Failed to get value list for can_id=%s signal_id=%s", can_id, signal_id)
			return []

	def _get_rawvalues(self, can_id: int, signal_id: int) -> list[int]:
		"""Get raw-value list from decode file only."""
		ctx = self._current_ctx
		if ctx is None:
			return []
		decoded = getattr(ctx, "dd_filelog", None)
		if decoded is None:
			return []
		try:
			return decoded.get_signal_rawvalue_list_by_key(int(can_id), int(signal_id))
		except Exception:
			LOG.exception("Failed to get rawvalue list for can_id=%s signal_id=%s", can_id, signal_id)
			return []

	def _get_timestamps_by_can_id(self, can_id: int) -> list[float]:
		"""Get timestamp list from raw file by can_id."""
		ctx = self._current_ctx
		if ctx is None:
			return []
		raw = getattr(ctx, "d_filelog", None)
		if raw is None:
			return []
		try:
			return raw.get_timestamps_by_can_id(int(can_id))
		except Exception:
			LOG.exception("Failed to get timestamp list for can_id=%s", can_id)
			return []

	def _is_choice_signal(self, can_id: int, signal_id: int) -> bool:
		try:
			_msg_info, sig_info = self._resolve_signal_info(int(can_id), int(signal_id))
			if sig_info is None:
				return False
			choices = getattr(sig_info, "choices", None)
			return bool(choices)
		except Exception:
			LOG.exception(
				"Failed to detect signal type for can_id=%s signal_id=%s",
				can_id,
				signal_id,
			)
			return False

if __name__ == "__main__":
	import sys
	from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout
	from can_sdk.canlog_viewmodel import LogContextViewModel
	from can_sdk.test_ultility import TEST_set_up_1_context
	from lw.logger_setup import setup_logger
	setup_logger(env="DEV", backup_count=30)
	ctx_model = TEST_set_up_1_context()
	app = QApplication(sys.argv)
	root = QWidget()
	root.setWindowTitle("SignalGraphCheckList Manual Test")
	layout = QVBoxLayout(root)

	checklist = SignalGraphCheckList(parent=root, ctx_model=ctx_model)
	layout.addWidget(checklist)

	def _on_value(identity: Identity, x_data: DataX, y_data: DataY):
		LOG.info("MAIN_TEST value data: signal=%s x=%d y=%d", identity.sig_name if identity else None, len(x_data), len(y_data))

	def _on_choice(identity: Identity, x_data: DataX, y_data: DataY):
		LOG.info("MAIN_TEST choice data: signal=%s x=%d y=%d", identity.sig_name if identity else None, len(x_data), len(y_data))

	checklist.valueSignalDataReady.connect(_on_value)
	checklist.choiceSignalDataReady.connect(_on_choice)

	root.resize(520, 700)
	root.show()
	sys.exit(app.exec())