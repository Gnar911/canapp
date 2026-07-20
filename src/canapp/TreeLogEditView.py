from __future__ import annotations

from copy import deepcopy
from typing import Any, Optional

from PySide6.QtCore import (
    QAbstractItemModel,
    QEvent,
    QItemSelectionModel,
    QModelIndex,
    QPersistentModelIndex,
    QTimer,
    Qt,
    Signal,
)
from PySide6.QtGui import (
    QColor,
    QCursor,
    QFont,
)
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QHeaderView,
    QLineEdit,
    QStyledItemDelegate,
    QToolTip,
    QTreeView,
    QVBoxLayout,
    QWidget,
)

from canapp.vm.log_viewmodel import (
    CANLogLine,
    DecodedSignalLine,
    LogViewModel,
)
from canapp.widgets.ParseableEditBox import (
    TimeEditBox,
    RawBytesEditBox,
)
from canapp.widgets.DLCSpinbox import DLCSpinBox
from canapp.widgets.DlcRawBinder import DlcRawBinder


class LogEditViewModel_QtAdapter(QAbstractItemModel):
    COL_STR_TIMESTAMP = 0
    COL_STR_DIFF = 1
    COL_DIRECTION = 2
    COL_CAN_ID_STR = 3
    COL_DATA_LEN = 4
    COL_RAW_DATA_BYTES = 5

    COLUMN_COUNT = 6

    def __init__(
        self,
        view_model: LogViewModel,
        parent=None,
    ):
        super().__init__(parent)

        self._vm = view_model
        self._entries: list[CANLogLine] = []

        self._reevaluate()

    def _reevaluate(self) -> None:
        entries = self._vm.entries

        self.beginResetModel()
        self._entries = entries
        self.endResetModel()

    def columnCount(
        self,
        parent: QModelIndex = QModelIndex(),
    ) -> int:
        return self.COLUMN_COUNT

    def rowCount(
        self,
        parent: QModelIndex = QModelIndex(),
    ) -> int:
        if not parent.isValid():
            return len(self._entries)

        if parent.column() != 0:
            return 0

        line = parent.internalPointer()

        if isinstance(line, CANLogLine):
            return len(line.signals)

        return 0

    def hasChildren(
        self,
        parent: QModelIndex = QModelIndex(),
    ) -> bool:
        if not parent.isValid():
            return bool(self._entries)

        if parent.column() != 0:
            return False

        line = parent.internalPointer()

        if isinstance(line, CANLogLine):
            return bool(line.signals)

        return False

    def index(
        self,
        row: int,
        column: int,
        parent: QModelIndex = QModelIndex(),
    ) -> QModelIndex:
        if not self.hasIndex(
            row,
            column,
            parent,
        ):
            return QModelIndex()

        if not parent.isValid():
            if not 0 <= row < len(self._entries):
                return QModelIndex()

            return self.createIndex(
                row,
                column,
                self._entries[row],
            )

        parent_line = parent.internalPointer()

        if not isinstance(
            parent_line,
            CANLogLine,
        ):
            return QModelIndex()

        if not 0 <= row < len(
            parent_line.signals
        ):
            return QModelIndex()

        return self.createIndex(
            row,
            column,
            parent_line.signals[row],
        )

    def parent(
        self,
        index: QModelIndex,
    ) -> QModelIndex:
        if not index.isValid():
            return QModelIndex()

        obj = index.internalPointer()

        if isinstance(obj, CANLogLine):
            return QModelIndex()

        if not isinstance(
            obj,
            DecodedSignalLine,
        ):
            return QModelIndex()

        parent_line = obj.parent

        if parent_line is None:
            return QModelIndex()

        for row, line in enumerate(
            self._entries
        ):
            if line is parent_line:
                return self.createIndex(
                    row,
                    0,
                    parent_line,
                )

        return QModelIndex()

    def data(
        self,
        index: QModelIndex,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        if not index.isValid():
            return None

        obj = index.internalPointer()

        if isinstance(obj, CANLogLine):
            return self._line_data(
                index,
                obj,
                role,
            )

        if isinstance(
            obj,
            DecodedSignalLine,
        ):
            return self._signal_data(
                index,
                obj,
                role,
            )

        return None

    def _line_data(
        self,
        index: QModelIndex,
        line: CANLogLine,
        role: int,
    ) -> Any:
        if role not in (
            Qt.ItemDataRole.DisplayRole,
            Qt.ItemDataRole.EditRole,
        ):
            return None

        column = index.column()

        if column == self.COL_STR_TIMESTAMP:
            return str(line.timestamp)

        if column == self.COL_STR_DIFF:
            return line.get_format_timediff()

        if column == self.COL_DIRECTION:
            return str(line.direction)

        if column == self.COL_CAN_ID_STR:
            return f"{int(line.can_id):X}"

        if column == self.COL_DATA_LEN:
            return int(line.data_len)

        if column == self.COL_RAW_DATA_BYTES:
            return str(line.raw_data)

        return None

    def _signal_data(
        self,
        index: QModelIndex,
        signal: DecodedSignalLine,
        role: int,
    ) -> Any:
        if (
            role
            != Qt.ItemDataRole.DisplayRole
        ):
            return None

        if (
            index.column()
            != self.COL_STR_TIMESTAMP
        ):
            return ""

        signal_name = str(
            getattr(
                signal,
                "_runtime_signal_name",
                "",
            )
            or ""
        )

        sig_info = getattr(
            signal,
            "_sig_info",
            None,
        )

        unit = ""

        if sig_info is not None:
            unit = str(
                getattr(
                    sig_info,
                    "unit",
                    "",
                )
                or ""
            )

        text = (
            f"{signal_name}: "
            f"{signal.raw_value}"
        )

        if unit:
            text += f" {unit}"

        return text

    def flags(
        self,
        index: QModelIndex,
    ) -> Qt.ItemFlag:
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags

        flags = (
            Qt.ItemFlag.ItemIsEnabled
            | Qt.ItemFlag.ItemIsSelectable
        )

        obj = index.internalPointer()

        if not isinstance(
            obj,
            CANLogLine,
        ):
            return flags

        if index.column() in (
            self.COL_STR_DIFF,
            self.COL_DIRECTION,
            self.COL_DATA_LEN,
            self.COL_RAW_DATA_BYTES,
        ):
            flags |= Qt.ItemFlag.ItemIsEditable

        return flags

    def setData(
        self,
        index: QModelIndex,
        value: Any,
        role: int = Qt.ItemDataRole.EditRole,
    ) -> bool:
        if (
            role
            != Qt.ItemDataRole.EditRole
        ):
            return False

        if not index.isValid():
            return False

        obj = index.internalPointer()

        if not isinstance(
            obj,
            CANLogLine,
        ):
            return False

        if not (
            self.flags(index)
            & Qt.ItemFlag.ItemIsEditable
        ):
            return False

        edited = deepcopy(obj)

        column = index.column()

        if column == self.COL_STR_DIFF:
            edited.set_format_timediff(
                str(value)
            )

        elif column == self.COL_DIRECTION:
            edited.direction = str(value)

        elif column == self.COL_DATA_LEN:
            edited.data_len = int(value)

        elif column == self.COL_RAW_DATA_BYTES:
            edited.raw_data = str(value)

        else:
            return False

        editing = dict(
            self._vm.editing_line
        )

        editing[
            edited.line_number
        ] = edited

        self._vm.editing_line = editing

        return True

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        if (
            role
            != Qt.ItemDataRole.DisplayRole
        ):
            return None

        if (
            orientation
            != Qt.Orientation.Horizontal
        ):
            return None

        headers = (
            "Timestamp",
            "Diff",
            "Direction",
            "CAN ID",
            "DLC",
            "Data",
        )

        if not 0 <= section < len(headers):
            return None

        return headers[section]


class TreeLogEditSelectionModel(
    QItemSelectionModel
):
    pass


class _TreeLogEditDelegate(
    QStyledItemDelegate
):
    def __init__(
        self,
        parent=None,
    ):
        super().__init__(parent)

        self._dlc_raw_binder = (
            DlcRawBinder()
        )

        self._row_height: Optional[int] = None

        self._hovered_index = (
            QModelIndex()
        )

    def set_hovered_index(
        self,
        index: QModelIndex,
    ) -> tuple[
        QModelIndex,
        QModelIndex,
    ]:
        old = self._hovered_index

        new = (
            index
            if index.isValid()
            else QModelIndex()
        )

        if self._is_same_cell(
            old,
            new,
        ):
            return old, new

        self._hovered_index = new

        return old, new

    def clear_hover(
        self,
    ) -> QModelIndex:
        old = self._hovered_index

        self._hovered_index = (
            QModelIndex()
        )

        return old

    def _is_same_cell(
        self,
        a: QModelIndex,
        b: QModelIndex,
    ) -> bool:
        return (
            a.isValid()
            and b.isValid()
            and a.row() == b.row()
            and a.column() == b.column()
            and a.parent() == b.parent()
        )

    def set_row_height(
        self,
        height: Optional[int],
    ) -> None:
        self._row_height = (
            None
            if height is None
            else max(
                1,
                int(height),
            )
        )

    def sizeHint(
        self,
        option,
        index,
    ):
        size = super().sizeHint(
            option,
            index,
        )

        if (
            self._row_height
            is not None
        ):
            size.setHeight(
                self._row_height
            )

        return size

    def createEditor(
        self,
        parent,
        option,
        index,
    ):
        if not index.isValid():
            return None

        model = index.model()

        if not (
            model.flags(index)
            & Qt.ItemFlag.ItemIsEditable
        ):
            return None

        column = index.column()

        if (
            column
            == model.COL_STR_DIFF
        ):
            return TimeEditBox(
                parent
            )

        if (
            column
            == model.COL_DIRECTION
        ):
            editor = QComboBox(
                parent
            )

            editor.addItems(
                [
                    "Rx",
                    "Tx",
                ]
            )

            return editor

        if (
            column
            == model.COL_DATA_LEN
        ):
            editor = DLCSpinBox(
                parent
            )

            self._dlc_raw_binder.bind_dlc_editor(
                editor,
                index,
            )

            return editor

        if (
            column
            == model.COL_RAW_DATA_BYTES
        ):
            editor = RawBytesEditBox(
                parent
            )

            self._dlc_raw_binder.bind_raw_editor(
                editor,
                index,
            )

            return editor

        return None

    def setEditorData(
        self,
        editor,
        index,
    ) -> None:
        value = index.model().data(
            index,
            Qt.ItemDataRole.EditRole,
        )

        if isinstance(
            editor,
            TimeEditBox,
        ):
            editor.setText(
                str(
                    value
                    or "0ms"
                )
            )
            return

        if isinstance(
            editor,
            QComboBox,
        ):
            text = str(
                value
                or "Rx"
            )

            combo_index = (
                editor.findText(
                    text
                )
            )

            editor.setCurrentIndex(
                combo_index
                if combo_index >= 0
                else 0
            )

            return

        if isinstance(
            editor,
            DLCSpinBox,
        ):
            try:
                editor.set_dlc_value(
                    int(value)
                )
            except (
                TypeError,
                ValueError,
            ):
                editor.set_dlc_value(
                    0
                )

            return

        if isinstance(
            editor,
            RawBytesEditBox,
        ):
            editor.setText(
                str(
                    value
                    or ""
                )
            )

            obj = (
                index.internalPointer()
            )

            if isinstance(
                obj,
                CANLogLine,
            ):
                self._dlc_raw_binder.normalize_raw_editor_for_row(
                    editor,
                    int(
                        obj.data_len
                    ),
                )

            return

        if isinstance(
            editor,
            QLineEdit,
        ):
            editor.setText(
                str(
                    value
                    or ""
                )
            )

            return

        super().setEditorData(
            editor,
            index,
        )

    def setModelData(
        self,
        editor,
        model,
        index,
    ) -> None:
        if isinstance(
            editor,
            TimeEditBox,
        ):
            editor._commit()

            value = (
                editor.text()
            )

        elif isinstance(
            editor,
            QComboBox,
        ):
            value = (
                editor.currentText()
            )

        elif isinstance(
            editor,
            DLCSpinBox,
        ):
            value = (
                editor.current_dlc_value()
            )

        elif isinstance(
            editor,
            RawBytesEditBox,
        ):
            value = (
                editor.text()
            )

        elif isinstance(
            editor,
            QLineEdit,
        ):
            value = (
                editor.text()
            )

        else:
            super().setModelData(
                editor,
                model,
                index,
            )
            return

        model.setData(
            index,
            value,
            Qt.ItemDataRole.EditRole,
        )


class TreeLogEditView(QWidget):
    undoAvailabilityChanged = Signal(bool)

    _HOVER_STYLESHEET = """
        QTreeView::item:hover {
            background: rgba(255, 255, 255, 12);
        }
    """

    def __init__(
        self,
        view_model: LogViewModel,
        parent=None,
    ):
        super().__init__(parent)

        self._vm = view_model

        self.view = QTreeView(self)

        self.model_ = (
            LogEditViewModel_QtAdapter(
                self._vm,
                self,
            )
        )

        self.view.setModel(
            self.model_
        )

        self.select_model = (
            TreeLogEditSelectionModel(
                self.model_,
                self.view,
            )
        )

        self.view.setSelectionModel(
            self.select_model
        )

        self._edit_delegate = (
            _TreeLogEditDelegate(
                self.view
            )
        )

        self.view.setItemDelegate(
            self._edit_delegate
        )

        self._undo_available = False

        self._hover_tooltip_timer = (
            QTimer(self)
        )

        self._hover_tooltip_timer.setSingleShot(
            True
        )

        self._hover_tooltip_timer.timeout.connect(
            self._show_edit_tooltip
        )

        self._hover_tooltip_index = (
            QPersistentModelIndex()
        )

        self._hover_expanded_parent = (
            QPersistentModelIndex()
        )

        mono = QFont(
            "Consolas",
            10,
        )

        mono.setStyleHint(
            QFont.StyleHint.Monospace
        )

        self.view.setFont(
            mono
        )

        header = self.view.header()

        header.setStretchLastSection(
            False
        )

        header.setSectionResizeMode(
            QHeaderView.ResizeMode.Interactive
        )

        header.setFixedHeight(
            20
        )

        self.view.setColumnWidth(
            LogEditViewModel_QtAdapter.COL_STR_TIMESTAMP,
            110,
        )

        self.view.setColumnWidth(
            LogEditViewModel_QtAdapter.COL_STR_DIFF,
            90,
        )

        self.view.setColumnWidth(
            LogEditViewModel_QtAdapter.COL_DIRECTION,
            90,
        )

        self.view.setColumnWidth(
            LogEditViewModel_QtAdapter.COL_CAN_ID_STR,
            90,
        )

        self.view.setColumnWidth(
            LogEditViewModel_QtAdapter.COL_DATA_LEN,
            70,
        )

        self.view.setColumnWidth(
            LogEditViewModel_QtAdapter.COL_RAW_DATA_BYTES,
            1120,
        )

        self.view.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection
        )

        self.view.setEditTriggers(
            QAbstractItemView.EditTrigger.DoubleClicked
            | QAbstractItemView.EditTrigger.EditKeyPressed
            | QAbstractItemView.EditTrigger.SelectedClicked
        )

        self.view.setUniformRowHeights(
            True
        )

        self.view.setAnimated(
            False
        )

        self.view.setAutoScroll(
            True
        )

        self.view.viewport().setMouseTracking(
            True
        )

        self.view.setStyleSheet(
            self._HOVER_STYLESHEET
        )

        self.view.entered.connect(
            self._on_item_hovered
        )

        self.view.viewport().installEventFilter(
            self
        )

        layout = QVBoxLayout(
            self
        )

        layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        layout.addWidget(
            self.view
        )

        self.select_model.currentChanged.connect(
            self._on_current_changed
        )

        self._vm.stateChanged.connect(
            self._on_state_changed
        )

        self._emit_undo_availability(
            force=True
        )

    def _on_state_changed(
        self,
    ) -> None:
        self._clear_hover_state()

        self.model_._reevaluate()

        self._emit_undo_availability()

    def _current_line(
        self,
    ) -> CANLogLine | None:
        index = (
            self.view.currentIndex()
        )

        if not index.isValid():
            return None

        obj = (
            index.internalPointer()
        )

        if isinstance(
            obj,
            CANLogLine,
        ):
            return obj

        if isinstance(
            obj,
            DecodedSignalLine,
        ):
            return obj.parent

        return None

    def _on_current_changed(
        self,
        current: QModelIndex,
        previous: QModelIndex,
    ) -> None:
        self._emit_undo_availability()

    def is_current_row_undo_available(
        self,
    ) -> bool:
        line = self._current_line()

        if line is None:
            return False

        return (
            line.line_number
            in self._vm.editing_line
        )

    def _emit_undo_availability(
        self,
        force: bool = False,
    ) -> None:
        available = (
            self.is_current_row_undo_available()
        )

        if (
            force
            or available
            != self._undo_available
        ):
            self._undo_available = (
                available
            )

            self.undoAvailabilityChanged.emit(
                available
            )

    def undo_current_edit(
        self,
    ) -> bool:
        line = self._current_line()

        if line is None:
            return False

        if (
            line.line_number
            not in self._vm.editing_line
        ):
            return False

        editing = dict(
            self._vm.editing_line
        )

        del editing[
            line.line_number
        ]

        self._vm.editing_line = (
            editing
        )

        return True

    def _on_item_hovered(
        self,
        index: QModelIndex,
    ) -> None:
        editable_index = (
            index
            if (
                index.isValid()
                and bool(
                    self.model_.flags(index)
                    & Qt.ItemFlag.ItemIsEditable
                )
            )
            else QModelIndex()
        )

        old_index, new_index = (
            self._edit_delegate.set_hovered_index(
                editable_index
            )
        )

        if editable_index.isValid():
            persistent = (
                QPersistentModelIndex(
                    editable_index
                )
            )

            if (
                self._hover_tooltip_index
                != persistent
            ):
                self._hover_tooltip_index = (
                    persistent
                )

                self._hover_tooltip_timer.start(
                    1600
                )

        else:
            self._hover_tooltip_timer.stop()

            self._hover_tooltip_index = (
                QPersistentModelIndex()
            )

            QToolTip.hideText()

            self._collapse_hover_expanded_row()

        if old_index.isValid():
            self.view.viewport().update(
                self.view.visualRect(
                    old_index
                )
            )

        if new_index.isValid():
            self.view.viewport().update(
                self.view.visualRect(
                    new_index
                )
            )

    def _show_edit_tooltip(
        self,
    ) -> None:
        index = QModelIndex(
            self._hover_tooltip_index
        )

        if not index.isValid():
            return

        if not bool(
            self.model_.flags(index)
            & Qt.ItemFlag.ItemIsEditable
        ):
            return

        rect = self.view.visualRect(
            index
        )

        if (
            not rect.isValid()
            or rect.isEmpty()
        ):
            return

        cursor_local = (
            self.view.viewport().mapFromGlobal(
                QCursor.pos()
            )
        )

        if not rect.contains(
            cursor_local
        ):
            return

        QToolTip.showText(
            QCursor.pos(),
            "Double click to edit",
            self.view.viewport(),
            rect,
        )

        self._expand_hover_row(
            index
        )

    def _expand_hover_row(
        self,
        index: QModelIndex,
    ) -> None:
        if not index.isValid():
            return

        parent_index = (
            index.siblingAtColumn(0)
        )

        if not parent_index.isValid():
            return

        if not self.model_.hasChildren(
            parent_index
        ):
            return

        current_parent = QModelIndex(
            self._hover_expanded_parent
        )

        if (
            current_parent.isValid()
            and (
                current_parent.row()
                != parent_index.row()
                or current_parent.parent()
                != parent_index.parent()
            )
        ):
            self.view.setExpanded(
                current_parent,
                False,
            )

        self.view.setExpanded(
            parent_index,
            True,
        )

        self._hover_expanded_parent = (
            QPersistentModelIndex(
                parent_index
            )
        )

    def _collapse_hover_expanded_row(
        self,
    ) -> None:
        current_parent = QModelIndex(
            self._hover_expanded_parent
        )

        if current_parent.isValid():
            self.view.setExpanded(
                current_parent,
                False,
            )

        self._hover_expanded_parent = (
            QPersistentModelIndex()
        )

    def _clear_hover_state(
        self,
    ) -> None:
        old_index = (
            self._edit_delegate.clear_hover()
        )

        if old_index.isValid():
            self.view.viewport().update(
                self.view.visualRect(
                    old_index
                )
            )

        self._hover_tooltip_timer.stop()

        self._hover_tooltip_index = (
            QPersistentModelIndex()
        )

        QToolTip.hideText()

        self._collapse_hover_expanded_row()

    def eventFilter(
        self,
        obj,
        event,
    ) -> bool:
        if (
            obj is self.view.viewport()
            and event.type()
            == QEvent.Type.Leave
        ):
            self._clear_hover_state()

        return super().eventFilter(
            obj,
            event,
        )