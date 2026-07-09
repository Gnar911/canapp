from typing import Optional, List

from PySide6.QtCore import QModelIndex, Qt, QItemSelectionModel, QPoint
from PySide6.QtWidgets import QTreeView, QScrollBar, QHBoxLayout

from can_sdk.data_object import CANLogLine
from can_sdk.dbc_manager import CANDBManager
from lw.logger_setup import setup_logger, LOG
from ui_sdk.components.pyqt.TreeLogMessageSignals import (
    TreeLogMessageSignals,
    TreeLogMessageSignalsModel,
    TreeLogSelectionSignalsModel,
    _Node,
    Type,
)
from ui_sdk.components.pyqt.TreeLogDiskView import TreeLogDiskModel, SourceProvider

""" Lazy load on RAM and Disk"""
class TreeLogLazyLoadModel(TreeLogMessageSignalsModel, TreeLogDiskModel):
    """Lazy loading model layered on top of TreeLogMessageSignalsModel."""
    NODE_TYPE = _Node
    CHUNK_SIZE = 100
    def __init__(
        self,
        parent=None,
        model: CANDBManager = None,
        **_,
    ):
        super().__init__(parent=parent, model=model)
        self._loaded_rows = 0

    def _total_rows(self) -> int:
        if getattr(self, "_source_provider", None) is None:
            return len(self._data)
        return TreeLogDiskModel._total_rows(self)

    def _build_message_node(self, row: int, entry: CANLogLine) -> _Node:
        node = super()._build_message_node(row, entry)
        node.type = Type.MESSAGE
        return node

    def set_data(self, data: List[CANLogLine], preload_first_window: bool = True):
        self.beginResetModel()
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

    def _append_source_rows(self, rows: List[CANLogLine]):
        for entry in rows:
            if entry is None:
                continue
            idx = len(self._data)
            self._data.append(entry)
            self._message_nodes[idx] = self._build_message_node(idx, entry)

    def canFetchMore(self, parent=QModelIndex()):
        if parent.isValid():
            return False

        if self._source_provider is None:
            return self._loaded_rows < self._total_rows()

        if self._loaded_rows < len(self._data):
            return True

        if self._source_total_rows is not None and self._loaded_rows >= int(self._source_total_rows):
            return False

        return not self._source_exhausted

    def rowCount(self, parent=QModelIndex()):
        if parent.isValid():
            return super().rowCount(parent)
        return self._loaded_rows

    def hasChildren(self, parent=QModelIndex()):
        if not parent.isValid():
            return self._loaded_rows > 0
        return bool(super().hasChildren(parent))

    def index(self, row, column, parent=QModelIndex()):
        if not parent.isValid():
            total = self._loaded_rows
            if row < 0 or row >= total or column < 0 or column >= self._columns:
                return QModelIndex()
            node = self._message_nodes.get(row)
            if node is None:
                return QModelIndex()
            node.parent = self._root
            return self.createIndex(row, column, node)
        return super().index(row, column, parent)

    def data(self, index, role=Qt.DisplayRole):
        return super().data(index, role)

    def fetchMore(self, parent=QModelIndex()):
        if parent.isValid():
            return
        start_row = self._loaded_rows
        loaded_start = int(getattr(self, "_loaded_start", 0))
        abs_start_row = loaded_start + start_row
        chunk_size = self.CHUNK_SIZE
        LOG.debug(
            f"fetchMore start_row={start_row}, abs_start_row={abs_start_row}, "
            f"loaded_start={loaded_start}, chunk_size={chunk_size}"
        )
        if self._source_provider is not None:
            if self._loaded_rows >= len(self._data) and not self._source_exhausted:
                start = loaded_start + len(self._data)
                rows = self._source_provider.load_visible(start, chunk_size) or []
                valid_rows = [row for row in rows if row is not None]
                if not valid_rows:
                    self._source_exhausted = True
                else:
                    self._append_source_rows(valid_rows)
                    if len(valid_rows) < chunk_size:
                        self._source_exhausted = True

        total_available = len(self._data)
        remaining = total_available - self._loaded_rows
        if remaining <= 0:
            LOG.debug(
                f"fetchMore skipped start_row={start_row}, abs_start_row={abs_start_row}, "
                f"loaded_start={loaded_start}, chunk_size={chunk_size}, "
                f"reason=remaining<=0, total_available={total_available}, loaded_rows={self._loaded_rows}"
            )
            return

        items_to_fetch = min(chunk_size, remaining)
        first = self._loaded_rows
        last = first + items_to_fetch - 1
        abs_first = loaded_start + first
        abs_last = loaded_start + last
        self.beginInsertRows(QModelIndex(), first, last)
        self._loaded_rows += items_to_fetch
        self.endInsertRows()
        LOG.debug(
            f"fetchMore loaded start_row={first}, end_row={last}, "
            f"abs_start_row={abs_first}, abs_end_row={abs_last}, "
            f"loaded_start={loaded_start}, chunk_size={items_to_fetch}, "
            f"loaded_rows={self._loaded_rows}, total_available={total_available}"
        )
        #self._load_until_row(self._loaded_rows - 1)

    def _load_until_row(self, row: int):
        LOG.debug("_load_until_row")
        total = self._total_rows()
        if total <= 0 or self._loaded_rows <= 0:
            return

        target_loaded = min(total, max(0, int(row) + 1))
        if target_loaded <= 0:
            return

        first_row = 0
        count = target_loaded - first_row
        lines = self._data[first_row:first_row + count]
        loaded_count = min(len(lines), count)
        if loaded_count <= 0:
            return

        for i, entry in enumerate(lines[:loaded_count]):
            idx = first_row + i
            if idx >= total:
                break
            node = self._message_nodes.get(idx)
            if node is None:
                continue
            if node.payload is None:
                node.payload = entry
            if not node.signals_loaded:
                """self._calculate_message(node)"""

        top_left = self.index(0, 0, QModelIndex())
        bottom_right = self.index(self._loaded_rows - 1, self._columns - 1, QModelIndex())
        if top_left.isValid() and bottom_right.isValid():
            self.dataChanged.emit(
                top_left,
                bottom_right,
                [Qt.DisplayRole, Qt.EditRole, Qt.ForegroundRole, Qt.BackgroundRole],
            )

    def ensure_message_row_loaded(self, row: int, extra_after: int = 0):
        total = self._total_rows()
        if row < 0 or row >= total:
            return False
        target = min(total - 1, row + extra_after)
        while self._loaded_rows <= target and self.canFetchMore():
            self.fetchMore()
        # if self._loaded_rows > 0:
        #     self._load_until_row(min(target, self._loaded_rows - 1))
        return True

