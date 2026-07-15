
from PySide6 import QtWidgets, QtCore, QtGui
from PySide6.QtCore import Qt


class FloatingWindow(QtWidgets.QWidget):
    redockRequested = QtCore.Signal(QtWidgets.QWidget, QtCore.QPoint)

    def __init__(self, title: str, content: QtWidgets.QWidget):
        super().__init__(None, QtCore.Qt.Window)

        self.content = content
        self.setWindowTitle(title)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        content.setParent(self)
        layout.addWidget(content)

    def mouseReleaseEvent(self, e):
        # When user releases mouse, try redock
        self.redockRequested.emit(self.content, self.mapToGlobal(e.pos()))
        super().mouseReleaseEvent(e)

    def closeEvent(self, event):
        # When user closes floating window, redock automatically
        self.redockRequested.emit(self.content, self.pos())
        super().closeEvent(event)
