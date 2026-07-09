from typing import List, Optional

from PySide6.QtCore import QModelIndex

from can_sdk.data_object import CANLogLine
from can_sdk.canlog_viewmodel import LogContextViewModel
from can_sdk.dbc_manager import CANDBManager
from lw.logger_setup import setup_logger, LOG

from ui_sdk.components.pyqt.TreeLogLazyLoad import TreeLogLazyLoad, TreeLogLazyLoadModel, SourceProvider
from ui_sdk.components.pyqt.TreeLogMessageSignals import TreeLogSelectionSignalsModel

class TreeLogPageTable(TreeLogLazyLoad):
    """Page-level tree view using TreeLogDiskModel + LogContext source provider."""
    class LogContextSourceProvider(SourceProvider):
        """Adapter: wraps any object with a load_visible method as a SourceProvider."""
        """ This is the bridge class for disk data, it must provide the window size data and the total rows index of disk data"""
        def __init__(self, ctx_model: LogContextViewModel):
            self._ctx_model = ctx_model
            self._total_rows = 0

        def _ctx(self):
            if self._ctx_model is None:
                return None
            return self._ctx_model.cur_ctx

        def _page_metrics(self) -> tuple[int, int, int]:
            ctx = self._ctx()
            if ctx is None:
                return 0, 1, 0

            self._total_rows = ctx.get_total_rows_for_current_filter()
            total_rows = max(0, int(self._total_rows))
            page_size = max(1, int(getattr(ctx, "ui_page_size", 1)))
            cur_page = max(1, int(getattr(ctx, "cur_page", 1)))

            page_first = (cur_page - 1) * page_size
            visible_count = max(0, min(page_size, total_rows - page_first))
            return page_first, page_size, visible_count

        def load_visible(self, first_row: int, window_size: int) -> List[CANLogLine]:
            ctx = self._ctx()
            if ctx is None:
                return []

            local_first = max(0, int(first_row))
            local_window = max(1, int(window_size))

            page_first, _, visible_count = self._page_metrics()
            if local_first >= visible_count:
                return []

            # Ensure LogContext absolute offset matches current page before delegating.
            # (LogContext.load_visible uses _page_first_line + local_first internally.)
            if getattr(ctx, "_page_first_line", page_first) != page_first:
                setattr(ctx, "_page_first_line", page_first)

            safe_window = min(local_window, visible_count - local_first)
            return ctx.load_visible(local_first, safe_window)

        def row_count(self) -> Optional[int]:
            _, _, visible_count = self._page_metrics()
            return visible_count


    def __init__(
        self,
        parent=None,
        ctx_model: Optional[LogContextViewModel] = None,
    ):
        db_model = ctx_model.mDBM if ctx_model is not None else None
        super().__init__(parent=parent, model=db_model)

        self._ctx_model: Optional[LogContextViewModel] = None
        self._source_provider: Optional[SourceProvider] = None
        self._bound_data_available_model: Optional[LogContextViewModel] = None

        self.model_ = TreeLogLazyLoadModel(self, source_provider=None, model=db_model)
        self.view.setModel(self.model_)

        self.select_model = TreeLogSelectionSignalsModel(self.model_, self.view)
        self.view.setSelectionModel(self.select_model)

        self.set_context_model(ctx_model)

    def _build_owned_provider(self) -> Optional[SourceProvider]:
        if self._ctx_model is None:
            return None
        return self.LogContextSourceProvider(self._ctx_model)

    def set_context_model(self, ctx_model: Optional[LogContextViewModel]):
        self._ctx_model = ctx_model
        self._bind_context_events()
        self._source_provider = self._build_owned_provider()
        self.model_.set_source_provider(self._source_provider)
        self.refresh_from_context()

    def _bind_context_events(self):
        if self._ctx_model is None:
            return
        if self._bound_data_available_model is self._ctx_model:
            return
        self._ctx_model.event_on_canlog_data_available.subscribe(self._on_canlog_data_available)
        self._bound_data_available_model = self._ctx_model

    def _on_canlog_data_available(self, ctx=None, *_):
        LOG.debug("_on_canlog_data_available")
        if self._ctx_model is None:
            return
        current = self._ctx_model.cur_ctx
        if ctx is not None and current is not None and ctx is not current:
            return
        self.refresh_from_context()

    def refresh_from_context(self):
        self.model_.set_source_provider(self._source_provider)
        if self.model_.canFetchMore(QModelIndex()):
            self.model_.fetchMore(QModelIndex())

        self._sync_virtual_scrollbar()
        self._virtual_bar.setValue(0)

        if self.model_._total_rows() > 0:
            self._on_virtual_scroll(0)

if __name__ == "__main__":
    import sys
    import time
    from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
    from can_sdk.test_ultility import TEST_set_up_1_context
    setup_logger(env="DEV", backup_count=30)
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = QWidget()
    win.setWindowTitle("TreeLogPageTable Test")
    layout = QVBoxLayout(win)

    ctx_model=TEST_set_up_1_context()
    tree = TreeLogPageTable(ctx_model=ctx_model)
    layout.addWidget(tree)

    controls = QHBoxLayout()

    load_btn = QPushButton("Refresh Page")
    def on_refresh():
        start = time.perf_counter()
        tree.refresh_from_context()
        t1 = time.perf_counter()
        app.processEvents()
        t2 = time.perf_counter()
        print(f"refresh: {t1 - start:.4f}s | render: {t2 - t1:.4f}s | total: {t2 - start:.4f}s")
    load_btn.clicked.connect(on_refresh)
    controls.addWidget(load_btn)

    prev_btn = QPushButton("Prev Page")
    next_btn = QPushButton("Next Page")
    page_label = QLabel("Page: 1")

    def update_page_label():
        ctx = getattr(ctx_model, "cur_ctx", None)
        page_label.setText(f"Page: {ctx.cur_page}" if ctx is not None else "Page: -")

    def on_prev_page():
        ctx = getattr(ctx_model, "cur_ctx", None)
        if ctx is None:
            return
        ctx.cur_page = max(1, ctx.cur_page - 1)
        update_page_label()
        tree.refresh_from_context()

    def on_next_page():
        ctx = getattr(ctx_model, "cur_ctx", None)
        if ctx is None:
            return
        total_rows = max(0, int(ctx.get_total_rows_for_current_filter()))
        page_size = max(1, int(ctx.ui_page_size))
        max_page = max(1, (total_rows + page_size - 1) // page_size)
        ctx.cur_page = min(max_page, ctx.cur_page + 1)
        update_page_label()
        tree.refresh_from_context()

    prev_btn.clicked.connect(on_prev_page)
    next_btn.clicked.connect(on_next_page)
    controls.addWidget(prev_btn)
    controls.addWidget(next_btn)
    controls.addWidget(page_label)

    fetch_btn = QPushButton("Fetch More")
    fetch_btn.clicked.connect(lambda: tree.model_.fetchMore(QModelIndex()))
    controls.addWidget(fetch_btn)

    mode_btn = QPushButton("Mode: Read")
    def on_toggle_mode():
        is_edit = tree.toggle_edit_mode()
        mode_btn.setText("Mode: Edit" if is_edit else "Mode: Read")
    mode_btn.clicked.connect(on_toggle_mode)
    controls.addWidget(mode_btn)

    layout.addLayout(controls)

    tree.refresh_from_context()
    update_page_label()

    win.resize(1100, 620)
    win.show()

    sys.exit(app.exec())
