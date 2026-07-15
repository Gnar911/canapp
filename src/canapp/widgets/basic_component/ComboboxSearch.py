import shiboken6

from PySide6.QtWidgets import (
    QComboBox, QListWidget, QListWidgetItem, QApplication,
)
from PySide6.QtCore import Qt, QEvent, QPoint, QSize


class _DropdownPopup(QListWidget):
    """A floating list that NEVER steals keyboard focus."""

    def __init__(self, combo: "ComboBoxSearch"):
        super().__init__(combo.window())  # parent = top-level window
        self._combo = combo
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setFocusPolicy(Qt.NoFocus)
        self.setMouseTracking(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setStyleSheet(
            "QListWidget { border: 1px solid palette(mid); }"
            "QListWidget::item { padding: 4px 8px; }"
            "QListWidget::item:hover { background-color: palette(highlight); color: palette(highlighted-text); }"
        )
        self.itemClicked.connect(self._on_item_clicked)

    # ------ geometry helpers ------
    def reposition(self):
        """Position below the combo box."""
        combo = self._combo
        global_pos = combo.mapToGlobal(QPoint(0, combo.height()))
        w = max(combo.width(), 180)
        row_count = min(self.count(), 12) or 1
        h = self.sizeHintForRow(0) * row_count + 4
        self.setGeometry(global_pos.x(), global_pos.y(), w, h)

    # ------ event filter ------
    def event(self, ev: QEvent) -> bool:
        # Block any focus-in that might sneak through
        if ev.type() == QEvent.FocusIn:
            self._combo.lineEdit().setFocus(Qt.OtherFocusReason)
            return True
        return super().event(ev)

    # ------ click on item ------
    def _on_item_clicked(self, item: QListWidgetItem):
        text = item.text()
        if text == ComboBoxSearch.NOT_FOUND_TEXT:
            return
        self.hide()
        combo = self._combo
        if not shiboken6.isValid(combo):
            return
        combo._select_value(text)


class ComboBoxSearch(QComboBox):
    NOT_FOUND_TEXT = "Not found"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.NoInsert)
        self.setCompleter(None)  # disable built-in completer entirely

        self._full_list: list[str] = []
        self._dropdown: _DropdownPopup | None = None  # lazy-init after show
        self._selected = False  # True after user picks an item

        self.lineEdit().textEdited.connect(self._on_text_edited)
        self.lineEdit().installEventFilter(self)
        QApplication.instance().installEventFilter(self)

    # lazy-create dropdown (needs a visible parent window)
    def _ensure_dropdown(self):
        if self._dropdown is None:
            self._dropdown = _DropdownPopup(self)
        return self._dropdown

    # Override native popup — use our own dropdown instead
    def showPopup(self):
        dd = self._ensure_dropdown()
        if dd.isVisible():
            dd.hide()
            return
        current_text = self.lineEdit().text().strip()
        has_exact_match = self.findText(current_text, Qt.MatchExactly) >= 0 if current_text else False
        # After a deliberate selection, show ALL items (user wants to browse)
        if self._selected or has_exact_match:
            self._set_all_items()
        else:
            self._apply_filter(self.lineEdit().text())
        dd.reposition()
        dd.show()
        # keep focus on the line edit
        self.lineEdit().setFocus(Qt.OtherFocusReason)

    def hidePopup(self):
        if self._dropdown and self._dropdown.isVisible():
            self._dropdown.hide()
        super().hidePopup()

    def focusOutEvent(self, ev):
        if self._dropdown and self._dropdown.isVisible():
            self._dropdown.hide()
        super().focusOutEvent(ev)

    # ---------------------------
    # Public API
    # ---------------------------
    def set_completer_values(self, values: list[str]):
        self._full_list = [str(v) for v in values]
        self.clear()
        if self._full_list:
            self.addItems(self._full_list)

    # ---------------------------
    # Internals
    # ---------------------------
    def _apply_filter(self, text: str):
        dd = self._ensure_dropdown()
        dd.clear()
        q = (text or "").strip().lower()
        if not q:
            items = self._full_list
        else:
            items = [v for v in self._full_list if q in v.lower()]

        if not items:
            it = QListWidgetItem(self.NOT_FOUND_TEXT)
            it.setFlags(Qt.NoItemFlags)
            it.setForeground(Qt.gray)
            dd.addItem(it)
        else:
            for s in items:
                dd.addItem(s)

    def _set_all_items(self):
        dd = self._ensure_dropdown()
        dd.clear()
        for s in self._full_list:
            dd.addItem(s)

    def _on_text_edited(self, text: str):
        self._selected = False  # user is typing → back to filter mode
        dd = self._ensure_dropdown()
        self._apply_filter(text)
        dd.reposition()
        dd.show()

    def _select_value(self, text: str):
        if not shiboken6.isValid(self):
            return
        self._selected = True  # mark as intentional selection
        idx = self.findText(text, Qt.MatchExactly)
        if idx >= 0:
            self.setCurrentIndex(idx)
        else:
            self.setEditText(text)

    def keyPressEvent(self, ev):
        """Intercept Escape before QComboBox can handle it."""
        if ev.key() == Qt.Key_Escape and self._dropdown and self._dropdown.isVisible():
            self._dropdown.hide()
            ev.accept()
            return
        super().keyPressEvent(ev)

    # --- keyboard: Enter picks highlighted item, Escape closes ---
    def eventFilter(self, obj, ev: QEvent) -> bool:
        if self._dropdown and self._dropdown.isVisible() and ev.type() == QEvent.MouseButtonPress:
            gp = ev.globalPosition().toPoint() if hasattr(ev, "globalPosition") else ev.globalPos()
            in_dropdown = self._dropdown.geometry().contains(gp)
            in_combo = self.geometry().contains(self.mapFromGlobal(gp))
            if not in_dropdown and not in_combo:
                self._dropdown.hide()

        if obj is self.lineEdit() and self._dropdown and self._dropdown.isVisible():
            if ev.type() == QEvent.KeyPress:
                key = ev.key()
                if key in (Qt.Key_Return, Qt.Key_Enter):
                    cur = self._dropdown.currentItem()
                    if cur and cur.text() != self.NOT_FOUND_TEXT:
                        self._select_value(cur.text())
                    self._dropdown.hide()
                    return True
                elif key == Qt.Key_Escape:
                    self._dropdown.hide()
                    return True
                elif key == Qt.Key_Down:
                    row = self._dropdown.currentRow()
                    if row < self._dropdown.count() - 1:
                        self._dropdown.setCurrentRow(row + 1)
                    return True
                elif key == Qt.Key_Up:
                    row = self._dropdown.currentRow()
                    if row > 0:
                        self._dropdown.setCurrentRow(row - 1)
                    return True
        return super().eventFilter(obj, ev)


if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton

    app = QApplication(sys.argv)

    win = QWidget()
    layout = QVBoxLayout(win)

    cb = ComboBoxSearch()
    cb.set_completer_values([
        "ENGINE_STATUS",
        "VEHICLE_SPEED",
        "BATTERY_INFO",
        "ADAS_OBJECT",
        "ADAS_LANE",
    ])

    layout.addWidget(cb)

    def _print_current_model_data():
        idx = cb.model().index(cb.currentIndex(), 0)
        print("model_display:", idx.data(Qt.DisplayRole))
        print("model_user_role:", idx.data(Qt.UserRole))

    btn = QPushButton("Get current")
    btn.clicked.connect(_print_current_model_data)
    layout.addWidget(btn)

    win.resize(400, 120)
    win.show()

    sys.exit(app.exec())
