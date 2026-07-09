import time
from typing import List, Optional

from PySide6.QtCore import QModelIndex, Qt, QItemSelectionModel, QPoint, QEvent
from PySide6.QtWidgets import QTreeView, QScrollBar, QHBoxLayout

from can_sdk.data_object import CANLogLine
from can_sdk.dbc_manager import CANDBManager
from lw.logger_setup import LOG, setup_logger

from ui_sdk.components.pyqt.TreeLogDiskView import SourceProvider, TreeLogDiskModel
from ui_sdk.components.pyqt.TreeLogMessageSignals import (
	TreeLogSelectionSignalsModel,
	_Node,
	Type,
)
from ui_sdk.components.pyqt.TreeLogLazyLoad import TreeLogLazyLoad, TreeLogLazyLoadModel


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Model – hybrid lazy-append with fast-scroll jump
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class TreeLogVirtualWindowModel(TreeLogLazyLoadModel):
	"""Extends TreeLogLazyLoadModel with a movable loaded-start offset.

	Loaded range = [_loaded_start .. _loaded_start + _loaded_rows)

	Normal scroll  → fetchMore appends linearly from _loaded_start + _loaded_rows.
	Fast scroll    → no loading.
	Scroll release → jump_to(dataset_row) resets window, fetchMore restarts.
	"""

	NODE_TYPE = _Node
	CHUNK_SIZE = 200

	def __init__(self, parent=None, model: CANDBManager = None, **_):
		super().__init__(parent=parent, model=model)
		self._loaded_start: int = 0
		self._fast_scroll = False

	# ── RAM set_data (no provider) ─────────────────────────────────────
	def set_data(self, data: List[CANLogLine], preload_first_window: bool = True):
		"""Load RAM data with _loaded_start = 0."""
		self.beginResetModel()
		self._loaded_start = 0
		self._loaded_rows = 0
		src = data if data is not None else []
		self._data = [entry for entry in src if entry is not None]
		self._root.children.clear()
		self._message_nodes.clear()
		for row, entry in enumerate(self._data):
			self._message_nodes[row] = self._build_message_node(row, entry)
		self.endResetModel()
		if preload_first_window and self._total_rows() > 0:
			self.fetchMore(QModelIndex())

	# ── Total rows (for scrollbar range) ───────────────────────────────
	def _total_rows(self) -> int:
		if getattr(self, "_source_provider", None) is None:
			return len(self._data)
		return TreeLogDiskModel._total_rows(self)

	def jump_to(self, dataset_row: int, preload_chunk: bool = False):
		total = self._total_rows()
		if total <= 0:
			return

		new_start = max(0, min(int(dataset_row), total - 1))

		self.beginResetModel()
		self._loaded_start = new_start
		self._loaded_rows = 0
		self._data.clear()
		self._message_nodes.clear()
		self._source_exhausted = False
		self._root.children.clear()
		self.endResetModel()

		if preload_chunk:
			self.fetchMore(QModelIndex())

	# ── Row mapping: index.row() is local [0 .. _loaded_rows) ─────────
	def index(self, row, column, parent=QModelIndex()):
		if not parent.isValid():
			if row < 0 or row >= self._loaded_rows or column < 0 or column >= self._columns:
				return QModelIndex()
			node_key = row
			if self._source_provider is None:
				node_key = self._loaded_start + row
			node = self._message_nodes.get(node_key)
			if node is None:
				return QModelIndex()
			node.parent = self._root
			return self.createIndex(row, column, node)
		return super().index(row, column, parent)

	def rowCount(self, parent=QModelIndex()):
		if parent.isValid():
			return super().rowCount(parent)
		return self._loaded_rows

	def hasChildren(self, parent=QModelIndex()):
		if not parent.isValid():
			return self._loaded_rows > 0
		return bool(super().hasChildren(parent))

	# ── Absolute ↔ local helpers ───────────────────────────────────────
	def dataset_row_from_local(self, local_row: int) -> int:
		return self._loaded_start + local_row

	def local_row_from_dataset(self, dataset_row: int) -> int:
		return dataset_row - self._loaded_start

	# ── ensure_message_row_loaded adjusted for _loaded_start ───────────
	def ensure_message_row_loaded(self, dataset_row: int, extra_after: int = 0):
		total = self._total_rows()
		if dataset_row < 0 or dataset_row >= total:
			return False

		local = self.local_row_from_dataset(dataset_row)
		target_local = local + extra_after

		while self._loaded_rows <= target_local and self.canFetchMore():
			self.fetchMore()
		return True


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  View – fast-scroll guards + jump on release
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class TreeLogVirtualWindow(TreeLogLazyLoad):
	"""Hybrid lazy-load + fast-scroll-jump tree view."""

	def __init__(
		self,
		parent=None,
		model: CANDBManager = None,
		source_provider: Optional[SourceProvider] = None,
		window_size: int = 200,
	):
		# Build the base widget (creates self.view, layout, _virtual_bar, etc.)
		super().__init__(parent=parent, model=model)

		# Replace model with our hybrid version
		self.model_ = TreeLogVirtualWindowModel(self, model=model)
		self.model_.CHUNK_SIZE = max(1, int(window_size))
		if source_provider is not None:
			self.model_.set_source_provider(source_provider)
		self.view.setModel(self.model_)

		self.select_model = TreeLogSelectionSignalsModel(self.model_, self.view)
		self.view.setSelectionModel(self.select_model)

		self._last_scroll_value: Optional[int] = None
		self._last_scroll_time: Optional[float] = None
		self._fast_scroll_threshold = 5000.0
		self._wheel_accumulator = 0.0
		# valueChanged + sliderPressed are already connected by TreeLogLazyLoad.__init__
		# (and bound to this overridden handlers). Only add sliderReleased here.
		self._virtual_bar.sliderReleased.connect(self._on_scroll_end)
		# Intercept wheel events so scrolling always routes through virtual bar,
		# even when the tree's internal scrollbar is at min/max of the loaded chunk.
		self.view.viewport().installEventFilter(self)

	# ── Wheel event filter ─────────────────────────────────────────────
	def eventFilter(self, obj, event):
		"""Redirect viewport wheel events to the virtual scrollbar.

		Without this, scrolling up past local row 0 (or down past the last
		loaded row) would stall because the QTreeView's internal scrollbar
		hits its limit and stops emitting valueChanged.
		"""
		if obj is self.view.viewport() and event.type() == QEvent.Wheel:
			delta = event.angleDelta().y()
			if delta != 0:
				# 120 units = 1 standard notch → 3 rows; accumulate for touchpad
				self._wheel_accumulator += -delta * 3.0 / 120.0
				whole = int(self._wheel_accumulator)
				if whole != 0:
					self._wheel_accumulator -= whole
					new_val = self._virtual_bar.value() + whole
					new_val = max(0, min(new_val, self._virtual_bar.maximum()))
					self._virtual_bar.setValue(new_val)
			return True  # consume wheel event
		return super().eventFilter(obj, event)

	# ── Fast-scroll guards ─────────────────────────────────────────────
	def _on_scroll_start(self):
		self._last_scroll_value = self._virtual_bar.value()
		self._last_scroll_time = time.perf_counter()
		self.model_._fast_scroll = False
		self._on_virtual_scroll(self._virtual_bar.value())

	def _on_scroll_end(self):
		self.model_._fast_scroll = False
		self._last_scroll_value = self._virtual_bar.value()
		self._last_scroll_time = time.perf_counter()
		self._on_virtual_scroll(self._virtual_bar.value())

	# ── Normal scroll (wheel / keyboard) ───────────────────────────────
	def _on_virtual_scroll(self, value: int):
		LOG.debug(f"_on_virtual_scroll: {value}")
		if self._scroll_guard:
			return

		now = time.perf_counter()
		if self._last_scroll_value is not None and self._last_scroll_time is not None:
			dv = abs(int(value) - int(self._last_scroll_value))
			dt = now - self._last_scroll_time
			if dt > 0:
				speed = dv / dt
				self.model_._fast_scroll = speed > self._fast_scroll_threshold

		self._last_scroll_value = int(value)
		self._last_scroll_time = now

		total = self.model_._total_rows()
		if total <= 0:
			return

		visible_rows = self._visible_rows()
		max_top_row = max(0, total - visible_rows)
		dataset_row = min(max(0, int(value)), max_top_row)

		# Fast scroll mode: suspend loading completely while dragging quickly.
		# Blank current chunk while dragging quickly; actual load happens on release.
		if self.model_._fast_scroll:
			self._scroll_guard += 1
			try:
				self.model_.jump_to(dataset_row, preload_chunk=False)
			finally:
				self._scroll_guard -= 1
			return

		self._scroll_guard += 1
		try:
			local = self.model_.local_row_from_dataset(dataset_row)
			if local < 0 or local >= self.model_._loaded_rows:
				# When scrolling UP (local < 0), back up the jump origin so
				# the next several wheel ticks stay inside the loaded window
				# instead of triggering a model-reset on every single tick.
				buffer = max(visible_rows * 2, self.model_.CHUNK_SIZE // 2)
				jump_target = max(0, dataset_row - buffer) if local < 0 else dataset_row
				self.model_.jump_to(jump_target, preload_chunk=True)
				local = self.model_.local_row_from_dataset(dataset_row)

			if not self.model_._fast_scroll:
				preload_margin = visible_rows * 2
				self.model_.ensure_message_row_loaded(dataset_row, extra_after=preload_margin)

			local = self.model_.local_row_from_dataset(dataset_row)
			idx = self.model_.index(local, 0, QModelIndex())
			if idx.isValid():
				self.view.scrollTo(idx, QTreeView.PositionAtTop)
		finally:
			self._scroll_guard -= 1

	# ── set_data (RAM mode) ────────────────────────────────────────────
	def set_data(self, data):
		self.model_.set_data(data)
		self._sync_virtual_scrollbar()
		self._virtual_bar.setValue(0)
		if self.model_._total_rows() > 0:
			self._on_virtual_scroll(0)

	# ── source provider mode ───────────────────────────────────────────
	def set_source_provider(self, source_provider: Optional[SourceProvider]):
		self.model_.set_source_provider(source_provider)
		self._sync_virtual_scrollbar()

	# ── Scrollbar sync ─────────────────────────────────────────────────
	def _sync_virtual_scrollbar(self):
		total = self.model_._total_rows()
		if total <= 0:
			self._virtual_bar.setRange(0, 0)
			self._virtual_bar.setPageStep(1)
			return

		visible_rows = self._visible_rows()
		max_top_row = max(0, total - visible_rows)
		self._virtual_bar.setRange(0, max_top_row)
		self._virtual_bar.setPageStep(max(1, visible_rows))

	def _visible_rows(self) -> int:
		idx = self.model_.index(0, 0, QModelIndex())
		row_h = self.view.rowHeight(idx)
		if row_h <= 0:
			row_h = max(1, self.view.fontMetrics().height() + 6)
		return max(1, self.view.viewport().height() // row_h)

	def _on_view_scrolled(self, _value: int):
		"""Sync manual/wheel scrolling using dataset row coordinates.

		Base TreeLogLazyLoad uses local row from indexAt(), which is incorrect for
		virtual-window mode where loaded rows are offset by _loaded_start.
		"""
		if self._scroll_guard:
			return
		if self.model_._total_rows() <= 0:
			return

		top_idx = self.view.indexAt(QPoint(0, 0))
		if not top_idx.isValid():
			return

		node = top_idx.internalPointer()
		if isinstance(node, _Node) and node.type == Type.SIGNAL and top_idx.parent().isValid():
			local_row = top_idx.parent().row()
		else:
			local_row = top_idx.row()

		if local_row < 0:
			return

		dataset_row = self.model_.dataset_row_from_local(local_row)
		visible_rows = self._visible_rows()
		max_top_row = max(0, self.model_._total_rows() - visible_rows)
		clamped_row = min(max(0, int(dataset_row)), max_top_row)

		if self._virtual_bar.value() != clamped_row:
			self._virtual_bar.setValue(clamped_row)



if __name__ == "__main__":
	import sys
	import time
	from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton
	from can_sdk.test_ultility import TEST_generated_CANLogLine_batch, TEST_set_up_DBModel

	setup_logger(env="DEV", backup_count=30)
	app = QApplication(sys.argv)
	app.setStyle("Fusion")

	db_model = TEST_set_up_DBModel()
	parsed_lines = TEST_generated_CANLogLine_batch(100000)

	win = QWidget()
	win.setWindowTitle("TreeLogVirtualWindow Test")
	layout = QVBoxLayout(win)
	tree = TreeLogVirtualWindow(model=db_model)
	layout.addWidget(tree)

	load_btn = QPushButton("Load Parsed Lines")

	def on_load_click():
		start = time.perf_counter()
		tree.set_data(parsed_lines)
		t1 = time.perf_counter()
		app.processEvents()
		t2 = time.perf_counter()
		print(f"set_data: {t1 - start:.4f}s | render: {t2 - t1:.4f}s | total: {t2 - start:.4f}s")

	load_btn.clicked.connect(on_load_click)
	layout.addWidget(load_btn)

	win.resize(1000, 620)
	win.show()
	sys.exit(app.exec())
