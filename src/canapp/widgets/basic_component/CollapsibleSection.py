from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QToolButton, QSizePolicy, QLayout, QGroupBox, QFrame
)

class CollapsibleSection(QWidget):
    def __init__(self, title: str, parent=None, expanded=False, animated=False):
        super().__init__(parent)

        self._animated = animated
        self._content_height = 0

        # Outer border frame that wraps button + content
        self._frame = QFrame(self)
        self._frame.setObjectName("collapsibleFrame")
        self._frame.setFrameShape(QFrame.StyledPanel)
        self._frame.setStyleSheet("""
            QFrame#collapsibleFrame {
                    border: 1px solid rgba(60, 60, 60, 130);
                border-radius: 1px;
            }
        """)

        frame_layout = QVBoxLayout(self._frame)
        frame_layout.setContentsMargins(0, 0, 0, 0)
        frame_layout.setSpacing(0)

        # Header button
        self.toggle_btn = QToolButton(text=title, checkable=True, checked=expanded)
        self.toggle_btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.toggle_btn.setArrowType(Qt.DownArrow if expanded else Qt.RightArrow)
        self.toggle_btn.setCursor(Qt.PointingHandCursor)
        self.toggle_btn.setStyleSheet("""
            QToolButton {
                border: none;
                font-weight: bold;
                padding: 4px 6px;
            }
            QToolButton:hover {
                background-color: rgba(120, 120, 120, 45);
            }
            QToolButton:checked:hover {
                background-color: rgba(120, 120, 120, 60);
            }
        """)
        self.toggle_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.toggle_btn.setFixedHeight(self.toggle_btn.sizeHint().height())

        # Content container (group box)
        self.content = QGroupBox()
        self.content.setTitle("")
        self.content.setFlat(True)
        self.content.setStyleSheet("QGroupBox { border: none; }")
        self.content.setVisible(True)
        self.content.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.content.setMinimumHeight(0)

        frame_layout.addWidget(self.toggle_btn)
        frame_layout.addWidget(self.content)

        # Animation
        self.anim = QPropertyAnimation(self.content, b"maximumHeight", self)
        self.anim.setDuration(150)
        self.anim.setEasingCurve(QEasingCurve.InOutCubic)
        self.anim.finished.connect(self._on_anim_finished)

        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._frame)

        self.toggle_btn.toggled.connect(self._on_toggled)

    def setContentLayout(self, content_layout):
        """Attach a layout to the collapsible content."""
        content_layout.setContentsMargins(0, 0, 0, 0)
        #content_layout.setSizeConstraint(QLayout.SetFixedSize)
        self.content.setLayout(content_layout)
        self._content_height = content_layout.sizeHint().height()
        if self.toggle_btn.isChecked():
            self.content.setMaximumHeight(self._content_height)
        else:
            self.content.setMaximumHeight(0)

    def _on_toggled(self, checked: bool):
        self.toggle_btn.setArrowType(Qt.DownArrow if checked else Qt.RightArrow)

        if not self._animated:
            self.content.setMaximumHeight(
                self._content_height if checked else 0
            )
            return

        self.content.setVisible(True)
        start = self.content.maximumHeight()
        end = self._content_height if checked else 0

        self.anim.stop()
        self.anim.setStartValue(start)
        self.anim.setEndValue(end)
        self.anim.start()

    def _on_anim_finished(self):
        if not self.toggle_btn.isChecked():
            self.content.setMaximumHeight(0)


from PySide6.QtWidgets import QLabel, QVBoxLayout

def _build_test_widget():
    # Example content
    basic_layout = QVBoxLayout()
    basic_layout.addWidget(QLabel("Signal Name: VehicleSpeed"))
    basic_layout.addWidget(QLabel("Unit: km/h"))
    basic_layout.addWidget(QLabel("Current Value: 80.0"))

    advanced_layout = QVBoxLayout()
    advanced_layout.addWidget(QLabel("Start Bit: 16"))
    advanced_layout.addWidget(QLabel("Length: 16 bits"))
    advanced_layout.addWidget(QLabel("Byte Order: Little Endian"))
    advanced_layout.addWidget(QLabel("Scale: 0.01"))
    advanced_layout.addWidget(QLabel("Offset: 0"))

    # Create sections
    basic_section = CollapsibleSection("Basic Info")
    basic_section.setContentLayout(basic_layout)

    advanced_section = CollapsibleSection("Advanced Signal Info")
    advanced_section.setContentLayout(advanced_layout)

    w = QWidget()
    parent_layout = QVBoxLayout(w)
    parent_layout.addWidget(basic_section)
    parent_layout.addWidget(advanced_section)
    parent_layout.addStretch()
    return w


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    win = _build_test_widget()
    win.setWindowTitle("CollapsibleSection Test")
    win.resize(360, 240)
    win.show()
    sys.exit(app.exec())
