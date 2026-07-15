from enum import Enum, auto
import warnings
from PySide6.QtCore import Qt, QModelIndex, QAbstractItemModel, QItemSelectionModel, QEvent, QPersistentModelIndex, QTimer, Signal
from PySide6.QtWidgets import (
    QAbstractItemView, QTreeView, QHeaderView, QVBoxLayout, QWidget,
    QStyledItemDelegate, QLineEdit, QComboBox, QStyle, QStyleOptionViewItem, QToolTip,
)
from canapp.data_object import CANLogLine
from typing import List, Dict, Optional
from lw.logger_setup import setup_logger, LOG
from PySide6.QtGui import QFont, QColor, QPalette, QCursor
from can_sdk.test_ultility import TEST_generated_CANLogLine_batch
# from canapp.global_event import event_on_signal_select, SignalFilter
from canapp.widgets.ParseableEditBox import TimeEditBox, RawBytesEditBox
from canapp.widgets.DLCSpinbox import DLCSpinBox
from canapp.widgets.DlcRawBinder import DlcRawBinder

#TEST
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTreeView

class _TreeLogMessageDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._dlc_raw_binder = DlcRawBinder()
        self._edit_red_paint_enabled = True
        self._row_height: Optional[int] = None
        self._hovered_index: QModelIndex = QModelIndex()
        self._hover_edit_bg = QColor(255, 255, 255, 26)
        self._hover_row_bg = QColor(255, 255, 255, 12)

    def set_hovered_index(self, index: QModelIndex) -> tuple[QModelIndex, QModelIndex]:
        old = self._hovered_index
        new = index if (index is not None and index.isValid()) else QModelIndex()
        if self._is_same_cell(old, new):
            return old, new
        self._hovered_index = new
        return old, new

    def clear_hover(self) -> QModelIndex:
        old = self._hovered_index
        self._hovered_index = QModelIndex()
        return old

    def _is_same_cell(self, a: QModelIndex, b: QModelIndex) -> bool:
        return (
            a.isValid() and b.isValid()
            and a.row() == b.row()
            and a.column() == b.column()
            and a.parent() == b.parent()
        )

    def _is_same_row(self, a: QModelIndex, b: QModelIndex) -> bool:
        return (
            a.isValid() and b.isValid()
            and a.row() == b.row()
            and a.parent() == b.parent()
        )

    def set_row_height(self, height: Optional[int]):
        self._row_height = None if height is None else max(1, int(height))

    def sizeHint(self, option, index):
        size = super().sizeHint(option, index)
        if self._row_height is not None:
            size.setHeight(self._row_height)
        return size

    def set_edit_red_paint_enabled(self, enabled: bool):
        self._edit_red_paint_enabled = bool(enabled)

    def createEditor(self, parent, option, index):
        if not index.isValid():
            return None

        model = index.model()
        if not bool(getattr(model, "_editable_mode", False)):
            return None
        node: _MessageNode = index.internalPointer()
        if node is None:
            return None

        col = index.column()
        if node.type != Type.MESSAGE:
            return None

        if col == model.COL_STR_DIFF:
            return TimeEditBox(parent)
        if col == model.COL_DIRECTION:
            editor = QComboBox(parent)
            editor.addItems(["Rx", "Tx"])
            return editor
        if col == model.COL_DATA_LEN:
            editor = DLCSpinBox(parent)
            self._dlc_raw_binder.bind_dlc_editor(editor, index)
            return editor
        if col == model.COL_RAW_DATA_BYTES:
            editor = RawBytesEditBox(parent)
            self._dlc_raw_binder.bind_raw_editor(editor, index)
            return editor
        return None

    def paint(self, painter, option, index):
        if not index.isValid():
            super().paint(painter, option, index)
            return

        model = index.model()
        node: _MessageNode = index.internalPointer()
        is_editable_hover = (
            bool(getattr(model, "_editable_mode", False))
            and bool(model.flags(index) & Qt.ItemIsEditable)
            and self._is_same_cell(index, self._hovered_index)
        )

        base_option = QStyleOptionViewItem(option)
        if is_editable_hover:
            base_option.state &= ~QStyle.State_MouseOver

        if not self._edit_red_paint_enabled:
            super().paint(painter, base_option, index)
            if is_editable_hover:
                painter.save()
                painter.fillRect(option.rect, self._hover_edit_bg)
                painter.restore()
            return

        if (
            node is None
            or not getattr(model, "_editable_mode", False)
            or node.type != Type.MESSAGE
            or index.column() != model.COL_RAW_DATA_BYTES
            or not hasattr(model, "get_initial_edit_value")
        ):
            super().paint(painter, base_option, index)
            if is_editable_hover:
                painter.save()
                painter.fillRect(option.rect, self._hover_edit_bg)
                painter.restore()
            return

        initial_text = model.get_initial_edit_value(node, index.column())
        current_text = str(model.data(index, Qt.DisplayRole) or "")
        if initial_text is None or current_text == initial_text:
            super().paint(painter, base_option, index)
            if is_editable_hover:
                painter.save()
                painter.fillRect(option.rect, self._hover_edit_bg)
                painter.restore()
            return

        opt = QStyleOptionViewItem(base_option)
        style = opt.widget.style() if opt.widget else None
        if style is None:
            super().paint(painter, base_option, index)
            if is_editable_hover:
                painter.save()
                painter.fillRect(option.rect, self._hover_edit_bg)
                painter.restore()
            return

        text_rect = style.subElementRect(QStyle.SE_ItemViewItemText, opt, opt.widget)
        style.drawControl(QStyle.CE_ItemViewItem, opt, painter, opt.widget)

        diff_mask = [
            (i >= len(initial_text)) or (current_text[i] != initial_text[i])
            for i in range(len(current_text))
        ]

        painter.save()
        fm = painter.fontMetrics()
        x = text_rect.x() + 2
        y = text_rect.y() + (text_rect.height() + fm.ascent() - fm.descent()) // 2
        normal_color = opt.palette.color(QPalette.HighlightedText if opt.state & QStyle.State_Selected else QPalette.Text)
        changed_color = QColor("#FF0000")

        for i, ch in enumerate(current_text):
            painter.setPen(changed_color if diff_mask[i] else normal_color)
            painter.drawText(x, y, ch)
            x += fm.horizontalAdvance(ch)
            if x > text_rect.right():
                break
        painter.restore()

        if is_editable_hover:
            painter.save()
            painter.fillRect(option.rect, self._hover_edit_bg)
            painter.restore()

    def setEditorData(self, editor, index):
        node: _MessageNode = index.internalPointer()
        model = index.model()
        if hasattr(model, "capture_initial_edit_value"):
            model.capture_initial_edit_value(index)

        value = index.model().data(index, Qt.DisplayRole)
        if isinstance(editor, TimeEditBox):
            editor.setText(str(value or "0ms"))
            return
        if isinstance(editor, QComboBox):
            txt = str(value or "Rx")
            idx = editor.findText(txt)
            editor.setCurrentIndex(idx if idx >= 0 else 0)
            return
        if isinstance(editor, QLineEdit):
            editor.setText(str(value or ""))
            return
        if isinstance(editor, DLCSpinBox):
            try:
                editor.set_dlc_value(int(value))
            except Exception:
                editor.set_dlc_value(0)
            return
        if isinstance(editor, RawBytesEditBox):
            editor.setText(str(value or ""))
            node: _MessageNode = index.internalPointer()
            if node is not None and node.type == Type.MESSAGE:
                try:
                    dlc_value = int(getattr(node.payload, "data_len", 0))
                except Exception:
                    dlc_value = 0
                self._dlc_raw_binder.normalize_raw_editor_for_row(editor, dlc_value)
            return
        super().setEditorData(editor, index)

    def setModelData(self, editor, model, index):
        if isinstance(editor, TimeEditBox):
            editor._commit()
            model.setData(index, editor.text(), Qt.EditRole)
            return
        if isinstance(editor, QComboBox):
            model.setData(index, editor.currentText(), Qt.EditRole)
            return
        if isinstance(editor, QLineEdit):
            model.setData(index, editor.text(), Qt.EditRole)
            return
        if isinstance(editor, DLCSpinBox):
            model.setData(index, editor.current_dlc_value(), Qt.EditRole)
            return
        if isinstance(editor, RawBytesEditBox):
            model.setData(index, editor.text(), Qt.EditRole)
            return
        super().setModelData(editor, model, index)


