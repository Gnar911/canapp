from typing import List, Optional, Any

from PySide6.QtCore import QModelIndex, QTimer

from can_sdk.data_object import CANLogLine
from can_sdk.connection_viewmodel import CANConnectManager, ChannelContext
from can_sdk.dbc_manager import CANDBManager
from lw.logger_setup import LOG

from ui_sdk.components.pyqt.TreeLogDiskView import SourceProvider, TreeLogDiskModel
from ui_sdk.components.pyqt.TreeLogVirtualWindow import TreeLogVirtualWindow

# Compatibility alias with requested naming
CANConnectionManager = CANConnectManager


class TreeMonitorTable(TreeLogVirtualWindow):
    """Monitor tree backed by current ChannelContext via SourceProvider + TreeLogDiskModel."""

    class MonitorContextSourceProvider(SourceProvider):
        """Adapter that provides rows from the current channel context (full mmap range)."""

        def __init__(
            self,
            connection_model: Optional[CANConnectionManager],
            channel_handle: Optional[Any] = None,
        ):
            self._connection_model = connection_model
            self._channel_handle = channel_handle

        def set_connection_model(self, connection_model: Optional[CANConnectionManager]):
            self._connection_model = connection_model

        def set_channel_handle(self, channel_handle: Optional[Any]):
            self._channel_handle = channel_handle

        def _ctx(self) -> Optional[ChannelContext]:
            model = self._connection_model
            if model is None:
                return None

            handle = self._channel_handle
            try:
                ctx = model.get_context(handle)
            except Exception:
                ctx = None
            if ctx is not None:
                return ctx
            return None

        def load_visible(self, first_row: int, window_size: int) -> List[CANLogLine]:
            ctx = self._ctx()
            if ctx is None:
                return []
            local_first = max(0, int(first_row))
            local_window = max(1, int(window_size))
            return ctx.load_visible(local_first, local_window)

        def row_count(self) -> Optional[int]:
            ctx = self._ctx()
            if ctx is None:
                return 0
            dlog = getattr(ctx, "d_filelog", None)
            if dlog is not None and hasattr(dlog, "total_lines"):
                return max(0, int(getattr(dlog, "total_lines", 0)))
            return max(0, int(getattr(ctx, "grow_size", 0)))

    def __init__(
        self,
        parent=None,
        connection_model: Optional[CANConnectionManager] = None,
        channel_handle: Optional[Any] = None,
        model: Optional[CANDBManager] = None,
    ):
        db_model = model
        super().__init__(
            parent=parent,
            model=db_model,
            source_provider=None,
            window_size=200,
        )

        self._connection_model: Optional[CANConnectionManager] = connection_model
        self._bound_connection_model: Optional[CANConnectionManager] = None
        self._source_provider: Optional[TreeMonitorTable.MonitorContextSourceProvider] = None

        self._visual_rows_timer = QTimer(self)
        self._visual_rows_timer.setInterval(1000)
        self._visual_rows_timer.timeout.connect(self._on_visual_rows_timer)
        # self._visual_rows_timer.start()

        self._source_provider = TreeMonitorTable.MonitorContextSourceProvider(
            connection_model=self._connection_model,
            channel_handle=channel_handle,
        )
        self.set_source_provider(self._source_provider)
        QTimer.singleShot(0, self._on_visual_rows_timer)
        #self._bind_connection_events()

    def start_visual_rows_timer(self):
        if not self._visual_rows_timer.isActive():
            self._visual_rows_timer.start()

    def stop_visual_rows_timer(self):
        if self._visual_rows_timer.isActive():
            self._visual_rows_timer.stop()

    def set_channel_handle(self, channel_handle: Optional[Any]):
        if self._source_provider is None:
            return
        self._source_provider.set_channel_handle(channel_handle)
        self.refresh_from_context()

    def _bind_connection_events(self):
        model = self._connection_model
        if model is None:
            return
        if self._bound_connection_model is model:
            return

        for event_name in (
            "event_on_channel_acquired",
            "event_on_channel_released",
            "event_on_channels_state_changed",
            "event_on_context_changed",
            "event_on_canlog_data_available",
        ):
            event = getattr(model, event_name, None)
            if event is not None and hasattr(event, "subscribe"):
                try:
                    event.subscribe(self._on_connection_changed)
                except Exception:
                    pass

        self._bound_connection_model = model

    def _on_connection_changed(self, *_):
        LOG.debug("TreeMonitorTable._on_connection_changed")
        self.refresh_from_context()

    def _on_virtual_scroll(self, value: int):
        # Delegate to TreeLogVirtualWindow's speed-based handler.
        # It will switch between fast/normal mode automatically and resume
        # fetchMore when scroll speed drops below threshold.
        super()._on_virtual_scroll(value)

    def _on_visual_rows_timer(self):
        if not isinstance(self.model_, TreeLogDiskModel):
            return
        if self._source_provider is None:
            return
        if getattr(self.model_, "_fast_scroll", False):
            return

        old_max = self._virtual_bar.maximum()
        was_at_bottom = self._virtual_bar.value() >= old_max

        try:
            latest_total = self._source_provider.row_count()
        except Exception:
            latest_total = None

        new_total = int(latest_total) if latest_total is not None else None
        old_total = getattr(self.model_, "_source_total_rows", None)
        total_changed = new_total != old_total
        if total_changed:
            self.model_._source_total_rows = new_total
            if new_total is not None and (old_total is None or int(new_total) > int(old_total)):
                self.model_._source_exhausted = False

            if was_at_bottom and self.model_.canFetchMore(QModelIndex()):
                self.model_.fetchMore(QModelIndex())

        self._sync_virtual_scrollbar()

        if total_changed and was_at_bottom and self.model_._loaded_rows > 0:
            self._virtual_bar.setValue(self._virtual_bar.maximum())

    def refresh_from_context(self):
        if getattr(self.model_, "_fast_scroll", False):
            return

        if self.model_.canFetchMore(QModelIndex()):
            self.model_.fetchMore(QModelIndex())

        self._sync_virtual_scrollbar()
        self._virtual_bar.setValue(0)

        # Guard: use _loaded_rows, NOT _total_rows().
        # _total_rows() can report a large _source_total_rows while _data is
        # empty and _source_exhausted is True.  Calling _on_virtual_scroll in
        # that state triggers an infinite loop inside ensure_message_row_loaded
        # (canFetchMore keeps returning True but fetchMore makes no progress).
        if self.model_._loaded_rows > 0:
            self._on_virtual_scroll(0)

