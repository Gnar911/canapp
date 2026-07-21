from typing import Any

from PySide6.QtCore import (
    QAbstractItemModel,
    QModelIndex,
    Qt,
)
from PySide6.QtGui import QColor

from canapp.data_object import (
    CANLogLine,
    DecodedSignalLine,
)
from canapp.vm.log_viewmodel import (
    CANLogLine,
    DecodedSignalLine,
    LogViewModel,
)

class TreeLogLazyLoad(QAbstractItemModel):
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
        # self._fetched_count = 0

        self._vm.stateChanged.connect(
            self._reevaluate
        )

        self._reevaluate()

    def _reevaluate(self) -> None:
        self.beginResetModel()
        # self._fetched_count = 0
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
            return self._vm.lazyCount

        if parent.column() != 0:
            return 0

        line = parent.internalPointer()

        if isinstance(line, CANLogLine):
            return len(line.signals)

        return 0

    def canFetchMore(
        self,
        parent: QModelIndex = QModelIndex(),
    ) -> bool:
        if parent.isValid():
            return False

        return (
            self._vm.lazyCount
            < self._vm.totalLines
        )

    def fetchMore(
        self,
        parent: QModelIndex = QModelIndex(),
    ) -> None:
        if parent.isValid():
            return

        if not self.canFetchMore(parent):
            return

        row = self._vm.lazyCount

        self.beginInsertRows(
            QModelIndex(),
            row,
            row,
        )

        self._vm.lazyCount += 1

        self.endInsertRows()

    def hasChildren(
        self,
        parent: QModelIndex = QModelIndex(),
    ) -> bool:
        if not parent.isValid():
            return (
                self._fetched_count > 0
                or self.canFetchMore(parent)
            )

        if parent.column() != 0:
            return False

        line = parent.internalPointer()

        if isinstance(line, CANLogLine):
            return bool(line.signals)

        return False

    """ NOTE: We dont let the Qt to manage the row state itself, we must store it on our ViewModel"""
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
            self._vm.row = row
            line = self._vm.entry

            if line is None:
                return QModelIndex()

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

        logical_row = getattr(
            parent_line,
            "_logical_row",
            None,
        )

        if logical_row is None:
            return QModelIndex()

        return self.createIndex(
            logical_row,
            0,
            parent_line,
        )

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

        if (
            column
            == self.COL_LOG_MESSAGES
        ):
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

        if (
            column
            != self.COL_LOG_MESSAGES
        ):
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

        if not (
            0
            <= section
            < len(headers)
        ):
            return None

        return headers[section]