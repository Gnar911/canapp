from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QHBoxLayout

from can_sdk.data_object import CANLogPlay
from can_sdk.connection_viewmodel import CANConnectManager
from ui_sdk.components.pyqt.basic_component.ComboboxSearch import ComboBoxSearch


class ChannelComboBox(ComboBoxSearch):
    """Searchable combo that displays acquired channel names.

    Holds a reference to a CANLogPlay entry and mutates ``entry.channel``
    directly when the user picks a value — exactly like SignalEditBox
    mutates ``sig.set_raw_value()``.
    """

    def __init__(self, parent=None, connection_model: Optional[CANConnectManager] = None):
        super().__init__(parent)
        self._connection_model: Optional[CANConnectManager] = None
        self._entry: Optional[CANLogPlay] = None
        self.set_connection_model(connection_model)

    # ------ entry reference (mutated on selection) ------
    def set_entry(self, entry: Optional[CANLogPlay]):
        self._entry = entry
        self._sync_from_entry()

    def entry(self) -> Optional[CANLogPlay]:
        return self._entry

    # ------ connection model ------
    def set_connection_model(self, connection_model: Optional[CANConnectManager]):
        if self._connection_model is connection_model:
            return
        self._connection_model = connection_model
        self.refresh_channels()

    def connection_model(self) -> Optional[CANConnectManager]:
        return self._connection_model

    # ------ popup ------
    def showPopup(self):
        self.refresh_channels()
        super().showPopup()

    # ------ selection → mutate entry directly ------
    def _select_value(self, text: str):
        """Override: call base then mutate entry.channel."""
        super()._select_value(text)
        if self._entry is not None:
            self._entry.channel = text

    # ------ refresh from connection model ------
    def refresh_channels(self):
        prev_text = self.currentText().strip()
        self.clear()

        model = self._connection_model
        if model is None:
            self.set_completer_values([])
            self.lineEdit().setPlaceholderText("No connection model")
            return

        acquired = model.acquired_channels
        if not acquired:
            self.set_completer_values([])
            self.lineEdit().setPlaceholderText("No acquired channels")
            return

        names = []
        for handle, _ctx in acquired.items():
            try:
                ch_info = model.get_channel_info(handle)
                name = str(getattr(ch_info, "name", "")) if ch_info is not None else ""
            except Exception:
                continue
            names.append(name.strip() if name else "Channel")

        names.sort()
        for name in names:
            self.addItem(name)

        self.set_completer_values(names)
        self.lineEdit().setPlaceholderText(f"{len(names)} acquired channels")

        # restore previous selection if still valid
        if prev_text:
            idx = self.findText(prev_text, Qt.MatchExactly)
            if idx >= 0:
                self.setCurrentIndex(idx)
                return
        if self.count() > 0:
            self.setCurrentIndex(0)

    def set_completer_values(self, values):
        self._full_list = [str(v) for v in values]

    # ------ sync combo text from entry ------
    def _sync_from_entry(self):
        if self._entry is None:
            return
        channel = str(self._entry.channel or "")
        if not channel:
            return
        idx = self.findText(channel, Qt.MatchExactly)
        if idx >= 0:
            self.setCurrentIndex(idx)
        else:
            self.setEditText(channel)


class ChannelEditBox(QWidget):
    """QWidget wrapper around ChannelComboBox — same pattern as SignalEditBox.

    The delegate creates THIS as the editor widget.  Because the wrapper
    QWidget itself never receives focus (its child combo does), the
    delegate never fires closeEditor on a stray FocusOut.
    """

    def __init__(self, parent=None, connection_model: Optional[CANConnectManager] = None):
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        self._combo = ChannelComboBox(self, connection_model=connection_model)
        lay.addWidget(self._combo)

    def combo(self) -> ChannelComboBox:
        return self._combo

    def set_entry(self, entry: Optional[CANLogPlay]):
        self._combo.set_entry(entry)

    def entry(self) -> Optional[CANLogPlay]:
        return self._combo.entry()

    def set_connection_model(self, connection_model: Optional[CANConnectManager]):
        self._combo.set_connection_model(connection_model)


if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel
    from lw.logger_setup import setup_logger
    from can_sdk.test_ultility import TEST_set_up_all_channels

    setup_logger(env="DEV", backup_count=30)

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    connect_manager = TEST_set_up_all_channels(10)
    app.aboutToQuit.connect(connect_manager.shutdown)

    win = QWidget()
    win.setWindowTitle("ChannelComboBox Test")
    layout = QVBoxLayout(win)

    combo = ChannelComboBox(connection_model=connect_manager)
    layout.addWidget(combo)

    status_label = QLabel("Ready")
    layout.addWidget(status_label)

    acquire_next_btn = QPushButton("Acquire Next Channel")

    def on_acquire_next_click():
        handles = sorted(
            connect_manager.available_channels.keys(),
            key=lambda h: int(getattr(h, "channel_idx", -1)),
        )
        if not handles:
            status_label.setText("No available channels")
            return

        handle = handles[0]
        ok = connect_manager.acquire(handle)
        if ok:
            ch_info = connect_manager.get_channel_info(handle)
            name = str(getattr(ch_info, "name", "") or "")
            idx = int(getattr(handle, "channel_idx", -1))
            status_label.setText(f"Acquired CH{idx}: {name}")
            combo.refresh_channels()
        else:
            status_label.setText("Acquire failed")

    acquire_next_btn.clicked.connect(on_acquire_next_click)
    layout.addWidget(acquire_next_btn)

    refresh_btn = QPushButton("Refresh")
    refresh_btn.clicked.connect(combo.refresh_channels)
    layout.addWidget(refresh_btn)

    win.resize(420, 180)
    win.show()

    sys.exit(app.exec())



