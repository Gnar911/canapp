from __future__ import annotations

from typing import Any

from PySide6.QtCore import (
    QAbstractItemModel,
    QItemSelectionModel,
    QModelIndex,
    Qt,
)
from PySide6.QtGui import (
    QColor,
    QFont,
)
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QTreeView,
    QVBoxLayout,
    QWidget,
)

from canapp.vm.log_viewmodel import (
    CANLogLine,
    DecodedSignalLine,
    LogViewModel,
)
from PySide6.QtWidgets import QTreeView, QScrollBar, QHBoxLayout

class LogViewModel_QtAdapter(QAbstractItemModel):
    COL_TREND = 0
    COL_LOG_MESSAGES = 1

    COLUMN_COUNT = 2

    TAG_FG = {
        "normal": QColor("#FFFFFF"),
        "change": QColor("#FFFFFF"),
    }

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

            line = self._entries[row]

            return self.createIndex(
                row,
                column,
                line,
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

        signal = parent_line.signals[row]

        return self.createIndex(
            row,
            column,
            signal,
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
        if (
            role
            == Qt.ItemDataRole.ForegroundRole
        ):
            return self.TAG_FG[
                "change"
                if line.changed
                else "normal"
            ]

        if (
            role
            != Qt.ItemDataRole.DisplayRole
        ):
            return None

        column = index.column()

        if column == self.COL_TREND:
            return (
                "●"
                if line.changed
                else "○"
            )

        if column == self.COL_LOG_MESSAGES:
            return line.format_line_log()

        return None

    def _signal_data(
        self,
        index: QModelIndex,
        signal: DecodedSignalLine,
        role: int,
    ) -> Any:
        if (
            role
            == Qt.ItemDataRole.ForegroundRole
        ):
            return self.TAG_FG[
                "change"
                if signal.changed
                else "normal"
            ]

        if (
            role
            != Qt.ItemDataRole.DisplayRole
        ):
            return None

        column = index.column()

        if column == self.COL_TREND:
            return (
                "●"
                if signal.changed
                else ""
            )

        if column != self.COL_LOG_MESSAGES:
            return None

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

        return (
            Qt.ItemFlag.ItemIsEnabled
            | Qt.ItemFlag.ItemIsSelectable
        )

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
            "",
            "Log Messages",
        )

        if not 0 <= section < len(headers):
            return None

        return headers[section]


class TreeLogSelectionModel(
    QItemSelectionModel
):
    pass


class TreeLogView(QWidget):
    _HOVER_STYLESHEET = """
        QTreeView::item:hover {
            background: rgba(255, 255, 255, 5);
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

        self.model_ = LogViewModel_QtAdapter(
            self._vm,
            self,
        )

        self.view.setModel(
            self.model_
        )

        self.select_model = TreeLogSelectionModel(
            self.model_,
            self.view,
        )

        self.view.setSelectionModel(
            self.select_model
        )

        mono = QFont(
            "Consolas",
            10,
        )

        mono.setStyleHint(
            QFont.StyleHint.Monospace
        )

        self.view.setFont(mono)

        header = self.view.header()

        header.setStretchLastSection(
            False
        )

        header.setSectionResizeMode(
            QHeaderView.ResizeMode.Interactive
        )

        header.setFixedHeight(20)

        self.view.setColumnWidth(
            LogViewModel_QtAdapter.COL_TREND,
            80,
        )

        self.view.setColumnWidth(
            LogViewModel_QtAdapter.COL_LOG_MESSAGES,
            1600,
        )

        self.view.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection
        )

        self.view.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
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

        self.view.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        self.view.setStyleSheet(
            self._HOVER_STYLESHEET
        )

        self.scrollbar = QScrollBar(
            Qt.Orientation.Vertical,
            self,
        )

        layout = QHBoxLayout(self)

        layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        layout.setSpacing(0)

        layout.addWidget(
            self.view
        )

        layout.addWidget(
            self.scrollbar
        )

        self.scrollbar.valueChanged.connect(
            self._on_scroll
        )

        self._vm.stateChanged.connect(
            self._on_state_changed
        )

        self._sync_scrollbar()

    def _on_scroll(
        self,
        first: int,
    ) -> None:
        _, count = self._vm.viewport

        self._vm.viewport = (
            first,
            count,
        )

    def _on_state_changed(
        self,
    ) -> None:
        self.model_._reevaluate()
        self._sync_scrollbar()

    def _sync_scrollbar(
        self,
    ) -> None:
        first, count = self._vm.viewport

        maximum = max(
            self._vm.totalLines - count,
            0,
        )

        self.scrollbar.blockSignals(True)

        self.scrollbar.setRange(
            0,
            maximum,
        )

        self.scrollbar.setPageStep(
            count
        )

        self.scrollbar.setSingleStep(
            1
        )

        self.scrollbar.setValue(
            min(first, maximum)
        )

        self.scrollbar.blockSignals(False)