class Type(Enum):
    MESSAGE = auto()

class _MessageNode:
    __slots__ = ("parent", "children", "type", "payload", "trend", "text", "tag", "row", "edited_cols", "initial_edit_values")

    def __init__(self, parent: Optional["_MessageNode"], type: Optional[Type], payload):
        self.parent = parent
        self.children: list[_MessageNode] = []
        self.type = type
        self.payload = payload
        self.trend = ""
        self.text = ""
        self.tag = "normal"
        self.row = -1
        self.edited_cols: set[int] = set()
        self.initial_edit_values: dict[int, str] = {}

class TreeLogMessageModel(QAbstractItemModel):
    TAG_FG = {
    "normal": QColor("#FFFFFF"),
    "change": QColor("#FFFFFF"),
    }
    COL_TREND = 0
    COL_LOG_MESSAGES = 1
    NODE_TYPE = _MessageNode

    COL_STR_TIMESTAMP = 0
    COL_STR_DIFF = 1
    COL_DIRECTION = 2
    COL_CAN_ID_STR = 3
    COL_DATA_LEN = 4
    COL_RAW_DATA_BYTES = 5

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data: list[CANLogLine] = []
        self._root = self.NODE_TYPE(None, None, None)
        self._message_nodes: Dict[int, _MessageNode] = {}
        self._header_overrides: Dict[int, str] = {}
        self._editable_mode = False
        self._allow_edit_raw_data = False
        self._last_edited_index = QPersistentModelIndex()
        self._columns = 2

    def _total_rows(self) -> int:
        return len(self._data)

    """ 20K -> ~ 100 ms without format_line_log, 3s with it"""
    def _build_message_node(self, row: int, entry: CANLogLine) -> NODE_TYPE:
        # LOG.debug("_build_message_node")
        node = self.NODE_TYPE(self._root, Type.MESSAGE, entry)
        node.row = int(row)
        changed = entry.changed
        node.trend = "●" if changed else "○"
        #node.text = entry.format_line_log()
        node.tag = "change" if changed else "normal"
        return node

    def set_data(self, data: List[CANLogLine]):
        self.beginResetModel()
        src = data if data is not None else []
        self._data = [entry for entry in src if entry is not None]
        self._root.children.clear()
        self._message_nodes.clear()
        self._last_edited_index = QPersistentModelIndex()
        for row, entry in enumerate(self._data):
            self._message_nodes[row] = self._build_message_node(row, entry)
        self.endResetModel()

    def columnCount(self, parent=QModelIndex()):
        return self._columns

    def rowCount(self, parent=QModelIndex()):
        if not parent.isValid():
            return self._total_rows()
        return 0

    def hasChildren(self, parent=QModelIndex()):
        if not parent.isValid():
            return self._total_rows() > 0
        return False

    def index(self, row, column, parent=QModelIndex()):
        if parent.isValid():
            return QModelIndex()
        if row < 0 or row >= self._total_rows() or column < 0 or column >= self._columns:
            return QModelIndex()
        node = self._message_nodes.get(row)
        if node is None:
            return QModelIndex()
        return self.createIndex(row, column, node)

    def parent(self, index):
        return QModelIndex()

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        node: _MessageNode = index.internalPointer()
        if not isinstance(node, _MessageNode) or node.payload is None:
            return "" if role == Qt.DisplayRole else None

        if role == Qt.ForegroundRole:
            if self._editable_mode and index.column() in node.edited_cols:
                if index.column() == self.COL_RAW_DATA_BYTES:
                    return self.TAG_FG["normal"]
                return QColor("#FF0000")
            return self.TAG_FG.get(node.tag, self.TAG_FG["normal"])

        if role not in (Qt.DisplayRole, Qt.EditRole):
            return None

        if self._editable_mode:
            entry: CANLogLine = node.payload
            col = index.column()
            if col == self.COL_STR_TIMESTAMP:
                return str(entry.timestamp)
            if col == self.COL_STR_DIFF:
                return entry.get_format_timediff()
            if col == self.COL_DIRECTION:
                return str(entry.direction)
            if col == self.COL_CAN_ID_STR:
                return f"{entry.can_id:X}"
            if col == self.COL_DATA_LEN:
                return int(entry.data_len)
            if col == self.COL_RAW_DATA_BYTES:
                return str(entry.raw_data)
            return ""

        if index.column() == self.COL_TREND:
            return node.trend
        if index.column() == self.COL_LOG_MESSAGES:
            """ cache """
            if not node.text:
                node.text = node.payload.format_line_log()
            return node.text
        return None

    def flags(self, index):
        if not index.isValid():
            return Qt.NoItemFlags
        flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        if not self._editable_mode:
            return flags

        """ Editable fields"""
        col = index.column()
        if col in (self.COL_DIRECTION, self.COL_DATA_LEN, self.COL_RAW_DATA_BYTES):
            flags |= Qt.ItemIsEditable
        return flags

    def headerData(self, section, orientation, role):
        if role != Qt.DisplayRole or orientation != Qt.Horizontal:
            return None
        if self._editable_mode:
            headers = ["Timestamp", "Diff", "Direction", "CAN ID", "DLC", "Data"]
        else:
            headers = ["#", "Log Messages"]
        if 0 <= section < len(headers):
            return self._header_overrides.get(section, headers[section])
        return None

    def set_header_text(self, section: int, text: Optional[str]):
        if section < 0 or section >= self._columns:
            return
        if text is None:
            self._header_overrides.pop(section, None)
        else:
            self._header_overrides[section] = str(text)
        self.headerDataChanged.emit(Qt.Horizontal, section, section)

    def set_header_texts(self, mapping: Dict[int, str]):
        if not mapping:
            return
        for section, text in mapping.items():
            if section < 0 or section >= self._columns:
                continue
            self._header_overrides[int(section)] = str(text)
        self.headerDataChanged.emit(Qt.Horizontal, 0, max(0, self._columns - 1))

    def set_editable_mode(self, enabled: bool):
        enabled = bool(enabled)
        if enabled == self._editable_mode:
            return

        old_columns = self._columns
        self._editable_mode = enabled
        self._columns = 6 if self._editable_mode else 2
        if self._editable_mode:
            self.begin_edit_session()
        #self._reset_edit_tracking()

        self.headerDataChanged.emit(Qt.Horizontal, 0, max(old_columns, self._columns) - 1)
        total = self._total_rows()
        if total > 0:
            top_left = self.index(0, 0, QModelIndex())
            bottom_right = self.index(total - 1, self._columns - 1, QModelIndex())
            if top_left.isValid() and bottom_right.isValid():
                self.dataChanged.emit(top_left, bottom_right, [Qt.DisplayRole, Qt.ForegroundRole])
        self.layoutChanged.emit()

    def set_allow_edit_raw_data(self, allow: bool):
        allow = bool(allow)
        if allow == self._allow_edit_raw_data:
            return
        self._allow_edit_raw_data = allow
        total = self._total_rows()
        if total <= 0:
            return
        top_left = self.index(0, self.COL_RAW_DATA_BYTES, QModelIndex())
        bottom_right = self.index(total - 1, self.COL_RAW_DATA_BYTES, QModelIndex())
        if top_left.isValid() and bottom_right.isValid():
            self.dataChanged.emit(top_left, bottom_right, [Qt.DisplayRole, Qt.EditRole, Qt.ForegroundRole])

    def is_allow_edit_raw_data(self) -> bool:
        return bool(self._allow_edit_raw_data)

    def capture_initial_edit_value(self, index: QModelIndex):
        LOG.debug("capture_initial_edit_value")
        if not index.isValid():
            return
        node = index.internalPointer()
        if not isinstance(node, _MessageNode):
            return
        col = int(index.column())
        if col not in node.initial_edit_values:
            node.initial_edit_values[col] = str(self.data(index, Qt.DisplayRole) or "")

    def get_initial_edit_value(self, node: _MessageNode, col: int) -> Optional[str]:
        #LOG.debug("get_initial_edit_value")
        if not isinstance(node, _MessageNode):
            return None
        return node.initial_edit_values.get(int(col))

    def begin_edit_session(self):
        for node in self._message_nodes.values():
            node.edited_cols.clear()
            node.initial_edit_values.clear()
        self._last_edited_index = QPersistentModelIndex()

    def _normalized_edit_value(self, col: int, text: Optional[str]) -> str:
        value = str(text or "")

        if col == self.COL_STR_DIFF:
            try:
                parser = TimeEditBox()
                seconds = float(parser.parse_timediff(value))
                return f"{seconds:.12g}"
            except Exception:
                return value.strip()

        if col == self.COL_DIRECTION:
            lower = value.strip().lower()
            if lower == "rx":
                return "Rx"
            if lower == "tx":
                return "Tx"
            return value.strip()

        if col == self.COL_DATA_LEN:
            try:
                return str(int(value))
            except Exception:
                return value.strip()

        if col == self.COL_RAW_DATA_BYTES:
            parser = RawBytesEditBox()
            parsed = parser._parse_raw_bytes(value)
            if parsed is None:
                return " ".join(value.strip().upper().split())
            return " ".join(f"{b:02X}" for b in parsed)

        return value

    def setData(self, index, value, role=Qt.EditRole):
        if role != Qt.EditRole or not index.isValid() or not self._editable_mode:
            return False

        node = index.internalPointer()
        if not isinstance(node, _MessageNode) or node.type != Type.MESSAGE:
            return False

        self.capture_initial_edit_value(index)

        col = index.column()
        entry: CANLogLine = node.payload

        try:
            if col == self.COL_STR_DIFF:
                new_text = str(value).strip()
                parser = TimeEditBox()
                new_seconds = float(parser.parse_timediff(new_text))
                if abs(float(entry.timediff) - new_seconds) < 1e-12:
                    return False
                entry.timediff = new_seconds
            elif col == self.COL_DIRECTION:
                direction = str(value).strip()
                if direction not in ("Rx", "Tx") or direction == str(entry.direction):
                    return False
                entry.direction = direction
            elif col == self.COL_DATA_LEN:
                new_dlc = int(value)
                if new_dlc < 0:
                    new_dlc = 0
                elif new_dlc > 15:
                    new_dlc = 15
                if int(entry.data_len) == new_dlc:
                    return False
                entry.data_len = new_dlc
            elif col == self.COL_RAW_DATA_BYTES:
                text = str(value).strip()
                parser = RawBytesEditBox()
                parsed = parser._parse_raw_bytes(text)
                if parsed is None:
                    return False
                new_raw = " ".join(f"{b:02X}" for b in parsed)
                if new_raw.upper() == str(entry.raw_data).upper():
                    return False
                entry.raw_data = new_raw
            else:
                return False
        except Exception:
            return False

        initial = self.get_initial_edit_value(node, col)
        current = str(self.data(index, Qt.DisplayRole) or "")
        if (
            initial is not None
            and self._normalized_edit_value(col, current) == self._normalized_edit_value(col, initial)
        ):
            node.edited_cols.discard(col)
        else:
            node.edited_cols.add(col)

        node.text = ""
        self._last_edited_index = QPersistentModelIndex(index)
        self.dataChanged.emit(index, index, [Qt.DisplayRole, Qt.EditRole, Qt.ForegroundRole])
        return True

    def revert_index_edit(self, index: QModelIndex) -> bool:
        if not index.isValid():
            return False
        node = index.internalPointer()
        if not isinstance(node, _MessageNode):
            return False
        initial = self.get_initial_edit_value(node, index.column())
        if initial is None:
            return False
        return self.setData(index, initial, Qt.EditRole)

    def has_row_edits(self, index: QModelIndex) -> bool:
        if not index.isValid():
            return False
        node = index.internalPointer()
        if not isinstance(node, _MessageNode):
            return False
        return bool(node.edited_cols)

    def revert_row_edits(self, index: QModelIndex) -> bool:
        if not index.isValid():
            return False
        node = index.internalPointer()
        if not isinstance(node, _MessageNode):
            return False

        columns = sorted(int(col) for col in node.edited_cols)
        if not columns:
            return False

        any_success = False
        for col in columns:
            cell_index = index.siblingAtColumn(col)
            if not cell_index.isValid():
                continue
            if self.revert_index_edit(cell_index):
                any_success = True

        return any_success

    def clear(self):
        self.beginResetModel()
        self._data = []
        self._root.children.clear()
        self._message_nodes.clear()
        self._last_edited_index = QPersistentModelIndex()
        self.endResetModel()

