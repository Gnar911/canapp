from typing import Any, Optional

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt, Signal, QItemSelectionModel
from PySide6.QtWidgets import (
    QWidget,
    QTreeView,
    QVBoxLayout,
    QStyledItemDelegate,
    QStyleOptionButton,
    QStyle,
)

class CheckboxTableModel(QAbstractTableModel):
    checkToggled = Signal(int, bool)
    COL_CHECK = 0

    def __init__(
        self,
        parent=None,
        heading_num: int = 1,
        headings: Optional[list[str]] = None,
    ):
        super().__init__(parent)
        self._items: list[Any] = []
        self._checked: dict[int, bool] = {}
        self._heading_num = max(1, heading_num)
        self._headings = ["#"]
        self.set_headings(headings or ["#"])

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._items)

    def columnCount(self, parent=QModelIndex()) -> int:
        return self._heading_num

    def headerData(self, section, orientation, role):
        if role != Qt.DisplayRole or orientation != Qt.Horizontal:
            return None
        if 0 <= section < len(self._headings):
            return self._headings[section]
        return f"Column {section}"

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        row = index.row()
        col = index.column()
        item = self._items[row]

        if col == self.COL_CHECK and role == Qt.CheckStateRole:
            return Qt.Checked if self._checked.get(row, False) else Qt.Unchecked

        if role == Qt.DisplayRole:
            return self._get_cell_value(item, col)

        return None

    def flags(self, index):
        if not index.isValid():
            return Qt.NoItemFlags

        flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        if index.column() == self.COL_CHECK:
            flags |= Qt.ItemIsUserCheckable
        return flags

    def setData(self, index, value, role):
        if index.column() == self.COL_CHECK and role == Qt.CheckStateRole:
            checked = value == Qt.Checked
            self._checked[index.row()] = checked
            self.dataChanged.emit(index, index)
            self.checkToggled.emit(index.row(), checked)
            return True
        return False

    def set_headings(self, headings: list[str]):
        normalized = headings[:] if headings else ["#"]
        if not normalized:
            normalized = ["#"]
        if normalized[0] != "#":
            normalized[0] = "#"

        self.beginResetModel()
        self._headings = normalized
        self._heading_num = len(normalized)
        self.endResetModel()

    def set_heading_num(self, heading_num: int):
        if heading_num < 1:
            heading_num = 1

        self.beginResetModel()
        self._heading_num = heading_num
        if len(self._headings) < heading_num:
            self._headings.extend(
                [f"Column {idx}" for idx in range(len(self._headings), heading_num)]
            )
        else:
            self._headings = self._headings[:heading_num]
        self.endResetModel()

    def add_item(self, item: Any):
        row = len(self._items)
        self.beginInsertRows(QModelIndex(), row, row)
        self._items.append(item)
        self._checked[row] = False
        self.endInsertRows()

    def set_items(self, items: list[Any]):
        self.beginResetModel()
        self._items = list(items)
        self._checked = {idx: False for idx, _ in enumerate(self._items)}
        self.endResetModel()

    def delete_all(self):
        if not self._items:
            return
        self.beginResetModel()
        self._items.clear()
        self._checked.clear()
        self.endResetModel()

    def remove_rows(self, rows: list[int]):
        for row in sorted(set(rows), reverse=True):
            if row < 0 or row >= len(self._items):
                continue
            self.beginRemoveRows(QModelIndex(), row, row)
            del self._items[row]
            self._checked.pop(row, None)
            self.endRemoveRows()
        self._reindex_checked()

    def item_at(self, row: int) -> Any:
        return self._items[row]

    def items(self) -> list[Any]:
        return self._items

    def _reindex_checked(self):
        self._checked = {idx: self._checked.get(idx, False) for idx in range(len(self._items))}

    def _get_cell_value(self, item: Any, col: int):
        return item if col == 0 else ""


