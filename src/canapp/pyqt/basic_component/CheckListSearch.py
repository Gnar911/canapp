from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QListWidget, QListWidgetItem, QPushButton
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPalette

class CheckListSearch(QWidget):
    def __init__(
        self,
        items: list[str] | None = None,
        default_state: str = "clear",
        show_controls: bool = True,
    ):
        super().__init__()
        layout = QVBoxLayout(self)
        self._reordering = False
        self._show_controls = bool(show_controls)
        self._default_state = str(default_state or "clear").strip().lower()
        if self._default_state not in {"all", "clear"}:
            self._default_state = "clear"
        search_row = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search…")
        search_row.addWidget(self.search)
        self.all_btn = QPushButton("All")
        self.all_btn.setToolTip("Check all items")
        self.all_btn.setFixedWidth(52)
        search_row.addWidget(self.all_btn)
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setToolTip("Uncheck all items")
        self.clear_btn.setFixedWidth(58)
        search_row.addWidget(self.clear_btn)
        if self._show_controls:
            layout.addLayout(search_row)
        self.list = QListWidget()
        self.list.setSelectionMode(QListWidget.NoSelection)
        self.list.setMouseTracking(True)
        self.list.setStyleSheet("QListWidget::item:hover { background-color: palette(light); }")
        layout.addWidget(self.list)
        if not self._show_controls:
            self.search.hide()
            self.all_btn.hide()
            self.clear_btn.hide()
        if items:
            self.set_items(items)
        self.search.textChanged.connect(self.filter_items)
        self.all_btn.clicked.connect(self.check_all)
        self.clear_btn.clicked.connect(self.uncheck_all)
        self.list.itemChanged.connect(self._on_item_changed)

    def set_items(self, items: list[str]):
        self.list.clear()
        for name in items:
            self.add_item(name)
        self.apply_default_state()

    def set_items_from_text(self, text: str, separator: str = ","):
        items = [value.strip() for value in text.split(separator) if value.strip()]
        self.set_items(items)

    def add_item(self, name: str):
        item = QListWidgetItem(name)
        item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
        item.setCheckState(Qt.Unchecked)
        self._apply_item_visual_state(item)
        self.list.addItem(item)

    def _apply_item_visual_state(self, item: QListWidgetItem):
        palette = self.palette()
        checked_color = palette.color(QPalette.Active, QPalette.Text)
        unchecked_color = palette.color(QPalette.Disabled, QPalette.Text)
        if item.checkState() == Qt.Checked:
            item.setForeground(checked_color)
        else:
            item.setForeground(unchecked_color)

    def filter_items(self, text: str):
        text = text.lower()
        for i in range(self.list.count()):
            item = self.list.item(i)
            item.setHidden(text not in item.text().lower())

    def _on_item_changed(self, item: QListWidgetItem):
        if self._reordering:
            return

        self._apply_item_visual_state(item)

        row = self.list.row(item)
        if row < 0:
            return

        target_row = None
        if item.checkState() == Qt.Checked:
            if row > 0:
                target_row = 0
        else:
            last_row = self.list.count() - 1
            if row < last_row:
                target_row = last_row

        if target_row is None:
            return

        self._reordering = True
        try:
            moved = self.list.takeItem(row)
            if target_row >= self.list.count():
                self.list.addItem(moved)
            else:
                self.list.insertItem(target_row, moved)
            self.filter_items(self.search.text())
        finally:
            self._reordering = False

    def uncheck_all(self):
        self._reordering = True
        try:
            for i in range(self.list.count()):
                item = self.list.item(i)
                item.setCheckState(Qt.Unchecked)
                self._apply_item_visual_state(item)
        finally:
            self._reordering = False

    def check_all(self):
        self._reordering = True
        try:
            for i in range(self.list.count()):
                item = self.list.item(i)
                item.setCheckState(Qt.Checked)
                self._apply_item_visual_state(item)
        finally:
            self._reordering = False

    def apply_default_state(self):
        if self._default_state == "all":
            self.check_all()
        else:
            self.uncheck_all()


if __name__ == "__main__":
    app = QApplication([])
    w = CheckListSearch([
        "ADAS Channel",
        "CDC Channel",
        "Body CAN",
        "Chassis CAN",
        "Powertrain CAN",
    ])
    w.resize(300, 400)
    w.show()
    app.exec()
