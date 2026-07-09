from PySide6.QtWidgets import (
    QApplication, QWidget, QPushButton, QHBoxLayout, QLabel, QVBoxLayout
)
from PySide6.QtCore import QPropertyAnimation, QEasingCurve, Qt


class SideDrawer(QWidget):
    LEFT = "left"
    RIGHT = "right"

    def __init__(
        self,
        content: QWidget,
        parent=None,
        panel_width=280,
        side=LEFT,
    ):
        super().__init__(parent)

        self.panel_width = panel_width
        self.side = side
        self.expanded = False
        self.content_widget = content

        # ---- handle button ----
        self.handle = QPushButton()
        self.handle.setFixedWidth(22)
        self.handle.setFocusPolicy(Qt.NoFocus)
        self.handle.clicked.connect(self.toggle)

        # ---- panel ----
        self.panel = QWidget()
        self.panel.setMaximumWidth(0)

        panel_layout = QVBoxLayout(self.panel)
        panel_layout.setContentsMargins(0, 0, 0, 0)
        panel_layout.addWidget(self.content_widget)

        # ---- layout ----
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        if side == self.LEFT:
            self.handle.setText("▶")
            layout.addWidget(self.handle)
            layout.addWidget(self.panel)
        else:
            self.handle.setText("◀")
            layout.addWidget(self.panel)
            layout.addWidget(self.handle)

        # ---- animation ----
        self.anim = QPropertyAnimation(self.panel, b"maximumWidth", self)
        self.anim.setDuration(220)
        self.anim.setEasingCurve(QEasingCurve.OutCubic)

    # -------------------------------------------------

    def toggle(self):
        self.anim.stop()

        start = self.panel.width()
        end = 0 if self.expanded else self.panel_width

        self.anim.setStartValue(start)
        self.anim.setEndValue(end)

        if self.side == self.LEFT:
            self.handle.setText("▶" if self.expanded else "◀")
        else:
            self.handle.setText("◀" if self.expanded else "▶")

        self.expanded = not self.expanded
        self.anim.start()

    def get_content_widget(self) -> QWidget:
        return self.content_widget

    def set_drawer_height(self, height: int):
        if height <= 0:
            return

        self.setFixedHeight(height)
        self.panel.setFixedHeight(height)
        self.handle.setFixedHeight(height)

if __name__ == "__main__":
    app = QApplication([])

    window = QWidget()
    window.setWindowTitle("SideDrawer Test")
    window.resize(520, 180)

    root_layout = QVBoxLayout(window)
    root_layout.addWidget(QLabel("Click the arrow button to toggle the drawer:"))

    content = QWidget()
    content_layout = QVBoxLayout(content)
    content_layout.addWidget(QLabel("Drawer content here"))

    root_layout.addWidget(SideDrawer(content=content, panel_width=280))

    window.show()
    app.exec()
