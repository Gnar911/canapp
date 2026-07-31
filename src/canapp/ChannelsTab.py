from PySide6 import QtWidgets, QtCore
from canapp.vm.channel_view_model import (
    ChannelViewModel,
    # ListModel,
    DeviceInfoLine
)
from PySide6.QtCore import (
    Qt,
    QModelIndex,
    QAbstractListModel,
)

class ListModel(QAbstractListModel):
    ItemRole = Qt.UserRole + 1

    def __init__(
        self,
        vm: ChannelViewModel,
        parent=None,
    ):
        super().__init__(parent)

        """ BUG: Qt is not automatically update if the available_devices changed -> need to nofity it"""
        self._items = vm.available_devices
        vm.deviceStateChanged.connect(lambda: 
                                      (self.beginResetModel(), 
                                       setattr(self, "_items", vm.available_devices), 
                                       self.endResetModel()))

    def rowCount(
        self,
        parent: QModelIndex = QModelIndex(),
    ) -> int:
        if parent.isValid():
            return 0

        return len(self._items)

    def data(
        self,
        index: QModelIndex,
        role: int = Qt.DisplayRole,
    ):
        if not index.isValid():
            return None

        row = index.row()

        if not 0 <= row < len(self._items):
            return None

        item = self._items[row]

        if role == Qt.DisplayRole:
            return item.device_id

        if role == self.ItemRole:
            return item

        return None

    def roleNames(self):
        return {
            self.ItemRole: b"item",
        }

class ChannelsTab(QtWidgets.QWidget):
    def __init__(self, vm: ChannelViewModel, parent = None):
        super().__init__(parent)

        self.vm = vm
        self._build_ui()

        self.vm.deviceStateChanged.connect(self.reevaluate)
        self.reevaluate()

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
        self._cbx_model = ListModel(self.vm)
        self.combo.setMinimumWidth(200)
        self.combo.setModel(self._cbx_model)
        select_row.addWidget(self.combo)

        lock_btn = QtWidgets.QPushButton("Lock")
        """20260726 BUG: QComboBox.currentData() can return None"""
        lock_btn.clicked.connect(
            lambda: (
                self.combo.currentData(ListModel.ItemRole) is not None
                and self.vm.acquireDevice(
                    self.combo.currentData(ListModel.ItemRole)
                )
            )
        )
        select_row.addWidget(lock_btn)
        select_row.addStretch(1)
        main_layout.addLayout(select_row)


        """ NOTE: Using stackk layout for 2 state: Empty state UI and Status state UI"""
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

        # rows container
        self.rows_container = QtWidgets.QVBoxLayout()
        self.rows_container.setAlignment(QtCore.Qt.AlignTop)
        status_layout.addLayout(self.rows_container)

        """ NOTE: Using stackk layout for 2 state: Empty state UI and Status state UI"""
        self.stack = QtWidgets.QStackedLayout()
        self.stack.addWidget(self.empty_state)
        self.stack.addWidget(self.status_section)
        main_layout.addLayout(self.stack)

    def reevaluate(self):
        self.stack.setCurrentWidget(
                    self.status_section if self.vm.isHavingDevices else self.empty_state
                )
        self._clear_channel_rows()
        lines = list(self.vm.all_device_status)
        for line in lines:
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

        label = QtWidgets.QLabel(line.show)

        status = QtWidgets.QLabel(line.status_show)
        status.setStyleSheet(f"color: {line.status_color};")

        layout.addWidget(label)
        layout.addWidget(status)
        layout.addStretch()

        if line.is_acquired:
            btn = QtWidgets.QPushButton("Unlock")
            btn.clicked.connect(
                lambda _, device=line: self.vm.releaseDevice(device.data)
            )
            layout.addWidget(btn)

        self.rows_container.addWidget(row)

