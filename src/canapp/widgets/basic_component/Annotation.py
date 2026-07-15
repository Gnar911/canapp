from PySide6.QtCore import QObject, QTimer, QPoint, QEvent
from PySide6.QtWidgets import QToolTip
from PySide6.QtGui import QCursor


class TextAnnotation(QObject):
    def __init__(self, widget, delay=200):
        super().__init__(widget)

        self.widget = widget
        self.delay = delay
        self.texts: list[str] = []

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._show)

        # IMPORTANT
        widget.setMouseTracking(True)
        widget.installEventFilter(self)

    # ---------------------------
    # Public API
    # ---------------------------
    def text_binding(self, new_texts):
        if isinstance(new_texts, str):
            if new_texts not in self.texts:
                self.texts.append(new_texts)
        else:
            for t in new_texts:
                if t not in self.texts:
                    self.texts.append(t)

    # ---------------------------
    # Event filter
    # ---------------------------
    def eventFilter(self, obj, event):
        if obj is not self.widget:
            return False

        et = event.type()

        if et == QEvent.Enter:
            self._timer.start(self.delay)

        elif et == QEvent.Leave:
            self._timer.stop()
            QToolTip.hideText()

        elif et == QEvent.MouseMove:
            if QToolTip.isVisible():
                QToolTip.showText(
                    QCursor.pos() + QPoint(15, 10),
                    "\n".join(self.texts),
                    self.widget,
                )

        return False

    # ---------------------------
    def _show(self):
        if not self.texts:
            return

        QToolTip.showText(
            QCursor.pos() + QPoint(15, 10),
            "\n".join(self.texts),
            self.widget,
        )


if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication, QPushButton

    app = QApplication(sys.argv)

    btn = QPushButton("Hover me")
    tip = TextAnnotation(btn)
    tip.text_binding([
        "Line 1: CAN ID = 0x123",
        "Line 2: DLC = 8",
        "Line 3: FD Enabled",
    ])

    btn.resize(200, 50)
    btn.show()
    sys.exit(app.exec())
