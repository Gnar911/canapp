from PySide6 import QtWidgets, QtCore
from can_sdk.connection_viewmodel import (
    CANConnectManager,
    CANChannelInfo,
    ChannelState,
)
from can_sdk.test_ultility import (
    TEST_set_up_all_channels,
    TEST_down_all_channels,
    TEST_get_channel_status,
)

STATE_COLOR = {
    ChannelState.ACQUIRED: "green",
    ChannelState.AVAILABLE: "orange",
    ChannelState.UNPLUGGED: "red",
}


class ChannelsTab(QtWidgets.QWidget):
    channelLocked = QtCore.Signal(object)
    _channelsStateRefreshRequested = QtCore.Signal()

    def __init__(self, model: CANConnectManager, parent = None):
        super().__init__(parent)

        self.model = model
        self._channelsStateRefreshRequested.connect(self.on_event_channels_scan, QtCore.Qt.QueuedConnection)
        self._subscribe_model_events()

        self._channel_rows: dict[str, QtWidgets.QWidget] = {}

        self._build_ui()
        self.on_event_channels_scan()

    def _subscribe_model_events(self):
        event = getattr(self.model, "event_on_channels_state_changed", None)
        if event is not None:
            event.subscribe(self._on_model_channels_state_changed)
            return

        fallback_event = getattr(self.model, "event_on_channels_scan", None)
        if fallback_event is not None:
            fallback_event.subscribe(self._on_model_channels_state_changed)

    def _on_model_channels_state_changed(self, *_):
        self._channelsStateRefreshRequested.emit()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
    def _build_ui(self):
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setAlignment(QtCore.Qt.AlignTop)

        # ---- title
        title = QtWidgets.QLabel("Channel Manager")
        title.setStyleSheet("font-size: 13pt; font-weight: bold;")
        main_layout.addWidget(title)

        # ---- select row
        select_row = QtWidgets.QHBoxLayout()

        select_row.addWidget(QtWidgets.QLabel("Available Channels:"))

        self.combo = QtWidgets.QComboBox()
        self.combo.setMinimumWidth(200)
        select_row.addWidget(self.combo)

        lock_btn = QtWidgets.QPushButton("Lock Channel")
        lock_btn.clicked.connect(self.on_lock_channel)
        select_row.addWidget(lock_btn)

        select_row.addStretch(1)
        main_layout.addLayout(select_row)

        # ---- empty state
        self.empty_state = QtWidgets.QWidget()
        empty_layout = QtWidgets.QVBoxLayout(self.empty_state)
        empty_layout.setAlignment(QtCore.Qt.AlignCenter)

        lbl_empty = QtWidgets.QLabel("No Active Channel")
        lbl_empty.setStyleSheet("font-size: 14pt; font-weight: bold;")
        empty_layout.addWidget(lbl_empty)

        lbl_hint = QtWidgets.QLabel(
            "Select a channel to lock and start working"
        )
        lbl_hint.setStyleSheet("color: gray;")
        empty_layout.addWidget(lbl_hint)

        main_layout.addWidget(self.empty_state)

        # ---- status section
        self.status_section = QtWidgets.QWidget()
        status_layout = QtWidgets.QVBoxLayout(self.status_section)
        status_layout.setAlignment(QtCore.Qt.AlignTop)

        status_layout.addWidget(self._hline())

        status_title = QtWidgets.QLabel("Channel Status")
        status_title.setStyleSheet("font-weight: bold;")
        status_layout.addWidget(status_title)

        # summary grid
        grid = QtWidgets.QGridLayout()
        grid.setColumnStretch(1, 1)

        self.active_label = QtWidgets.QLabel("")
        self.disconnected_label = QtWidgets.QLabel("—")
        self.unplugged_label = QtWidgets.QLabel("—")

        self.active_label.setStyleSheet("color: green;")
        self.disconnected_label.setStyleSheet("color: orange;")
        self.unplugged_label.setStyleSheet("color: red;")

        grid.addWidget(QtWidgets.QLabel("Active:"), 0, 0)
        grid.addWidget(self.active_label, 0, 1)

        grid.addWidget(QtWidgets.QLabel("Disconnected:"), 1, 0)
        grid.addWidget(self.disconnected_label, 1, 1)

        grid.addWidget(QtWidgets.QLabel("Unplugged:"), 2, 0)
        grid.addWidget(self.unplugged_label, 2, 1)

        status_layout.addLayout(grid)

        # rows container
        self.rows_container = QtWidgets.QVBoxLayout()
        self.rows_container.setAlignment(QtCore.Qt.AlignTop)
        status_layout.addLayout(self.rows_container)

        main_layout.addWidget(self.status_section)

        # start hidden
        self.status_section.hide()

    def _hline(self):
        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        return line

    # ------------------------------------------------------------------
    # Backend events
    # ------------------------------------------------------------------
    def on_event_channels_scan(self):
        self._sync_available_combo()

        self._refresh_channel_status()

    def _sync_available_combo(self):
        current_handle = self.combo.currentData()
        current_text = self.combo.currentText()

        available_items = list(self.model.available_channels.items())
        available_handles = [handle for handle, _ in available_items]

        blocker = QtCore.QSignalBlocker(self.combo)
        try:
            existing_index_by_handle = {
                self.combo.itemData(i): i
                for i in range(self.combo.count())
            }

            for handle, ch in available_items:
                idx = existing_index_by_handle.get(handle)
                if idx is None:
                    self.combo.addItem(ch.name, handle)
                elif self.combo.itemText(idx) != ch.name:
                    self.combo.setItemText(idx, ch.name)

            remove_indices = [
                i for i in range(self.combo.count())
                if self.combo.itemData(i) not in available_handles
            ]
            for idx in reversed(remove_indices):
                self.combo.removeItem(idx)

            if current_handle in available_handles:
                for i in range(self.combo.count()):
                    if self.combo.itemData(i) == current_handle:
                        self.combo.setCurrentIndex(i)
                        break
            elif self.combo.count() > 0:
                match_index = self.combo.findText(current_text)
                if match_index >= 0:
                    self.combo.setCurrentIndex(match_index)
        finally:
            del blocker

    def _refresh_channel_status(self):
        # clear rows
        while self.rows_container.count():
            item = self.rows_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self._channel_rows.clear()

        for ch in self.model.all_channels.values():
            self._add_channel_row(ch)

        self.active_label.setText(str(len(self.model.acquired_channels)))
        self.disconnected_label.setText(str(len(self.model.available_channels)))
        self.unplugged_label.setText(str(len(self.model.disconnected_channels)))

        # toggle empty/status
        if self.model.all_channels:
            self.empty_state.hide()
            self.status_section.show()
        else:
            self.status_section.hide()
            self.empty_state.show()

    def _add_channel_row(self, ch: CANChannelInfo):
        row = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)

        vendor = getattr(getattr(ch.config, "vendor", None), "name", "Unknown")

        label = QtWidgets.QLabel(
            f"{vendor}  Channel {ch.name}:"
        )
        label.setMinimumWidth(300)
        layout.addWidget(label)

        status = QtWidgets.QLabel(ch.state.name.capitalize())
        color = STATE_COLOR.get(ch.state, "gray")
        status.setStyleSheet(f"color: {color};")

        layout.addWidget(status)
        layout.addStretch(1)

        self.rows_container.addWidget(row)
        self._channel_rows[ch.name] = row

    # ------------------------------------------------------------------
    # UI actions
    # ------------------------------------------------------------------
    def on_lock_channel(self):
        handle = self.combo.currentData()
        if handle is None:
            return

        if self.model.acquire(handle):
            self.channelLocked.emit(handle)


if __name__ == "__main__":
    app = QtWidgets.QApplication([])

    try:
        TEST_set_up_all_channels()
        print(TEST_get_channel_status())
    except Exception as exc:
        QtWidgets.QMessageBox.warning(
            None,
            "VCAN Setup",
            f"Failed to setup vcan interfaces:\n{exc}",
        )

    model = CANConnectManager()
    model.start_scan()

    w = ChannelsTab(model=model)
    w.resize(700, 420)
    w.setWindowTitle("ChannelsTab Multi-Channel Test")
    w.show()

    refresh_timer = QtCore.QTimer(w)
    refresh_timer.setInterval(500)
    refresh_timer.timeout.connect(w.on_event_channels_scan)
    refresh_timer.start()

    def _cleanup():
        try:
            model.shutdown()
        finally:
            try:
                TEST_down_all_channels()
            except Exception as exc:
                print(f"VCAN teardown warning: {exc}")

    app.aboutToQuit.connect(_cleanup)
    app.exec()