if __name__ == "__main__":
    import sys
    import time
    from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
    from can_sdk.test_ultility import TEST_set_up_1_basic_context, TEST_set_up_DBModel
    from lw.logger_setup import setup_logger
    from can_sdk.data_object import CANLogLine, CANLogFile, CANLogRawDiskFile, CANLogDecodedDiskFile

    setup_logger(env="DEV", backup_count=30)
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    ctx_model = None

    db_model = TEST_set_up_DBModel()
    # class _TestMonitorContextSourceProvider(TreeMonitorTable.MonitorContextSourceProvider):
    #     """Test provider: grows total rows by +1000 each time row_count is queried."""
    #     def __init__(self, connection_model, channel_handle=None):
    #         super().__init__(connection_model=connection_model, channel_handle=channel_handle)
    #         self._dynamic_total = 0
    #         self.ctx = TEST_set_up_1_basic_context()

    #     def _ctx(self) -> Optional[ChannelContext]:
    #         return self.ctx
        
    #     def row_count(self) -> Optional[int]:
    #         self._dynamic_total += 1000
    #         return self._dynamic_total

    win = QWidget()
    win.setWindowTitle("TreeMonitorTable Test")
    layout = QVBoxLayout(win)

    tree = TreeMonitorTable(connection_model=ctx_model, model=db_model)
    #test_provider = _TestMonitorContextSourceProvider(connection_model=ctx_model)
    #tree._source_provider = test_provider
    #tree.set_source_provider(test_provider)
    layout.addWidget(tree)

    controls = QHBoxLayout()
    total_label = QLabel("Total mmap rows: 0")

    def update_total_label():
        total = max(0, int(tree._source_provider.row_count()))
        total_label.setText(f"Total mmap rows: {total}")

    refresh_btn = QPushButton("Refresh")
    def on_refresh():
        start = time.perf_counter()
        tree.refresh_from_context()
        t1 = time.perf_counter()
        app.processEvents()
        t2 = time.perf_counter()
        print(f"refresh: {t1 - start:.4f}s | render: {t2 - t1:.4f}s | total: {t2 - start:.4f}s")
    refresh_btn.clicked.connect(on_refresh)
    controls.addWidget(refresh_btn)

    tick_btn = QPushButton("Visual Rows Tick")
    tick_btn.clicked.connect(tree._on_visual_rows_timer)
    controls.addWidget(tick_btn)

    mode_btn = QPushButton("Mode: Read")
    def on_toggle_mode():
        is_edit = tree.toggle_edit_mode()
        mode_btn.setText("Mode: Edit" if is_edit else "Mode: Read")
    mode_btn.clicked.connect(on_toggle_mode)
    controls.addWidget(mode_btn)

    timer_toggle_btn = QPushButton("Start Timer")
    def on_toggle_timer():
        if tree._visual_rows_timer.isActive():
            tree.stop_visual_rows_timer()
            timer_toggle_btn.setText("Start Timer")
        else:
            tree.start_visual_rows_timer()
            timer_toggle_btn.setText("Stop Timer")
    timer_toggle_btn.clicked.connect(on_toggle_timer)
    controls.addWidget(timer_toggle_btn)

    controls.addWidget(total_label)
    layout.addLayout(controls)

    tree._visual_rows_timer.timeout.connect(update_total_label)

    # tree.refresh_from_context()
    update_total_label()
    win.resize(1100, 620)
    win.show()

    sys.exit(app.exec())
