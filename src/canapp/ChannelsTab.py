from PySide6 import QtWidgets, QtCore
from canapp.vm.channel_view_model import (
    ChannelViewModel,
    ListModel,
    DeviceInfoLine
)

# STATE_COLOR = {
#     ChannelState.ACQUIRED: "green",
#     ChannelState.AVAILABLE: "orange",
#     ChannelState.UNPLUGGED: "red",
# }

class ChannelsTab(QtWidgets.QWidget):
    def __init__(self, vm: ChannelViewModel, parent = None):
        super().__init__(parent)

        self.vm = vm
        self.vm.deviceStateChanged.connect(self.reevaluate)

        # self._channel_rows: dict[str, QtWidgets.QWidget] = {}

        self._build_ui()
        #self.on_event_channels_scan()

    # def _subscribe_vm_events(self):
    #     event = getattr(self.vm, "event_on_channels_state_changed", None)
    #     if event is not None:
    #         event.subscribe(self._on_vm_channels_state_changed)
    #         return

    #     fallback_event = getattr(self.vm, "event_on_channels_scan", None)
    #     if fallback_event is not None:
    #         fallback_event.subscribe(self._on_vm_channels_state_changed)

    # def _on_vm_channels_state_changed(self, *_):
    #     self._channelsStateRefreshRequested.emit()

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
        self.combo.setModel(self.vm._cbx_model)
        select_row.addWidget(self.combo)

        lock_btn = QtWidgets.QPushButton("Lock Channel")
        lock_btn.clicked.connect(
            lambda: self.vm.acquireDevice(
                self.combo.currentData(ListModel.ItemRole)
            )
        )
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

        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        status_layout.addWidget(line)

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

    # def _hline(self):
    #     line = QtWidgets.QFrame()
    #     line.setFrameShape(QtWidgets.QFrame.HLine)
    #     line.setFrameShadow(QtWidgets.QFrame.Sunken)
    #     return line

    # def _sync_available_combo(self):
    #     current_handle = self.combo.currentData()
    #     current_text = self.combo.currentText()

    #     available_items = list(self.vm.available_channels.items())
    #     available_handles = [handle for handle, _ in available_items]

    #     blocker = QtCore.QSignalBlocker(self.combo)
    #     try:
    #         existing_index_by_handle = {
    #             self.combo.itemData(i): i
    #             for i in range(self.combo.count())
    #         }

    #         for handle, ch in available_items:
    #             idx = existing_index_by_handle.get(handle)
    #             if idx is None:
    #                 self.combo.addItem(ch.name, handle)
    #             elif self.combo.itemText(idx) != ch.name:
    #                 self.combo.setItemText(idx, ch.name)

    #         remove_indices = [
    #             i for i in range(self.combo.count())
    #             if self.combo.itemData(i) not in available_handles
    #         ]
    #         for idx in reversed(remove_indices):
    #             self.combo.removeItem(idx)

    #         if current_handle in available_handles:
    #             for i in range(self.combo.count()):
    #                 if self.combo.itemData(i) == current_handle:
    #                     self.combo.setCurrentIndex(i)
    #                     break
    #         elif self.combo.count() > 0:
    #             match_index = self.combo.findText(current_text)
    #             if match_index >= 0:
    #                 self.combo.setCurrentIndex(match_index)
    #     finally:
    #         del blocker

    # def _refresh_channel_status(self):
    #     # clear rows
    #     while self.rows_container.count():
    #         item = self.rows_container.takeAt(0)
    #         if item.widget():
    #             item.widget().deleteLater()

    #     self._channel_rows.clear()

    #     for ch in self.vm.all_channels.values():
    #         self._add_channel_row(ch)

    #     self.active_label.setText(str(len(self.vm.acquired_channels)))
    #     self.disconnected_label.setText(str(len(self.vm.available_channels)))
    #     self.unplugged_label.setText(str(len(self.vm.disconnected_channels)))

    #     # toggle empty/status
    #     if self.vm.all_channels:
    #         self.empty_state.hide()
    #         self.status_section.show()
    #     else:
    #         self.status_section.hide()
    #         self.empty_state.show()

    def reevaluate(self):
        self._clear_channel_rows()
        for line in self.vm.all_device_status:
            self._add_channel_row(line)

    def _clear_channel_rows(self):
        while self.rows_container.count():
            item = self.rows_container.takeAt(0)

            if widget := item.widget():
                widget.deleteLater()

    def _add_channel_row(
        self,
        line: DeviceInfoLine,
    ):
        row = QtWidgets.QWidget()

        layout = QtWidgets.QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)

        label = QtWidgets.QLabel(
            line.device.show
        )

        status = QtWidgets.QLabel(
            line.status
        )

        layout.addWidget(label)
        layout.addWidget(status)
        layout.addStretch()

        self.rows_container.addWidget(row)