class _CheckBoxDelegate(QStyledItemDelegate):
    def editorEvent(self, event, model, option, index):
        if index.column() != CheckboxTableModel.COL_CHECK:
            return super().editorEvent(event, model, option, index)

        if event.type() not in (event.MouseButtonPress, event.MouseButtonRelease):
            return super().editorEvent(event, model, option, index)

        opt = QStyleOptionButton()
        opt.rect = option.rect
        check_rect = option.widget.style().subElementRect(
            QStyle.SE_CheckBoxIndicator, opt, option.widget
        )
        check_rect.moveCenter(option.rect.center())

        if not check_rect.contains(event.pos()):
            return False

        current = model.data(index, Qt.CheckStateRole)
        new_state = Qt.Unchecked if current == Qt.Checked else Qt.Checked
        return model.setData(index, new_state, Qt.CheckStateRole)


class CheckboxTable(QWidget):
    def __init__(self, parent=None, model: Optional[CheckboxTableModel] = None):
        super().__init__(parent)

        self.model = model or CheckboxTableModel(self)
        self.view = QTreeView(self)
        self.view.setModel(self.model)
        self.selection_model = QItemSelectionModel(self.model, self.view)
        self.view.setSelectionModel(self.selection_model)

        self.view.setRootIsDecorated(False)
        self.view.setAlternatingRowColors(True)
        self.view.setSelectionMode(QTreeView.ExtendedSelection)
        self.view.setAllColumnsShowFocus(True)
        self.view.setUniformRowHeights(True)
        self.view.setSelectionBehavior(QTreeView.SelectRows)
        self.view.setEditTriggers(QTreeView.NoEditTriggers)
        self.view.setItemDelegateForColumn(CheckboxTableModel.COL_CHECK, _CheckBoxDelegate(self.view))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.view)

        self.model.checkToggled.connect(self._on_check_toggled)

    def set_model(self, model: CheckboxTableModel):
        self.model = model
        self.view.setModel(self.model)
        self.selection_model = QItemSelectionModel(self.model, self.view)
        self.view.setSelectionModel(self.selection_model)
        self.view.setItemDelegateForColumn(CheckboxTableModel.COL_CHECK, _CheckBoxDelegate(self.view))
        self.model.checkToggled.connect(self._on_check_toggled)

    def set_headings(self, headings: list[str]):
        self.model.set_headings(headings)

    def set_heading_num(self, heading_num: int):
        self.model.set_heading_num(heading_num)

    def set_column_widths(self, widths: list[int]):
        for col, width in enumerate(widths):
            self.view.setColumnWidth(col, width)

    def add_item(self, item: Any):
        self.model.add_item(item)

    def set_items(self, items: list[Any]):
        self.model.set_items(items)

    def remove_all(self):
        self.model.delete_all()

    def remove_selected(self):
        rows = sorted({idx.row() for idx in self.selection_model.selectedIndexes()}, reverse=True)
        self.model.remove_rows(rows)

    def select_row(self, row: int):
        index = self.model.index(row, 0)
        if index.isValid():
            self.selection_model.select(index, QItemSelectionModel.Select | QItemSelectionModel.Rows)

    def deselect_row(self, row: int):
        index = self.model.index(row, 0)
        if index.isValid():
            self.selection_model.select(index, QItemSelectionModel.Deselect | QItemSelectionModel.Rows)

    def clear_selection(self):
        self.selection_model.clearSelection()

    def selected_rows(self) -> list[int]:
        return sorted({idx.row() for idx in self.selection_model.selectedIndexes()})

    def current_selected_items(self, data_column: int = 1) -> list[Any]:
        rows = {
            index.row()
            for index in self.selection_model.selectedIndexes()
            if index.column() == data_column
        }
        return [self.model.item_at(row) for row in rows]

    def _on_check_toggled(self, row: int, checked: bool):
        if checked:
            self.select_row(row)
        else:
            self.deselect_row(row)


if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication

    class _DemoModel(CheckboxTableModel):
        def _get_cell_value(self, item: Any, col: int):
            if col == self.COL_CHECK:
                return ""
            if col == 1:
                return str(item)
            return ""

    app = QApplication(sys.argv)

    demo_model = _DemoModel(headings=["#", "Name"])
    demo_model.set_items(["EngineSpeed", "VehicleSpeed", "CoolantTemp"])

    demo = CheckboxTable(model=demo_model)
    demo.setWindowTitle("CheckboxTable Demo")
    demo.resize(360, 220)
    demo.show()

    sys.exit(app.exec())
