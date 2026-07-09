from PySide6.QtWidgets import QListWidget, QApplication, QToolTip
from PySide6.QtCore import Qt, QTimer, QPoint
from PySide6.QtGui import QCursor

class ReadOnlyListWidget(QListWidget):
    def __init__(self, parent=None, tooltip_text="Click to copy"):
        super().__init__(parent)

        # ---- Read-only behavior ----
        self.setSelectionMode(QListWidget.NoSelection)
        self.setFocusPolicy(Qt.NoFocus)
        self.setVerticalScrollMode(QListWidget.ScrollPerPixel)

        # ---- Tooltip text ----
        self._hover_tooltip_text = tooltip_text
        self._tooltip_enabled = True

        # Enable mouse tracking for hover tooltip
        self.setMouseTracking(True)

    # -------------------------------------------------
    # Hover tooltip ("Click to copy")
    # -------------------------------------------------
    def enterEvent(self, event):
        if self._tooltip_enabled and self.count() > 0:
            QToolTip.showText(
                QCursor.pos() + QPoint(10, 10),
                self._hover_tooltip_text,
                self,
            )
        super().enterEvent(event)

    def leaveEvent(self, event):
        QToolTip.hideText()
        self._tooltip_enabled = True
        super().leaveEvent(event)

    def mouseMoveEvent(self, event):
        if self._tooltip_enabled and self.count() > 0:
            QToolTip.showText(
                event.globalPosition().toPoint() + QPoint(10, 10),
                self._hover_tooltip_text,
                self,
            )
        super().mouseMoveEvent(event)

    # -------------------------------------------------
    # Click → copy ALL items + temporary tooltip
    # -------------------------------------------------
    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton:
            return

        if self.count() == 0:
            return

        # Collect all items
        all_items = [
            self.item(i).text()
            for i in range(self.count())
        ]
        combined = "\n".join(all_items)

        if not combined:
            return

        # Copy to clipboard
        clipboard = QApplication.clipboard()
        clipboard.setText(combined)

        # Disable hover tooltip temporarily
        self._tooltip_enabled = False
        QToolTip.hideText()

        # Show temporary "Copied!" tooltip
        QToolTip.showText(
            event.globalPosition().toPoint() + QPoint(10, 10),
            "Copied to clipboard!",
            self,
        )

        # Hide it after 800 ms
        QTimer.singleShot(800, QToolTip.hideText)

    # -------------------------------------------------
    # Public API (like your set_data)
    # -------------------------------------------------
    def set_data(self, data_list):
        self.clear()
        for item in data_list:
            self.addItem(str(item))


if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout

    app = QApplication(sys.argv)

    win = QWidget()
    layout = QVBoxLayout(win)

    lst = ReadOnlyListWidget(tooltip_text="Click to copy")
    lst.set_data([
        "CAN ID: 0x123",
        "CAN ID: 0x456",
        "CAN ID: 0x789",
    ])

    layout.addWidget(lst)

    win.resize(400, 300)
    win.show()

    sys.exit(app.exec())