class TreeLogLazyLoad(TreeLogMessageSignals):

    def __init__(self, parent=None, model: CANDBManager = None, **kwargs):
        super().__init__(parent=parent, model=model)

        self.model_ = TreeLogLazyLoadModel(self, model=model, **kwargs)
        self.view.setModel(self.model_)

        self.select_model = TreeLogSelectionSignalsModel(self.model_, self.view)
        self.view.setSelectionModel(self.select_model)

        self._scroll_guard = 0
        self._current_focus_message_row: Optional[int] = None

        # hide Qt scrollbar and create virtual scrollbar
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._fast_scroll = False
        self._virtual_bar = QScrollBar(Qt.Vertical, self)
        self._virtual_bar.valueChanged.connect(self._on_virtual_scroll)
        self._virtual_bar.sliderPressed.connect(self._on_scroll_start)
        self.view.verticalScrollBar().valueChanged.connect(self._on_view_scrolled)
        #self._virtual_bar.sliderReleased.connect(self._on_scroll_end)

        # re-layout
        main_layout = self.layout()
        main_layout.removeWidget(self.view)

        h_layout = QHBoxLayout()
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(0)

        h_layout.addWidget(self.view)
        h_layout.addWidget(self._virtual_bar)

        main_layout.addLayout(h_layout)

    def _on_scroll_start(self):
        self.model_._fast_scroll = True

    def _on_scroll_end(self):
        self.model_._fast_scroll = False
        value = self._virtual_bar.value()
        target_row = min(value, self.model_._total_rows() - 1)
        visible_rows = self._visible_rows()
        # ensure rows are loaded
        self.model_.ensure_message_row_loaded(
            target_row,
            extra_after=visible_rows
        )

    def _sync_virtual_scrollbar(self):
        total = self.model_._total_rows()

        if total <= 0:
            self._virtual_bar.setRange(0, 0)
            return

        visible_rows = self._visible_rows()
        max_top_row = max(0, total - visible_rows)
        self._virtual_bar.setRange(0, max_top_row)
        self._virtual_bar.setPageStep(visible_rows)

    def _visible_rows(self):
        idx = self.model_.index(0, 0, QModelIndex())

        row_h = self.view.rowHeight(idx)
        if row_h <= 0:
            row_h = max(1, self.view.fontMetrics().height() + 6)

        return max(1, self.view.viewport().height() // row_h)

    def _on_virtual_scroll(self, value: int):
        if self._scroll_guard:
            return

        self._scroll_guard += 1

        try:
            total = self.model_._total_rows()
            if total <= 0:
                return
            visible_rows = self._visible_rows()
            max_top_row = max(0, total - visible_rows)
            target_row = min(max(0, value), max_top_row)

            # prefetch margin prevents jumps
            preload_margin = visible_rows * 2

            self.model_.ensure_message_row_loaded(
                target_row,
                extra_after=preload_margin
            )
            idx = self.model_.index(target_row, 0, QModelIndex())
            if idx.isValid():
                self.view.scrollTo(idx, QTreeView.PositionAtTop)

        finally:
            self._scroll_guard -= 1

    def _on_view_scrolled(self, _value: int):
        """Sync manual/wheel scrolling in the view back to the virtual bar."""
        if self._scroll_guard:
            return
        if self.model_._total_rows() <= 0:
            return

        top_idx = self.view.indexAt(QPoint(0, 0))
        if not top_idx.isValid():
            return

        node = top_idx.internalPointer()
        if isinstance(node, _Node) and node.type == Type.SIGNAL and top_idx.parent().isValid():
            top_row = top_idx.parent().row()
        else:
            top_row = top_idx.row()

        if top_row < 0:
            return

        visible_rows = self._visible_rows()
        max_top_row = max(0, self.model_._total_rows() - visible_rows)
        clamped_row = min(top_row, max_top_row)

        if self._virtual_bar.value() != clamped_row:
            self._virtual_bar.setValue(clamped_row)

    def set_data(self, data):

        self.model_.set_data(data)

        self._sync_virtual_scrollbar()

        self._virtual_bar.setValue(0)

        if self.model_._total_rows() > 0:
            self._on_virtual_scroll(0)

    def focus_message_row(self, row: int) -> bool:
        row_h = self.view.rowHeight(self.model_.index(0, 0, QModelIndex()))
        if row_h <= 0:
            row_h = max(1, self.view.fontMetrics().height() + 6)

        visible_rows = max(1, self.view.viewport().height() // row_h)
        preload_after = max(visible_rows // 2, 10)

        if not self.model_.ensure_message_row_loaded(row, extra_after=preload_after):
            return False

        index = self.model_.index(row, 1, QModelIndex())
        if not index.isValid():
            return False

        self.select_model.setCurrentIndex(
            index,
            QItemSelectionModel.ClearAndSelect | QItemSelectionModel.Rows,
        )
        hbar = self.view.horizontalScrollBar()
        h_value = hbar.value()
        self.view.scrollTo(index, QTreeView.PositionAtCenter)
        hbar.setValue(h_value)
        self.view.setFocus()
        self._current_focus_message_row = row
        return True

    def get_current_focus_message_row(self) -> Optional[int]:
        return self._current_focus_message_row


if __name__ == "__main__":
    import sys
    import time
    from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton
    from can_sdk.test_ultility import TEST_generated_CANLogLine_batch, TEST_set_up_DBModel

    setup_logger(env="DEV", backup_count=30)
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    db_model = TEST_set_up_DBModel()
    parsed_lines = TEST_generated_CANLogLine_batch(10000)

    win = QWidget()
    win.setWindowTitle("TreeLogLazyLoad Test")
    layout = QVBoxLayout(win)

    tree = TreeLogLazyLoad(model=db_model)
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

    fetch_btn = QPushButton("Fetch More")
    fetch_btn.clicked.connect(lambda: tree.model_.fetchMore(QModelIndex()))
    layout.addWidget(fetch_btn)

    win.resize(900, 560)
    win.show()

    sys.exit(app.exec())
