from enum import Enum
from PySide6.QtCore import Qt
from typing import Optional
from ui_sdk.components.pyqt.basic_component.ComboboxSearch import ComboBoxSearch
from can_sdk.dbc_manager import CANDBManager
from lw.logger_setup import LOG

class DisplayMode(Enum):
    HEX = "hex"
    DEC = "dec"

""" BUG: current_can_id always return None even selecting -> UserRole is None"""
"""
FINAL FIX:
Dropdown showed “Not found” because _full_list wasn’t updated after you stopped calling set_values(). I added set_completer_values() and used it in DBCCombobox so the completer list is updated without clearing combo items (and without losing CAN ID user data).
    def set_completer_values(self, values: list[str]):
        self._full_list = list(values)
        self._set_items(self._full_list)

    self.set_completer_values(items)
"""
class DBCComboBox(ComboBoxSearch):
    """
    ComboBoxSearch specialized for CAN DBC messages.

    - Model data: int (CAN ID)
    - Display: "[CANID] MessageName"
    - Data role: Qt.UserRole -> int (CAN ID)
    """
    def __init__(self, parent=None, candb: CANDBManager = None):
        super().__init__(parent)
        self._candb = candb
        self._entries: list[int] = []
        self._display_mode: DisplayMode = DisplayMode.HEX
        self._reload_from_db()
        self._candb.event_on_db_changed.subscribe(self._reload_from_db)

    # ---------------------------
    # Override: keep filter list in sync WITHOUT destroying UserRole data
    # ---------------------------
    def set_completer_values(self, values):
        """Only update the search/filter list.
        Do NOT call clear()/addItems() here – _rebuild_items already
        populated the combo with addItem(display, int(can_id)) which
        stores the CAN ID in Qt.UserRole.  The base-class implementation
        would wipe that data."""
        self._full_list = [str(v) for v in values]

    # ---------------------------
    # Public API
    # ---------------------------
    def current_value(self) -> Optional[int]:
        idx = self.model().index(self.currentIndex(), 0)
        if not idx.isValid():
            return None
        return idx.data(Qt.UserRole)

    def set_display_mode(self, mode: DisplayMode):
        """Switch between HEX and DEC display for CAN IDs."""
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
    def _reload_from_db(self):
        """
        Load CAN IDs from CANDBManager.
        """
        can_ids = self._candb.get_message_ids()
        self._entries = list(can_ids)
        self._rebuild_items(self._entries)

    def _format_display(self, can_id: int) -> str:
        """Format CAN ID + message name according to current display mode."""
        name = self._candb.get_message_name(can_id)
        if self._display_mode == DisplayMode.DEC:
            return f"[{can_id}] {name}"
        return f"[{can_id:X}] {name}"

    def _rebuild_items(self, can_ids: list[int]):
        le = self.lineEdit()
        if not can_ids:
            le.setPlaceholderText("0 messages in DBC..")
            self.set_completer_values([])
            return
        else:
            count = len(can_ids)
            le.setPlaceholderText(f"{count} messages in DBC..")
            self.clear()
            items = []
            for can_id in can_ids:
                display = self._format_display(can_id)
                self.addItem(display, int(can_id))
                items.append(display)
            self.set_completer_values(items)

if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton

    app = QApplication(sys.argv)

    win = QWidget()
    layout = QVBoxLayout(win)

    model = CANDBManager()
    model.load_database(
        "/home/gnar911/Desktop/20260122 APP WEBSITE - CAN ANALYZER 3.0 CBCM TOOL APP ARC/CAN_Analyzer_MVVM/Database/EEA10_CANFD_R00c_withADAS_Main.dbc")
    
    cb = DBCComboBox(win, model)
    layout.addWidget(cb)

    btn_decimal = QPushButton("Test: Decimal Mode")
    btn_decimal.clicked.connect(cb.set_display_decimal)
    layout.addWidget(btn_decimal)

    btn = QPushButton("Get CAN ID")
    btn.clicked.connect(lambda: print("current_can_id:", cb.current_can_id()))
    layout.addWidget(btn)

    win.resize(400, 120)
    win.show()

    sys.exit(app.exec())
