# from can_sdk.dbc_manager import CANDBManager
# from can_sdk.connection_viewmodel import CANConnectManager, Handle
# from can_sdk.logger_setup import LOG, setup_logger
from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QGroupBox, QVBoxLayout, QHBoxLayout,
    QLineEdit, QComboBox, QMessageBox, QLabel, QPushButton, QSizePolicy, 
    QApplication, QStyle, QToolButton
)
from PySide6.QtCore import Slot, Qt
# from can_sdk.parser import LogParser
# from ui_sdk.components.pyqt.TreeMonitorTable import TreeMonitorTable
"""
The steps to form a panel View-Model
1. The models it is using/components UI
2. The model function for View -> Model event
3. The event for Model-> View
"""
from typing import Optional, List, Tuple
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QToolButton,
    QComboBox, QApplication, QStyle, QFrame, QSizePolicy)
from cansrv.test.mock_vm import *
# from cansrv.application_events import ParserStatusEvent, DBCLoadedEvent
# from cansrv.status import ParserStatus
from cansrv.file_service import get_file_service, LogId, MetaDataStorageInterface, DBCId, CANDBInfo, ViewBrowser, LogQuery
from canapp.vm.data_object import CANLogLine, DecodedSignalLine
from typing import Literal
from lw.logger_setup import LOG
from lw.qt.declarative import bind
RowId = int
from PySide6.QtCore import QThread
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

from canapp.vm.record_viewmodel import (
    CANLogLine,
    DecodedSignalLine,
    RecordViewModel,
)
from PySide6.QtWidgets import QTreeView, QScrollBar, QHBoxLayout
from lw.logger_setup import LOG
from canapp.FileLogViewPanel import LogViewModel_QtAdapter

