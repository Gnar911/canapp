from enum import Enum
from typing import Optional

from PySide6.QtCore import Qt

from can_sdk.canlog_viewmodel import LogContextManager, LogContext
from ui_sdk.components.pyqt.basic_component.ComboboxSearch import ComboBoxSearch


class DisplayMode(Enum):
	HEX = "hex"
	DEC = "dec"


class MessageComboBox(ComboBoxSearch):
	"""
	ComboBoxSearch specialized for message IDs from current LogContext.

	- Parent: ComboBoxSearch
	- Model: LogContextManager
	- Event: subscribes to event_on_context_changed
	- Data role: Qt.UserRole -> int (CAN ID)
	- Display format: <can_id> - <message_name>
	"""

	def __init__(self, parent=None, ctx_model: LogContextManager = None):
		super().__init__(parent)
		self._ctx_model = ctx_model
		self._entries: list[int] = []
		self._display_mode: DisplayMode = DisplayMode.HEX

		if self._ctx_model is not None:
			self._ctx_model.event_on_context_changed.subscribe(self._on_context_changed)
			self._reload_from_context(self._ctx_model.cur_ctx)
		else:
			self._rebuild_items([])

	# ---------------------------
	# Public API
	# ---------------------------
	def current_value(self) -> Optional[int]:
		idx = self.model().index(self.currentIndex(), 0)
		if not idx.isValid():
			return None
		return idx.data(Qt.UserRole)

	def set_display_mode(self, mode: DisplayMode):
		if self._display_mode != mode:
			self._display_mode = mode
			self._rebuild_items(self._entries)

	def set_display_hex(self):
		self.set_display_mode(DisplayMode.HEX)

	def set_display_decimal(self):
		self.set_display_mode(DisplayMode.DEC)

	# ---------------------------
	# Internal
	# ---------------------------
	def _on_context_changed(self, ctx: Optional[LogContext]):
		self._reload_from_context(ctx)

	def _reload_from_context(self, ctx: Optional[LogContext]):
		if ctx is None:
			self._entries = []
			self._rebuild_items([])
			return

		try:
			can_ids = list(getattr(ctx.d_filelog, "can_ids", []) or [])
			normalized = sorted({int(can_id) for can_id in can_ids})
		except Exception:
			normalized = []

		self._entries = normalized
		self._rebuild_items(self._entries)

	def _format_can_id(self, can_id: int) -> str:
		if self._display_mode == DisplayMode.DEC:
			return f"{int(can_id)}"
		return f"0x{int(can_id):X}"

	def _get_message_name(self, can_id: int) -> str:
		if self._ctx_model is None:
			return "Unknown"

		dbm = getattr(self._ctx_model, "mDBM", None)
		if dbm is None:
			return "Unknown"

		try:
			name = dbm.get_message_name(int(can_id))
			if not name:
				return "Unknown"
			return str(name)
		except Exception:
			return "Unknown"

	def _format_display(self, can_id: int) -> str:
		return f"{self._format_can_id(can_id)} - {self._get_message_name(can_id)}"

	def _rebuild_items(self, can_ids: list[int]):
		le = self.lineEdit()
		if not can_ids:
			if self._ctx_model is None or self._ctx_model.cur_ctx is None:
				le.setPlaceholderText("No context selected..")
			else:
				le.setPlaceholderText("0 messages in context..")
			self.clear()
			self.set_completer_values([])
			return

		le.setPlaceholderText(f"{len(can_ids)} messages in context..")
		self.clear()
		items: list[str] = []
		for can_id in can_ids:
			display = self._format_display(int(can_id))
			self.addItem(display, int(can_id))
			items.append(display)
		self.set_completer_values(items)

