from typing import Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QListWidgetItem
from can_sdk.canlog_viewmodel import LogContextManager, LogContext, MsgFilter, NoFilter, FilterState
from lw.logger_setup import LOG
from ui_sdk.components.pyqt.basic_component.CheckListSearch import CheckListSearch

class MessageFilterCheckList(CheckListSearch):
	def __init__(self, parent=None, ctx_model: LogContextManager | None = None):
		super().__init__()
		if parent is not None:
			self.setParent(parent)

		self._ctx_model = ctx_model
		self._current_ctx: Optional[LogContext] = None
		self._entries: list[int] = []
		self._active_filter_ids: set[int] = set()
		self._rebuilding = False
		self._ui_syncing = False
		self._subscribed_ctx_ids: set[int] = set()

		self.list.itemChanged.connect(self._on_item_filter_changed)

		if self._ctx_model is not None:
			self._ctx_model.event_on_context_changed.subscribe(self._on_context_changed)
			self._on_context_changed(self._ctx_model.cur_ctx)
		else:
			self._rebuild_items([])

	def _on_context_changed(self, ctx: Optional[LogContext]):
		self._current_ctx = ctx

		if ctx is None:
			self._entries = []
			self._active_filter_ids = set()
			self._rebuild_items([])
			return

		self._subscribe_ctx_filter_event(ctx)
		self._reload_from_context(ctx)
		self._apply_filter_state_to_ui(getattr(ctx, "filter_state", NoFilter()))

	def _subscribe_ctx_filter_event(self, ctx: LogContext):
		ctx_id = id(ctx)
		if ctx_id in self._subscribed_ctx_ids:
			return
		ctx.event_on_filter_state_changed.subscribe(
			lambda state, source_ctx=ctx: self._on_filter_state_changed(source_ctx, state)
		)
		self._subscribed_ctx_ids.add(ctx_id)

	def _on_filter_state_changed(self, source_ctx: LogContext, state: FilterState):
		if source_ctx is not self._current_ctx:
			return
		self._apply_filter_state_to_ui(state)

	def _reload_from_context(self, ctx: Optional[LogContext]):
		if ctx is None:
			self._entries = []
			self._rebuild_items([])
			return

		try:
			can_ids = ctx.d_filelog.get_all_can_ids()
			normalized = sorted({int(can_id) for can_id in can_ids})
		except Exception:
			normalized = []

		self._entries = normalized
		self._rebuild_items(self._entries)

	def _format_display(self, can_id: int) -> str:
		message_name = ""
		try:
			if self._ctx_model is not None and getattr(self._ctx_model, "mDBM", None) is not None:
				message_name = self._ctx_model.mDBM.get_message_name(int(can_id)) or ""
		except Exception:
			message_name = ""
		return f"0x{int(can_id):X} - {message_name}"

	def _rebuild_items(self, can_ids: list[int]):
		self._rebuilding = True
		self._ui_syncing = True
		self._reordering = True
		try:
			self.list.clear()
			if not can_ids:
				if self._ctx_model is None or self._ctx_model.cur_ctx is None:
					self.search.setPlaceholderText("No context selected..")
				else:
					self.search.setPlaceholderText("0 messages in context..")
				return

			self.search.setPlaceholderText(f"{len(can_ids)} messages in context..")
			for can_id in can_ids:
				item = QListWidgetItem(self._format_display(int(can_id)))
				item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
				item.setCheckState(Qt.Unchecked)
				item.setData(Qt.UserRole, int(can_id))
				self.list.addItem(item)
		finally:
			self._reordering = False
			self._ui_syncing = False
			self._rebuilding = False

	def _checked_can_ids_from_ui(self) -> list[int]:
		result: list[int] = []
		for i in range(self.list.count()):
			item = self.list.item(i)
			if item.checkState() != Qt.Checked:
				continue
			can_id = item.data(Qt.UserRole)
			if can_id is None:
				continue
			try:
				result.append(int(can_id))
			except Exception:
				continue
		return result

	def _sync_ui_checks(self, checked_can_ids: set[int]):
		self._ui_syncing = True
		self._reordering = True
		try:
			for i in range(self.list.count()):
				item = self.list.item(i)
				can_id = item.data(Qt.UserRole)
				should_check = False
				if can_id is not None:
					try:
						should_check = int(can_id) in checked_can_ids
					except Exception:
						should_check = False
				item.setCheckState(Qt.Checked if should_check else Qt.Unchecked)
		finally:
			self._reordering = False
			self._ui_syncing = False

	def _apply_filter_state_to_ui(self, state: FilterState):
		if isinstance(state, NoFilter):
			checked_ids: set[int] = set(self._entries)
		elif isinstance(state, MsgFilter):
			checked_ids = set()
			for can_id in state.can_ids:
				try:
					checked_ids.add(int(can_id))
				except Exception:
					continue
		else:
			checked_ids = set()
		self._active_filter_ids = checked_ids
		self._sync_ui_checks(self._active_filter_ids)

	def _request_filter_update(self, checked_ids: list[int]):
		ctx = self._current_ctx
		if ctx is None:
			return
		try:
			normalized = sorted({int(can_id) for can_id in checked_ids})
		except Exception:
			normalized = []

		try:
			all_ids = sorted({int(can_id) for can_id in self._entries})
			if normalized == all_ids:
				ctx.set_filter_state(NoFilter())
			elif normalized:
				ctx.set_filter_state(MsgFilter(can_ids=normalized, mode=MsgFilter.Type.FILTER_MSG))
			else:
				ctx.set_filter_state(MsgFilter(can_ids=[], mode=MsgFilter.Type.FILTER_MSG))
		except Exception:
			LOG.exception("Failed to update current context message filter state")

	def _on_item_filter_changed(self, _item: QListWidgetItem):
		if self._rebuilding or self._ui_syncing or self._reordering:
			return

		requested_checked_ids = self._checked_can_ids_from_ui()
		self._sync_ui_checks(self._active_filter_ids)
		self._request_filter_update(requested_checked_ids)

	def uncheck_all(self):
		super().uncheck_all()
		if self._rebuilding or self._ui_syncing:
			return
		self._request_filter_update([])

	def check_all(self):
		super().check_all()
		if self._rebuilding or self._ui_syncing:
			return
		self._request_filter_update(list(self._entries))
