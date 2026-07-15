from typing import Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QListWidgetItem
from can_sdk.canlog_viewmodel import (
	LogContextManager,
	LogContext,
	MsgFilter,
	NoFilter,
	DecodeStatusChangedInfo,
)
from lw.logger_setup import LOG
from ui_sdk.components.pyqt.basic_component.CheckListSearch import CheckListSearch


class SignalFilterCheckList(CheckListSearch):
	def __init__(self, parent=None, ctx_model: LogContextManager | None = None):
		super().__init__()
		if parent is not None:
			self.setParent(parent)

		self._ctx_model = ctx_model
		self._current_ctx: Optional[LogContext] = None
		self._entries: list[tuple[int, int, str, str]] = []
		self._active_signal_keys: set[tuple[int, int]] = set()
		self._rebuilding = False
		self._ui_syncing = False

		self.list.itemChanged.connect(self._on_item_filter_changed)

		if self._ctx_model is not None:
			self._ctx_model.event_on_context_changed.subscribe(self._on_context_changed)
			self._ctx_model.event_on_decode_status_changed.subscribe(self._on_decode_status_changed)
			self._on_context_changed(self._ctx_model.cur_ctx)
		else:
			self._rebuild_items([])

	def _on_context_changed(self, ctx: Optional[LogContext]):
		self._current_ctx = ctx
		self._active_signal_keys = set()
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

		entries: list[tuple[int, int, str, str]] = []
		try:
			decode_pairs = list(getattr(ctx.dd_filelog, "decode_signal_list", []) or [])
			dbm = getattr(self._ctx_model, "mDBM", None) if self._ctx_model is not None else None
			if dbm is None:
				decode_pairs = []

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

				msg_info, sig_info = dbm.get_message_and_signal_info_by_signal_id(can_id, signal_id)
				if sig_info is None:
					continue

				signal_name = str(getattr(sig_info, "name", "") or "")
				message_name = str(getattr(msg_info, "name", "") or "")
				entries.append((can_id, signal_id, signal_name, message_name))
		except Exception:
			LOG.exception("Failed to reload signal entries from context")
			entries = []

		entries.sort(key=lambda item: (item[2].lower(), item[3].lower(), item[0], item[1]))
		self._entries = entries
		self._active_signal_keys &= {(can_id, signal_id) for can_id, signal_id, _, _ in entries}
		self._rebuild_items(self._entries)
		self._sync_ui_checks(self._active_signal_keys)

	def _format_display(self, can_id: int, signal_id: int, signal_name: str, message_name: str) -> str:
		if message_name:
			return f"{signal_name} - {message_name}"
		return f"{signal_name} (0x{int(can_id):X}:{int(signal_id)})"

	def _rebuild_items(self, entries: list[tuple[int, int, str, str]]):
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
			for can_id, signal_id, signal_name, message_name in entries:
				item = QListWidgetItem(self._format_display(can_id, signal_id, signal_name, message_name))
				item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
				item.setCheckState(Qt.Unchecked)
				item.setData(Qt.UserRole, (int(can_id), int(signal_id)))
				self.list.addItem(item)
		finally:
			self._reordering = False
			self._ui_syncing = False
			self._rebuilding = False

	def _checked_signal_keys_from_ui(self) -> list[tuple[int, int]]:
		result: list[tuple[int, int]] = []
		for i in range(self.list.count()):
			item = self.list.item(i)
			if item.checkState() != Qt.Checked:
				continue
			pair = item.data(Qt.UserRole)
			if pair is None:
				continue
			try:
				can_id, signal_id = pair
				result.append((int(can_id), int(signal_id)))
			except Exception:
				continue
		return result

	def _sync_ui_checks(self, checked_signal_keys: set[tuple[int, int]]):
		self._ui_syncing = True
		self._reordering = True
		try:
			for i in range(self.list.count()):
				item = self.list.item(i)
				pair = item.data(Qt.UserRole)
				should_check = False
				if pair is not None:
					try:
						can_id, signal_id = pair
						should_check = (int(can_id), int(signal_id)) in checked_signal_keys
					except Exception:
						should_check = False
				item.setCheckState(Qt.Checked if should_check else Qt.Unchecked)
		finally:
			self._reordering = False
			self._ui_syncing = False

	def _request_filter_update(self, checked_signal_keys: list[tuple[int, int]]):
		ctx = self._current_ctx
		if ctx is None:
			return

		can_ids: set[int] = set()
		for can_id, _signal_id in checked_signal_keys:
			try:
				can_ids.add(int(can_id))
			except Exception:
				continue

		normalized = sorted(can_ids)
		all_can_ids = sorted({int(can_id) for can_id, _signal_id, _signal_name, _msg_name in self._entries})

		try:
			if normalized == all_can_ids:
				ctx.set_filter_state(NoFilter())
			elif normalized:
				ctx.set_filter_state(MsgFilter(can_ids=normalized, mode=MsgFilter.Type.FILTER_MSG))
			else:
				ctx.set_filter_state(MsgFilter(can_ids=[], mode=MsgFilter.Type.FILTER_MSG))
		except Exception:
			LOG.exception("Failed to update current context filter from selected signals")

	def _on_item_filter_changed(self, _item: QListWidgetItem):
		if self._rebuilding or self._ui_syncing or self._reordering:
			return

		requested_checked_keys = self._checked_signal_keys_from_ui()
		self._active_signal_keys = set(requested_checked_keys)
		self._sync_ui_checks(self._active_signal_keys)
		self._request_filter_update(requested_checked_keys)

	def uncheck_all(self):
		super().uncheck_all()
		if self._rebuilding or self._ui_syncing:
			return
		self._active_signal_keys = set()
		self._request_filter_update([])

	def check_all(self):
		super().check_all()
		if self._rebuilding or self._ui_syncing:
			return
		all_keys = [(can_id, signal_id) for can_id, signal_id, _sig_name, _msg_name in self._entries]
		self._active_signal_keys = set(all_keys)
		self._request_filter_update(all_keys)
