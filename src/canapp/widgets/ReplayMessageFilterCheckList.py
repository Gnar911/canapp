from typing import Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QListWidgetItem
from can_sdk.canlog_viewmodel import LogContextManager, LogContext
from can_sdk.replay_viewmodel import CANLogPlayer, ReplayStatus
from lw.logger_setup import LOG
from ui_sdk.components.pyqt.basic_component.CheckListSearch import CheckListSearch

class ReplayMessageFilterCheckList(CheckListSearch):
	def __init__(
		self,
		parent=None,
		ctx_model: LogContextManager | None = None,
		player: CANLogPlayer | None = None,
	):
		super().__init__()
		if parent is not None:
			self.setParent(parent)

		self._ctx_model = ctx_model
		self._player = player
		self._rebuilding = False
		self._ui_syncing = False
		self._entries: list[int] = []
		self._ignored_ids: set[int] = set()
		self._subscribed_player_ids: set[int] = set()

		# Additional hook beyond CheckListSearch._on_item_changed
		self.list.itemChanged.connect(self._on_item_filter_changed)
		self._subscribe_player_status_event(self._player)

		if self._ctx_model is not None:
			self._ctx_model.event_on_context_changed.subscribe(self._on_context_changed)
			self._reload_from_context(self._ctx_model.cur_ctx)
		else:
			self._rebuild_items([])

	# ---------------------------
	# Public API
	# ---------------------------
	def set_player(self, player: CANLogPlayer | None):
		self._player = player
		self._subscribe_player_status_event(player)
		self._request_ignore_filter_update(self._ignored_ids)

	# ---------------------------
	# Internal
	# ---------------------------
	def _on_context_changed(self, ctx: Optional[LogContext]):
		self._reload_from_context(ctx)

	def _subscribe_player_status_event(self, player: CANLogPlayer | None):
		if player is None:
			return
		player_id = id(player)
		if player_id in self._subscribed_player_ids:
			return
		player.event_on_replay_status_changed.subscribe(self._on_player_status_changed)
		self._subscribed_player_ids.add(player_id)

	def _on_player_status_changed(self, status: ReplayStatus):
		if status is None or getattr(status, "status", None) != "FILTER_MSG":
			return

		payload = getattr(status, "payload", {}) or {}
		incoming_ignored = payload.get("ignored_msg_ids", [])
		normalized_ignored: set[int] = set()
		for can_id in incoming_ignored:
			try:
				normalized_ignored.add(int(can_id))
			except Exception:
				continue

		if self._entries:
			normalized_ignored &= set(self._entries)

		self._ignored_ids = normalized_ignored
		self._apply_ignored_ids_to_ui(self._ignored_ids)

	def _reload_from_context(self, ctx: Optional[LogContext]):
		if ctx is None:
			self._entries = []
			self._ignored_ids = set()
			self._rebuild_items([])
			return

		try:
			can_ids = ctx.d_filelog.can_ids
			normalized = sorted({int(can_id) for can_id in can_ids})
		except Exception:
			normalized = []

		self._entries = normalized
		self._ignored_ids = set()
		self._rebuild_items(self._entries)

	def _format_display(self, can_id: int) -> str:
		return f"0x{int(can_id):X} - {self._ctx_model.mDBM.get_message_name(can_id)}"

	def _rebuild_items(self, can_ids: list[int]):
		self._rebuilding = True
		self._ui_syncing = True
		self._reordering = True
		try:
			self.list.clear()
			if not can_ids:
				if self._ctx_model is None or self._ctx_model.cur_ctx is None:
					self.search.setPlaceholderText("No log file selected..")
				else:
					self.search.setPlaceholderText("0 messages in log file..")
				return

			self.search.setPlaceholderText(f"{len(can_ids)} messages in log file..")
			for can_id in can_ids:
				item = QListWidgetItem(self._format_display(int(can_id)))
				item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
				item.setCheckState(Qt.Checked)
				self._apply_item_visual_state(item)
				item.setData(Qt.UserRole, int(can_id))
				self.list.addItem(item)
		finally:
			self._reordering = False
			self._ui_syncing = False
			self._rebuilding = False

		# Reset ignore filter on context change (ignore none), then wait for FILTER_MSG status.
		self._request_ignore_filter_update(set())

	def _checked_can_ids(self) -> set[int]:
		ids: set[int] = set()
		for i in range(self.list.count()):
			item = self.list.item(i)
			if item.checkState() != Qt.Checked:
				continue
			can_id = item.data(Qt.UserRole)
			if can_id is None:
				continue
			try:
				ids.add(int(can_id))
			except Exception:
				continue
		return ids

	def _apply_ignored_ids_to_ui(self, ignored_ids: set[int]):
		checked_ids = set(self._entries) - set(ignored_ids)
		self._ui_syncing = True
		self._reordering = True
		try:
			for i in range(self.list.count()):
				item = self.list.item(i)
				can_id = item.data(Qt.UserRole)
				should_check = False
				if can_id is not None:
					try:
						should_check = int(can_id) in checked_ids
					except Exception:
						should_check = False
				item.setCheckState(Qt.Checked if should_check else Qt.Unchecked)
				self._apply_item_visual_state(item)
		finally:
			self._reordering = False
			self._ui_syncing = False

	def _request_ignore_filter_update(self, ignored_ids: set[int]):
		if self._player is None:
			return
		normalized = sorted({int(can_id) for can_id in ignored_ids})
		try:
			self._player.set_msg_id_filter(normalized if normalized else None)
		except Exception:
			LOG.exception("Failed to push message ID filter to CANLogPlayer")

	def _on_item_filter_changed(self, _item: QListWidgetItem):
		if self._rebuilding or self._ui_syncing or self._reordering:
			return

		requested_checked = self._checked_can_ids()
		requested_ignored = set(self._entries) - requested_checked

		# Keep UI state authoritative from replay process status.
		self._apply_ignored_ids_to_ui(self._ignored_ids)
		self._request_ignore_filter_update(requested_ignored)

	def uncheck_all(self):
		super().uncheck_all()
		if self._rebuilding or self._ui_syncing:
			return
		self._apply_ignored_ids_to_ui(self._ignored_ids)
		self._request_ignore_filter_update(set(self._entries))

	def check_all(self):
		super().check_all()
		if self._rebuilding or self._ui_syncing:
			return
		self._apply_ignored_ids_to_ui(self._ignored_ids)
		self._request_ignore_filter_update(set())

