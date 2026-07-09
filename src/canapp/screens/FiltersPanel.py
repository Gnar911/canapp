import sys
from typing import Optional
from PySide6 import QtWidgets
from PySide6.QtWidgets import QWidget
from CenterContextPane import CenterContextManagerViewModel
from can_sdk.canlog_viewmodel import BasicFileLogContext, FilterMode, LogContextManager
from can_sdk.dbc_manager import CANDBManager
from can_sdk.data_object import CANLogLine
from ui_sdk.components.pyqt.basic_component.CollapsibleSection import CollapsibleSection
from ui_sdk.components.pyqt.FilterTimeScopeSlider import FilterTimeScopeSlider
from ui_sdk.components.pyqt.MessageFilterCheckList import MessageFilterCheckList
from ui_sdk.components.pyqt.ChannelFilterCheckList import ChannelFilterCheckList
from ui_sdk.components.pyqt.SignalFilterCheckList import SignalFilterCheckList

class FiltersPanel(QtWidgets.QWidget):
    def __init__(
        self,
        parent: QWidget,
        ctx_model: CenterContextManagerViewModel,
        candb: CANDBManager = None,
        log_ctx_mgr: LogContextManager = None,
    ):
        super().__init__(parent)
        self.ctx_model = ctx_model
        self.candb = candb
        self.log_ctx_mgr = log_ctx_mgr
        self.target_logfile: Optional[BasicFileLogContext] = None
        self._filtered_lines: list[CANLogLine] = []

        self._build_ui()
        self._connect_ui()

        self.ctx_model.event_on_target_context_changed.subscribe(self.on_event_target_logfile_changed)
        self.on_event_target_logfile_changed(self.ctx_model.get_current_context())

    def _build_ui(self):
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        # --- Message Filter section ---
        self.section_message = CollapsibleSection("Filter Message")
        msg_content = QtWidgets.QVBoxLayout()
        self.message_filter_panel = MessageFilterCheckList(
            parent=self,
            ctx_model=self.log_ctx_mgr,
        )
        msg_content.addWidget(self.message_filter_panel)
        self.section_message.setContentLayout(msg_content)

        # --- Signal Filter section ---
        self.section_signal = CollapsibleSection("Filter Signal")
        sig_content = QtWidgets.QVBoxLayout()
        self.signal_filter_panel = SignalFilterCheckList(
            parent=self,
            ctx_model=self.log_ctx_mgr,
        )
        sig_content.addWidget(self.signal_filter_panel)
        self.section_signal.setContentLayout(sig_content)

        self.section_channel = CollapsibleSection("Filter Channel")
        channel_content = QtWidgets.QVBoxLayout()
        self.channel_filter_panel = ChannelFilterCheckList(
            parent=self,
            ctx_model=self.log_ctx_mgr,
        )
        channel_content.addWidget(self.channel_filter_panel)
        self.section_channel.setContentLayout(channel_content)

        self.section_dir = CollapsibleSection("Filter Rx/Tx")
        dir_content = QtWidgets.QVBoxLayout()
        group_dir = QtWidgets.QGroupBox("")
        group_dir_layout = QtWidgets.QHBoxLayout(group_dir)
        group_dir_layout.setContentsMargins(6, 6, 6, 6)
        group_dir_layout.setSpacing(10)

        self.rb_rx_only = QtWidgets.QRadioButton("Rx Only")
        self.rb_tx_only = QtWidgets.QRadioButton("Tx Only")
        self.rb_none = QtWidgets.QRadioButton("None")
        self.rb_none.setChecked(True)

        group_dir_layout.addWidget(self.rb_rx_only)
        group_dir_layout.addWidget(self.rb_tx_only)
        group_dir_layout.addWidget(self.rb_none)
        group_dir_layout.addStretch(1)
        dir_content.addWidget(group_dir)
        self.section_dir.setContentLayout(dir_content)

        self.section_time = CollapsibleSection("Filter Time Range")
        time_content = QtWidgets.QVBoxLayout()
        group_time = QtWidgets.QGroupBox("")
        group_time_layout = QtWidgets.QVBoxLayout(group_time)
        group_time_layout.setContentsMargins(6, 6, 6, 6)
        group_time_layout.setSpacing(6)

        self.range_slider = FilterTimeScopeSlider(
            parent=self,
            ctx_model=self.log_ctx_mgr,
        )

        group_time_layout.addWidget(self.range_slider)
        time_content.addWidget(group_time)
        self.section_time.setContentLayout(time_content)

        root.addWidget(self.section_message)
        root.addWidget(self.section_signal)
        root.addWidget(self.section_channel)
        root.addWidget(self.section_dir)
        root.addWidget(self.section_time)
        root.addStretch(1)

    def _connect_ui(self):
        self.rb_rx_only.toggled.connect(self._on_dir_filter_changed)
        self.rb_tx_only.toggled.connect(self._on_dir_filter_changed)
        self.rb_none.toggled.connect(self._on_dir_filter_changed)

    def _on_dir_filter_changed(self):
        if self.rb_rx_only.isChecked():
            self.target_logfile.set_dir_filter(FilterMode.RX_ONLY)
        elif self.rb_tx_only.isChecked():
            self.target_logfile.set_dir_filter(FilterMode.TX_ONLY)
        else:
            self.target_logfile.unset_dir_filter()

    def on_event_target_logfile_changed(self, file: BasicFileLogContext):
        if file is None:
            return
        if self.target_logfile is not None:
            self.target_logfile.event_on_filter_changed.remove_all_subscribes()
        file.event_on_filter_changed.subscribe(self.on_event_filter_changed)
        self.target_logfile = file
        self.range_slider.set_context(file)
        self.rb_none.setChecked(True)

    def on_event_filter_changed(self, data: list[CANLogLine]):
        self._filtered_lines = list(data)
        if self.target_logfile is not None:
            self.range_slider.set_context(self.target_logfile)


