from typing import Optional, Union, Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QListWidgetItem

from can_sdk.canlog_viewmodel import LogContextManager, LogContext, NoFilter
from lw.logger_setup import LOG
from ui_sdk.components.pyqt.basic_component.CheckListSearch import CheckListSearch

ChannelType = Union[str, int]


class ChannelFilterCheckList(CheckListSearch):
	"""
	Checklist for filtering current log context by channel.

	- Parent: CheckListSearch (list-only mode)
	- Model: LogContextManager
	- DataModel: ChannelType = Union[str, int]
	- Events:
		* event_on_context_changed: reload channels
		* event_on_filter_state_changed: sync checkbox UI state
	- UX rule: checkbox UI is updated only from filter-state event callbacks.
	"""

	def __init__(self, parent=None, ctx_model: LogContextManager | None = None):
		super().__init__(show_controls=False)
		if parent is not None:
			self.setParent(parent)

		self._ctx_model = ctx_model
		self._current_ctx: Optional[LogContext] = None
		self._entries: list[ChannelType] = []
		self._active_channels: set[ChannelType] = set()
		self._rebuilding = False
		self._ui_syncing = False
		self._subscribed_ctx_ids: set[int] = set()

		self.list.itemChanged.connect(self._on_item_filter_changed)

		if self._ctx_model is not None:
			self._ctx_model.event_on_context_changed.subscribe(self._on_context_changed)
			self._on_context_changed(self._ctx_model.cur_ctx)
		else:
			self._rebuild_items([])

	# ---------------------------
	# Event handling
	# ---------------------------
	def _on_context_changed(self, ctx: Optional[LogContext]):
		self._current_ctx = ctx

		if ctx is None:
			self._entries = []
			self._active_channels = set()
			self._rebuild_items([])
			return

		self._subscribe_ctx_filter_event(ctx)
		self._reload_from_context(ctx)
		self._apply_filter_state_to_ui(getattr(ctx, "filter_state", None))

	def _subscribe_ctx_filter_event(self, ctx: LogContext):
		ctx_id = id(ctx)
		if ctx_id in self._subscribed_ctx_ids:
			return
		ctx.event_on_filter_state_changed.subscribe(
			lambda state, source_ctx=ctx: self._on_filter_state_changed(source_ctx, state)
		)
		self._subscribed_ctx_ids.add(ctx_id)

	def _on_filter_state_changed(self, source_ctx: LogContext, state: Any):
		if source_ctx is not self._current_ctx:
			return
		self._apply_filter_state_to_ui(state)

	# ---------------------------
	# Data reload + formatting
	# ---------------------------
	def _reload_from_context(self, ctx: Optional[LogContext]):
		if ctx is None:
			self._entries = []
			self._rebuild_items([])
			return

		d_filelog = getattr(ctx, "d_filelog", None)
		entries = self._extract_channels(d_filelog)
		self._entries = entries
		self._rebuild_items(self._entries)

	def _extract_channels(self, d_filelog: Any) -> list[ChannelType]:
		if d_filelog is None:
			return []

		raw_values = []
		try:
			if hasattr(d_filelog, "get_all_channels"):
				raw_values = list(d_filelog.get_all_channels() or [])
			elif hasattr(d_filelog, "channels"):
				raw_values = list(getattr(d_filelog, "channels") or [])
		except Exception:
			raw_values = []

		normalized: list[ChannelType] = []
		seen: set[ChannelType] = set()
		for value in raw_values:
			channel = self._normalize_channel(value)
			if channel is None or channel in seen:
				continue
			seen.add(channel)
			normalized.append(channel)
		return normalized

	def _normalize_channel(self, value: Any) -> Optional[ChannelType]:
		if value is None:
			return None
		if isinstance(value, int):
			return int(value)
		if isinstance(value, str):
			txt = value.strip()
			if not txt:
				return None
			if txt.isdigit():
				try:
					return int(txt)
				except Exception:
					return txt
			return txt
		try:
			as_int = int(value)
			return as_int
		except Exception:
			try:
				txt = str(value).strip()
				return txt if txt else None
			except Exception:
				return None

	def _format_display(self, channel: ChannelType) -> str:
		return f"<{channel}>"

	def _rebuild_items(self, channels: list[ChannelType]):
		self._rebuilding = True
		self._ui_syncing = True
		self._reordering = True
		try:
			self.list.clear()
			for channel in channels:
				item = QListWidgetItem(self._format_display(channel))
				item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
				item.setCheckState(Qt.Unchecked)
				item.setData(Qt.UserRole, channel)
				self._apply_item_visual_state(item)
				self.list.addItem(item)
		finally:
			self._reordering = False
			self._ui_syncing = False
			self._rebuilding = False

	# ---------------------------
	# UI <-> state mapping
	# ---------------------------
	def _checked_channels_from_ui(self) -> list[ChannelType]:
		result: list[ChannelType] = []
		for i in range(self.list.count()):
			item = self.list.item(i)
			if item.checkState() != Qt.Checked:
				continue
			channel = self._normalize_channel(item.data(Qt.UserRole))
			if channel is None:
				continue
			result.append(channel)
		return result

	def _sync_ui_checks(self, checked_channels: set[ChannelType]):
		self._ui_syncing = True
		self._reordering = True
		try:
			for i in range(self.list.count()):
				item = self.list.item(i)
				channel = self._normalize_channel(item.data(Qt.UserRole))
				should_check = channel in checked_channels if channel is not None else False
				item.setCheckState(Qt.Checked if should_check else Qt.Unchecked)
				self._apply_item_visual_state(item)
		finally:
			self._reordering = False
			self._ui_syncing = False

	def _extract_channels_from_state(self, state: Any) -> Optional[set[ChannelType]]:
		if state is None:
			return None
		if isinstance(state, NoFilter):
			return set(self._entries)

		raw_channels = None
		if hasattr(state, "channels"):
			raw_channels = getattr(state, "channels", None)
		elif hasattr(state, "channel"):
			raw_channels = [getattr(state, "channel")]

		if raw_channels is None:
			return None

		normalized: set[ChannelType] = set()
		for value in raw_channels:
			channel = self._normalize_channel(value)
			if channel is not None:
				normalized.add(channel)
		return normalized

	def _apply_filter_state_to_ui(self, state: Any):
		next_active = self._extract_channels_from_state(state)
		if next_active is None:
			return
		next_active &= set(self._entries)
		self._active_channels = next_active
		self._sync_ui_checks(self._active_channels)

	# ---------------------------
	# Request flow (user action -> model API)
	# ---------------------------
	def _resolve_api_owner(self) -> Any:
		ctx = self._current_ctx
		if ctx is None:
			return None
		if hasattr(ctx, "get_page_from_channels_row_indices"):
			return ctx
		d_filelog = getattr(ctx, "d_filelog", None)
		if hasattr(d_filelog, "get_page_from_channels_row_indices"):
			return d_filelog
		return None

	def _resolve_page_request(self, owner: Any, channels: list[ChannelType]) -> tuple[int, int]:
		first_line = 0
		for attr in ("first_line", "first_row", "page_first_line", "current_first_line"):
			if hasattr(owner, attr):
				try:
					first_line = max(0, int(getattr(owner, attr)))
					break
				except Exception:
					continue

		total_count = 0
		try:
			if hasattr(owner, "get_total_count_by_channels"):
				total_count = int(owner.get_total_count_by_channels(channels) or 0)
		except Exception:
			total_count = 0

		page_size = 0
		for attr in ("page_size", "page_limit", "window_size", "current_page_size"):
			if hasattr(owner, attr):
				try:
					page_size = int(getattr(owner, attr) or 0)
					if page_size > 0:
						break
				except Exception:
					continue
		if page_size <= 0:
			page_size = max(1, total_count) if total_count > 0 else 1
		return first_line, page_size

	def _request_channel_view_update(self, channels: list[ChannelType]):
		owner = self._resolve_api_owner()
		if owner is None:
			return

		normalized: list[ChannelType] = []
		seen: set[ChannelType] = set()
		for value in channels:
			channel = self._normalize_channel(value)
			if channel is None or channel in seen:
				continue
			seen.add(channel)
			normalized.append(channel)

		try:
			if len(normalized) == 1:
				if hasattr(owner, "get_row_indices_by_channel"):
					owner.get_row_indices_by_channel(normalized[0])
			elif hasattr(owner, "get_row_indices_by_channels"):
				owner.get_row_indices_by_channels(normalized)

			first_line, page_size = self._resolve_page_request(owner, normalized)
			if hasattr(owner, "get_page_from_channels_row_indices"):
				owner.get_page_from_channels_row_indices(normalized, first_line, page_size)
		except Exception:
			LOG.exception("Failed to request channel-filtered page update")

	def _on_item_filter_changed(self, _item: QListWidgetItem):
		if self._rebuilding or self._ui_syncing or self._reordering:
			return

		requested_channels = self._checked_channels_from_ui()
		self._sync_ui_checks(self._active_channels)
		self._request_channel_view_update(requested_channels)