"""
    # def rowCount(
    #     self,
    #     parent: QModelIndex = QModelIndex(),
    # ) -> int:
    #     if not parent.isValid():
    #         return self._vm.lazyCount

    #     if parent.column() != 0:
    #         return 0

    #     line = parent.internalPointer()

    #     if isinstance(line, CANLogLine):
    #         return len(line.signals)

    #     return 0

    # def canFetchMore(
    #     self,
    #     parent: QModelIndex = QModelIndex(),
    # ) -> bool:
    #     if parent.isValid():
    #         return False

    #     return (
    #         self._vm.lazyCount
    #         < self._vm.totalLines
    #     )

    # def fetchMore(
    #     self,
    #     parent: QModelIndex = QModelIndex(),
    # ) -> None:
    #     if parent.isValid():
    #         return

    #     if not self.canFetchMore(parent):
    #         return

    #     row = self._vm.lazyCount

    #     self.beginInsertRows(
    #         QModelIndex(),
    #         row,
    #         row,
    #     )

    #     self._vm.lazyCount += 1

    #     self.endInsertRows()

"""
class TreeLogLazyLoadModel(QAbstractItemModel):
    COL_TREND = 0
    COL_LOG_MESSAGES = 1
    COLUMN_COUNT = 2
    TAG_FG = {
        "normal": QColor("#FFFFFF"),
        "change": QColor("#FFFFFF"),
    }

    def __init__(
        self,
        vm: RecordViewModel,
        parent=None,
    ):
        super().__init__(parent)

        self._vm = vm
        self._known_rows = vm.totalRows

        self._vm.recordingChanged.connect(self._reevaluate)
        self._vm.progressChanged.connect(self._on_total_rows_changed)

        """ NOTE: QML bindings automatically evaluate once when the binding is established
                Qt Widgets do not have this automatic initial evaluation
        """
        self._reevaluate()

    def _reevaluate(self) -> None:
        self.beginResetModel()
        self.endResetModel()

    def _on_total_rows_changed(self):
        new_total = self._vm.totalRows
        if new_total == self._known_rows:
            return

        if new_total < self._known_rows:
            self.beginRemoveRows(
                QModelIndex(),
                new_total,
                self._known_rows - 1,
            )

            self._known_rows = new_total

            self.endRemoveRows()
            return

        self.beginInsertRows(
            QModelIndex(),
            self._known_rows,
            new_total - 1,
        )
        self._known_rows = new_total
        self.endInsertRows()

    def columnCount(
        self,
        parent: QModelIndex = QModelIndex(),
    ) -> int:
        return self.COLUMN_COUNT

    def rowCount(
        self,
        parent=QModelIndex(),
    ):
        # Flat monitor tree: top-level message rows only.
        if parent.isValid():
            obj = parent.internalPointer()

            if isinstance(obj, CANLogLine):
                return len(obj.signals)

            return 0
        return self._known_rows

    def hasChildren(
        self,
        parent: QModelIndex = QModelIndex(),
    ) -> bool:
        #LOG.debug("hasChildren(%s)", parent.isValid())
        if not parent.isValid():
            # return (
            #     self._vm.lazyCount > 0
            #     or self.canFetchMore(parent)
            # )
            return self._known_rows > 0

        if parent.column() != 0:
            return False

        line = parent.internalPointer()

        if isinstance(line, CANLogLine):
            return bool(line.signals)

        return False

    """ NOTE: We dont let the Qt to manage the row state itself, we must store it on our ViewModel"""
    """ 20260731 BUG: 
        In C++, QModelIndex stores an opaque pointer (internalPointer). In PySide, when you do:

        self.createIndex(row, column, python_object)

        Shiboken wraps the Python object, but it does not magically keep a strong reference to an object that has no other owners.    

            line = Dummy(f"Row {row + 1}")
    """
    def index(
        self,
        row: int,
        column: int,
        parent: QModelIndex = QModelIndex(),
    ) -> QModelIndex:
        #LOG.debug("index(%d,%d,parent=%s)", row, column, parent.isValid())
        if not self.hasIndex(
            row,
            column,
            parent,
        ):
            return QModelIndex()

        if not parent.isValid():
            #self._vm.row = row
            line = self._vm.entry
            line = self._vm.entries[row]

            # if line is None:
            #     return QModelIndex()

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
#
    def parent(
        self,
        index: QModelIndex,
    ) -> QModelIndex:
        #LOG.debug("parent()")
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

        logical_row = parent_line.line_number

        if logical_row is None:
            return QModelIndex()

        return self.createIndex(
            logical_row,
            0,
            parent_line,
        )

        # return QModelIndex()

    def data(
        self,
        index: QModelIndex,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        if not index.isValid():
            return None

        if role != Qt.ItemDataRole.DisplayRole:
            return None

        obj = index.internalPointer()

        if role == Qt.ItemDataRole.DisplayRole and isinstance(obj, CANLogLine):
            if index.column() == self.COL_TREND:
                return ""

            if index.column() == self.COL_LOG_MESSAGES:
                return obj.message_line

        if role == Qt.ItemDataRole.DisplayRole and isinstance(
            obj,
            DecodedSignalLine,
        ):
            if index.column() == self.COL_LOG_MESSAGES:
                return obj.signal_line
        
        return None

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
    
class MonitorLogViewPanel(QWidget):
    def __init__(
        self,
        vm: RecordViewModel,
        parent: QWidget = None,
    ):
        super().__init__(parent)
        self.vm = vm
        self._build_ui()


    # -------------------------------------------------
    # UI
    # -------------------------------------------------
    def _build_ui(self):
        main = QVBoxLayout(self)
        main.setContentsMargins(6, 2, 6, 6)
        main.setSpacing(4)

        # ---------- controls row (Start/Stop) ----------
        ctrl_row = QWidget(self)
        ctrl_layout = QHBoxLayout(ctrl_row)
        ctrl_layout.setContentsMargins(0, 0, 0, 0)
        ctrl_layout.setSpacing(6)

        self.btn_start_stop = QPushButton()
        self.btn_start_stop.setCheckable(True)
        self.btn_start_stop.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        ctrl_layout.addWidget(self.btn_start_stop, 1)

        main.addWidget(ctrl_row)

        # ---------- tree ----------
        self.view = QTreeView(self)

        self.view.setStyleSheet(
            """
            QTreeView::item:hover {
                background: rgba(255, 255, 255, 12);
            }
            """
        )
        
        self.model_ = (
            TreeLogLazyLoadModel(
                self.vm,
                self,
            )
        )

        self.view.setModel(
            self.model_
        )
        main.addWidget(self.view, 1)








        # self.cmb_mode = QComboBox()
        # self.cmb_mode.addItems(["Full mode", "Compact mode"])
        # self.cmb_mode.setCurrentIndex(0)  # default full

        # # ---------- toolbox container (header + tools) ----------
        # self.toolbox_container = QFrame(self)
        # self.toolbox_container.setContentsMargins(0, 0, 0, 0)
        # self.toolbox_container.setFrameStyle(QFrame.StyledPanel | QFrame.Plain)
        # self.toolbox_container.setStyleSheet(
        #     "QFrame { border: 1px solid #444; border-radius: 3px; }"
        # )

        # toolbox_container_layout = QVBoxLayout(self.toolbox_container)
        # toolbox_container_layout.setContentsMargins(0, 0, 0, 0)
        # toolbox_container_layout.setSpacing(4)

        # header_row = QWidget(self.toolbox_container)
        # header_layout = QHBoxLayout(header_row)
        # header_layout.setContentsMargins(6, 4, 6, 4)
        # header_layout.setSpacing(6)

        # self.display_group = QWidget(self.toolbox_container)
        # display_layout = QHBoxLayout(self.display_group)
        # display_layout.setContentsMargins(0, 0, 0, 0)
        # display_layout.setSpacing(6)
        # self.lbl_display = QLabel("Display:")
        # display_layout.addWidget(self.lbl_display)
        # display_layout.addWidget(self.cmb_mode)

        # self.btn_toggle_toolbox = QToolButton(self.toolbox_container)
        # self.btn_toggle_toolbox.setCheckable(True)
        # self.btn_toggle_toolbox.setChecked(True)
        # self.btn_toggle_toolbox.setArrowType(Qt.DownArrow)
        # self.btn_toggle_toolbox.setToolTip("Show / hide tools")

        # header_layout.addWidget(self.display_group)
        # header_layout.addStretch(1)
        # header_layout.addWidget(self.btn_toggle_toolbox)
        # toolbox_container_layout.addWidget(header_row)

        # # ---------- toolbox row (only when STOP) ----------
        # self.toolbox_tools = QFrame(self.toolbox_container)
        # self.toolbox_tools.setContentsMargins(0, 0, 0, 0)

        # toolbox_layout = QHBoxLayout(self.toolbox_tools)
        # toolbox_layout.setContentsMargins(6, 4, 6, 4)
        # toolbox_layout.setSpacing(4)

        # style = QApplication.style()

        # def themed_icon(theme_name: str, fallback_sp: QStyle.StandardPixmap) -> QIcon:
        #     # "Google icon" try: on many Linux desktops, Material icons may exist in theme.
        #     # Fallback: Qt standard icon (always works).
        #     icon = QIcon.fromTheme(theme_name)
        #     if icon.isNull():
        #         icon = style.standardIcon(fallback_sp)
        #     return icon

        # # Google-ish theme names (Material / freedesktop). Fallback to Qt SP_*
        # icon_refresh = themed_icon("view-refresh", QStyle.SP_BrowserReload)
        # icon_edit    = themed_icon("document-edit", QStyle.SP_FileDialogDetailedView)
        # icon_clear   = themed_icon("edit-clear", QStyle.SP_DialogResetButton)
        # icon_save    = themed_icon("document-save", QStyle.SP_DialogSaveButton)

        # self.btn_refresh = QPushButton(icon_refresh, "Reset")
        # self.btn_edit    = QPushButton(icon_edit,    "Edit")
        # self.btn_clear   = QPushButton(icon_clear,   "Clear")
        # self.btn_save    = QPushButton(icon_save,    "Save")

        # toolbox_layout.addWidget(self.btn_refresh)
        # toolbox_layout.addWidget(self.btn_edit)
        # toolbox_layout.addWidget(self.btn_clear)
        # toolbox_layout.addWidget(self.btn_save)
        # toolbox_layout.addStretch(1)

        # toolbox_container_layout.addWidget(self.toolbox_tools)

        # self.header_label = QLabel("Monitor (Stopped)")
        # self.header_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        # main.addWidget(self.header_label)
        # main.addWidget(self.toolbox_container)