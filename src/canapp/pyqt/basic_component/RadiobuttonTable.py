import sys
from PySide6.QtWidgets import (
    QApplication, QWidget, QTreeView, QVBoxLayout, QLabel
)
from PySide6.QtGui import (
    QStandardItemModel, QStandardItem, QPainter
)
from PySide6.QtCore import Qt, QRect
from PySide6.QtWidgets import QStyledItemDelegate, QStyle, QStyleOptionButton


# ------------------------------------------------------------
# Radio button delegate (visual radio, model uses CheckState)
# ------------------------------------------------------------

class RadioDelegate(QStyledItemDelegate):
    def paint(self, painter: QPainter, option, index):
        if index.column() == 0:
            checked = index.data(Qt.CheckStateRole) == Qt.Checked

            opt = QStyleOptionButton()
            opt.state = QStyle.State_Enabled
            if checked:
                opt.state |= QStyle.State_On
            else:
                opt.state |= QStyle.State_Off

            # center the radio button
            rect = option.rect
            size = QApplication.style().pixelMetric(
                QStyle.PM_ExclusiveIndicatorWidth
            )
            opt.rect = QRect(
                rect.center().x() - size // 2,
                rect.center().y() - size // 2,
                size,
                size,
            )

            QApplication.style().drawControl(
                QStyle.CE_RadioButton, opt, painter
            )
        else:
            super().paint(painter, option, index)

    def editorEvent(self, event, model, option, index):
        if index.column() != 0:
            return False

        if event.type() == event.MouseButtonRelease:
            model.setData(index, Qt.Checked, Qt.CheckStateRole)
            return True

        return False


# ------------------------------------------------------------
# TreeView with exclusive radio + selectable rows
# ------------------------------------------------------------

class RadioChoiceTree(QTreeView):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setRootIsDecorated(False)
        self.setAlternatingRowColors(True)
        self.setSelectionMode(QTreeView.SingleSelection)
        self.setSelectionBehavior(QTreeView.SelectRows)

        self.model = QStandardItemModel(self)
        self.model.setHorizontalHeaderLabels(
            ["Use", "Message Name", "Path"]
        )
        self.setModel(self.model)

        self.setItemDelegateForColumn(0, RadioDelegate())

        self.model.itemChanged.connect(self._on_item_changed)

    def add_row(self, name: str, path: str, active=False):
        radio = QStandardItem()
        radio.setCheckable(True)
        radio.setEditable(False)
        radio.setCheckState(Qt.Checked if active else Qt.Unchecked)

        name_item = QStandardItem(name)
        name_item.setEditable(False)

        path_item = QStandardItem(path)
        path_item.setEditable(False)

        self.model.appendRow([radio, name_item, path_item])

    def _on_item_changed(self, item: QStandardItem):
        if item.column() != 0:
            return
        if item.checkState() != Qt.Checked:
            return

        # Enforce exclusivity
        for row in range(self.model.rowCount()):
            other = self.model.item(row, 0)
            if other is not item:
                other.setCheckState(Qt.Unchecked)

    def active_item(self):
        for row in range(self.model.rowCount()):
            if self.model.item(row, 0).checkState() == Qt.Checked:
                return self.model.item(row, 1).text()
        return None


# ------------------------------------------------------------
# Test window with inspection panel
# ------------------------------------------------------------

class TestWindow(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        self.tree = RadioChoiceTree()
        self.tree.add_row("EngineStatus", "/dbc/powertrain.dbc", active=True)
        self.tree.add_row("VehicleSpeed", "/dbc/chassis.dbc")
        self.tree.add_row("ADASState", "/dbc/adas.dbc")

        self.tree.resizeColumnToContents(0)
        self.tree.resizeColumnToContents(1)

        self.info = QLabel("Select a row to inspect")
        self.info.setStyleSheet("color: gray;")

        layout.addWidget(self.tree)
        layout.addWidget(self.info)

        self.tree.selectionModel().currentChanged.connect(
            self.on_row_selected
        )
        self.tree.model.itemChanged.connect(
            self.on_active_changed
        )

    def on_row_selected(self, current, previous):
        name = current.siblingAtColumn(1).data()
        path = current.siblingAtColumn(2).data()
        self.info.setText(f"Inspecting: {name}\nPath: {path}")

    def on_active_changed(self, item):
        if item.column() == 0 and item.checkState() == Qt.Checked:
            active = self.tree.active_item()
            print(f"[ACTIVE] {active}")


# ------------------------------------------------------------
# main test
# ------------------------------------------------------------

def main():
    app = QApplication(sys.argv)
    w = TestWindow()
    w.resize(720, 360)
    w.setWindowTitle("Radio choice + selectable inspection (Qt)")
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