class TreeLogSelectionModel(QItemSelectionModel):
    NODE_TYPE = _MessageNode
    def __init__(self, model: QAbstractItemModel, parent=None):
        super().__init__(model, parent)
        self.currentChanged.connect(self._on_current_changed)

    def _on_current_changed(self, current: QModelIndex, previous: QModelIndex):
        if not current.isValid():
            return
        if current == previous:
            return
        #selection_sig = self._create_data_for_selection(current)
        #event_on_signal_select.notify(selection_sig)

    # def _create_data_for_selection(self, current: QModelIndex) -> SignalFilter:
    #     item = current.internalPointer()
    #     selection_sig = SignalFilter()
    #     if item.type == Type.MESSAGE:
    #         entry: CANLogLine = item.payload
    #         selection_sig.msg_info = entry.message_obj.msg_info if entry.message_obj else None
    #     return selection_sig

class TreeLogMessage(QWidget):
    undoAvailabilityChanged = Signal(bool)
    _HOVER_STYLESHEET = """
        QTreeView::item:hover {
            background: rgba(255, 255, 255, 5);
        }
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.view = QTreeView(self)
        self.view.setMouseTracking(False)
        self._editable_mode = False
        self.model_ = TreeLogMessageModel(self)
        self.view.setModel(self.model_)
        self.select_model = TreeLogSelectionModel(self.model_, self.view)
        self.view.setSelectionModel(self.select_model)
        self._edit_delegate = _TreeLogMessageDelegate(self.view)
        self._undo_available = False
        self._hover_tooltip_timer = QTimer(self)
        self._hover_tooltip_timer.setSingleShot(True)
        self._hover_tooltip_timer.timeout.connect(self._show_edit_tooltip)
        self._hover_tooltip_index = QPersistentModelIndex()
        self._hover_expanded_parent = QPersistentModelIndex()

        # FONT
        mono = QFont("Consolas", 10)
        mono.setStyleHint(QFont.Monospace)
        self.view.setFont(mono)

        # HEADER
        header = self.view.header()
        self.view.setColumnWidth(0, 80)
        self.view.header().setStretchLastSection(False)
        header.setSectionResizeMode(QHeaderView.Interactive)
        self.view.setColumnWidth(1, 1600)
        header.setFixedHeight(20)
        font = header.font()
        font.setPointSize(font.pointSize())   # or setPointSize(11 / 12)
        # font.setBold(True)
        header.setFont(font)

        self.view.setSelectionMode(QTreeView.ExtendedSelection)
        self.view.viewport().setMouseTracking(True)
        self.view.setUniformRowHeights(True)   # good for performance
        self.view.setAnimated(False)
        self.view.setAutoScroll(True)
        self._apply_mode_config()
        self.view.entered.connect(self._on_item_hovered)
        self.view.viewport().installEventFilter(self)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.view)
        self._bind_undo_state_tracking()
        self._emit_undo_availability(force=True)

    def _bind_undo_state_tracking(self):
        def _safe_disconnect(signal_obj, slot):
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)
                try:
                    signal_obj.disconnect(slot)
                except Exception:
                    pass

        if self.select_model is not None:
            _safe_disconnect(self.select_model.currentChanged, self._on_selection_changed_for_undo)
            self.select_model.currentChanged.connect(self._on_selection_changed_for_undo)

        if self.model_ is not None:
            _safe_disconnect(self.model_.dataChanged, self._on_model_changed_for_undo)
            _safe_disconnect(self.model_.modelReset, self._on_model_changed_for_undo)
            _safe_disconnect(self.model_.layoutChanged, self._on_model_changed_for_undo)

            self.model_.dataChanged.connect(self._on_model_changed_for_undo)
            self.model_.modelReset.connect(self._on_model_changed_for_undo)
            self.model_.layoutChanged.connect(self._on_model_changed_for_undo)

    def _on_selection_changed_for_undo(self, *_):
        self._emit_undo_availability()

    def _on_model_changed_for_undo(self, *_):
        self._emit_undo_availability()

    def _emit_undo_availability(self, force: bool = False):
        available = self.is_current_row_undo_available()
        if force or available != self._undo_available:
            self._undo_available = available
            self.undoAvailabilityChanged.emit(available)

    def is_current_row_undo_available(self) -> bool:
        if not self._editable_mode:
            return False
        index = self.view.currentIndex()
        if not index.isValid():
            return False
        model = self.model_
        if hasattr(model, "has_row_edits"):
            try:
                return bool(model.has_row_edits(index))
            except Exception:
                return False
        return False

    def _on_item_hovered(self, index: QModelIndex):
        if self._edit_delegate is None:
            return
        editable_index = index if (index.isValid() and bool(self.model_.flags(index) & Qt.ItemIsEditable)) else QModelIndex()
        old_idx, new_idx = self._edit_delegate.set_hovered_index(editable_index)

        if editable_index.isValid():
            persistent = QPersistentModelIndex(editable_index)
            if self._hover_tooltip_index != persistent:
                self._hover_tooltip_index = persistent
                self._hover_tooltip_timer.start(1600)
        else:
            self._hover_tooltip_timer.stop()
            self._hover_tooltip_index = QPersistentModelIndex()
            QToolTip.hideText()
            self._collapse_hover_expanded_row()

        if editable_index.isValid() and self._hover_expanded_parent.isValid():
            parent_index = editable_index.siblingAtColumn(0)
            current_parent = QModelIndex(self._hover_expanded_parent)
            if (
                not current_parent.isValid()
                or current_parent.row() != parent_index.row()
                or current_parent.parent() != parent_index.parent()
            ):
                self._collapse_hover_expanded_row()

        if old_idx.isValid():
            self.view.viewport().update(self.view.visualRect(old_idx))
        if new_idx.isValid():
            self.view.viewport().update(self.view.visualRect(new_idx))

    def _show_edit_tooltip(self):
        index = QModelIndex(self._hover_tooltip_index)
        if not index.isValid():
            return
        if not bool(self.model_.flags(index) & Qt.ItemIsEditable):
            return

        rect = self.view.visualRect(index)
        if not rect.isValid() or rect.isEmpty():
            return

        cursor_local = self.view.viewport().mapFromGlobal(QCursor.pos())
        if not rect.contains(cursor_local):
            return

        QToolTip.showText(QCursor.pos(), "Double click to edit", self.view.viewport(), rect)
        self._expand_hover_row(index)

    def _expand_hover_row(self, index: QModelIndex):
        if not index.isValid():
            return
        parent_index = index.siblingAtColumn(0)
        if not parent_index.isValid():
            return
        if not self.model_.hasChildren(parent_index):
            return

        current_parent = QModelIndex(self._hover_expanded_parent)
        if (
            current_parent.isValid()
            and (current_parent.row() != parent_index.row() or current_parent.parent() != parent_index.parent())
        ):
            self.view.setExpanded(current_parent, False)

        self.view.setExpanded(parent_index, True)
        self._hover_expanded_parent = QPersistentModelIndex(parent_index)

    def _collapse_hover_expanded_row(self):
        current_parent = QModelIndex(self._hover_expanded_parent)
        if current_parent.isValid():
            self.view.setExpanded(current_parent, False)
        self._hover_expanded_parent = QPersistentModelIndex()

    def eventFilter(self, obj, event):
        if obj is self.view.viewport() and event.type() == QEvent.Leave:
            if self._edit_delegate is not None:
                old_idx = self._edit_delegate.clear_hover()
                if old_idx.isValid():
                    self.view.viewport().update(self.view.visualRect(old_idx))
            self._hover_tooltip_timer.stop()
            self._hover_tooltip_index = QPersistentModelIndex()
            QToolTip.hideText()
            self._collapse_hover_expanded_row()
        return super().eventFilter(obj, event)
    
    def _apply_mode_config(self):
        if self._editable_mode:
            self.model_.set_allow_edit_raw_data(True)
            self.view.setEditTriggers(
                QAbstractItemView.DoubleClicked
                | QAbstractItemView.EditKeyPressed
                | QAbstractItemView.SelectedClicked
            )
            self.view.setItemDelegate(self._edit_delegate)
            self.view.setStyleSheet("")
            self.view.setColumnWidth(0, 110)
            self.view.setColumnWidth(1, 90)
            self.view.setColumnWidth(2, 90)
            self.view.setColumnWidth(3, 90)
            self.view.setColumnWidth(4, 70)
            self.view.setColumnWidth(5, 1120)
        else:
            self.model_.set_editable_mode(False)
            self.model_.set_allow_edit_raw_data(False)
            self.view.setEditTriggers(QAbstractItemView.NoEditTriggers)
            self.view.setColumnWidth(0, 80)
            self.view.setColumnWidth(1, 1600)
            if self._edit_delegate is not None:
                old_idx = self._edit_delegate.clear_hover()
                if old_idx.isValid():
                    self.view.viewport().update(self.view.visualRect(old_idx))
            self.view.setStyleSheet(self._HOVER_STYLESHEET)

    def set_editable_mode(self, enabled: bool):
        self._editable_mode = bool(enabled)
        self._apply_mode_config()
        self._emit_undo_availability(force=True)

    def toggle_edit_mode(self) -> bool:
        self.set_editable_mode(not self._editable_mode)
        return self._editable_mode

    def undo_current_edit(self) -> bool:
        index = self.view.currentIndex()
        model = self.model_

        if not index.isValid():
            return False
        if not hasattr(model, "revert_row_edits"):
            return False

        try:
            ok = bool(model.revert_row_edits(index))
        except Exception:
            ok = False

        self._emit_undo_availability()
        return ok

    def set_data(self, data: List[CANLogLine]):
        self.model_.set_data(data)
        self.view.verticalScrollBar().setValue(self.view.verticalScrollBar().minimum())
        self.view.horizontalScrollBar().setValue(self.view.horizontalScrollBar().minimum())
        self._emit_undo_availability(force=True)

if __name__ == "__main__":
    import sys
    import time
    from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton
    setup_logger(env="DEV", backup_count=30)
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    parsed_lines = TEST_generated_CANLogLine_batch(10000)
    
    win = QWidget()
    win.setWindowTitle("TreeLogView Test")
    layout = QVBoxLayout(win)
    tree = TreeLogMessage()
    layout.addWidget(tree)

    load_btn = QPushButton("Load Parsed Lines")

    def on_load_click():
        start = time.perf_counter()
        tree.set_data(parsed_lines)
        t1 = time.perf_counter()
        app.processEvents()          # force Qt to do the layout/paint NOW
        t2 = time.perf_counter()
        print(f"set_data: {t1 - start:.4f}s | render: {t2 - t1:.4f}s | total: {t2 - start:.4f}s")

    load_btn.clicked.connect(on_load_click)
    layout.addWidget(load_btn)

    mode_btn = QPushButton("Mode: Read")

    def on_toggle_mode():
        is_edit = tree.toggle_edit_mode()
        mode_btn.setText("Mode: Edit" if is_edit else "Mode: Read")

    mode_btn.clicked.connect(on_toggle_mode)
    layout.addWidget(mode_btn)

    undo_btn = QPushButton("Undo Current Edit")
    undo_btn.setEnabled(tree.is_current_row_undo_available())

    def on_undo_current_edit():
        ok = tree.undo_current_edit()
        print(f"undo_current_edit: {ok}")

    tree.undoAvailabilityChanged.connect(undo_btn.setEnabled)
    undo_btn.clicked.connect(on_undo_current_edit)
    layout.addWidget(undo_btn)

    win.resize(800, 500)
    win.show()

    sys.exit(app.exec())

""" Conclusion: The time for set all 20000 data ram into the tree and load costs 1 ~ 3 seconds deplay"""
""" set_data: 0.1084s | render: 2.5804s | total: 2.6887s """