if __name__ == "__main__":
    class _DummyEvent:
        def __init__(self):
            self._subs = []

        def subscribe(self, cb):
            self._subs.append(cb)

        def remove_all_subscribes(self):
            self._subs.clear()

        def notify(self, payload):
            for cb in list(self._subs):
                cb(payload)

    class _DummyTargetLog:
        def __init__(self):
            self.event_on_filter_changed = _DummyEvent()
            self._channels = {"CH1", "CH2", "CH3"}
            self._timestamps = [0.1, 0.4, 0.8, 1.2, 1.9, 2.6, 3.1]

        def get_filter_channels(self):
            return self._channels

        def set_channel_filter(self, ch: str):
            print("set_channel_filter:", ch)

        def unset_channel_filter(self):
            print("unset_channel_filter")

        def set_dir_filter(self, mode):
            print("set_dir_filter:", mode)

        def unset_dir_filter(self):
            print("unset_dir_filter")

        def get_filter_timestamps(self):
            return self._timestamps

        def time_range_filter(self, time_start: float, time_end: float, target_logs=None):
            print("time_range_filter:", time_start, time_end)

        def set_time_range_filter(self, time_start: float, time_end: float):
            self.time_range_filter(time_start, time_end)

    class _DummyCtxModel(QtWidgets.QWidget):
        def __init__(self, ctx):
            super().__init__()
            self._ctx = ctx
            self.event_on_target_context_changed = _DummyEvent()

        def get_current_context(self):
            return self._ctx

    app = QtWidgets.QApplication(sys.argv)
    win = QtWidgets.QWidget()
    win.setWindowTitle("OtherFiltersPanel - Small Test")
    lay = QtWidgets.QVBoxLayout(win)

    dummy_ctx = _DummyTargetLog()
    dummy_vm = _DummyCtxModel(dummy_ctx)
    panel = FiltersPanel(parent=win, ctx_model=dummy_vm)
    lay.addWidget(panel)

    win.resize(640, 420)
    win.show()
    sys.exit(app.exec())
