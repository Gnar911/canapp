from PySide6.QtCore import Qt, QAbstractItemModel, QModelIndex, QItemSelectionModel, QTimer, QEvent
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QFileDialog, QStyledItemDelegate, QLineEdit, QComboBox, QAbstractItemView, QStyle, QHeaderView
from can_sdk.data_object import CANLogLine, SignalFilter, Signal
from can_sdk.canlog_viewmodel import LogContextViewModel
from typing import List, Dict, Optional, Tuple, Any
from can_sdk.dbc_manager import CANDBManager
from can_sdk.parser_manager import CANLogManager
from lw.logger_setup import LOG, setup_logger
from PySide6.QtGui import QFont
from ui_sdk.components.pyqt.ultility import open_in_editor, open_in_excel
from enum import Enum, auto
from ui_sdk.components.pyqt.ParseableEditBox import TimeEditBox, RawBytesEditBox
from ui_sdk.components.pyqt.DLCSpinbox import DLCSpinBox
from ui_sdk.components.pyqt.SignalEditBox import SignalEditBox
from ui_sdk.components.pyqt.DlcRawBinder import DlcRawBinder

#TEST
from cansrv.file_service.parser import LogParser

TAG_FG = {
    "normal": QColor("#FFFFFF"),
    "change": QColor("#FFFFFF"),
    "signormal": QColor("#0000FF"),
    "sigchange": QColor("#FF0000"),
    # highlights (light backgrounds)
    "markselection11": (None, QColor("#FFCCCC")),
    "markselection22": (None, QColor("#C6EFCE")),
    "markselection33": (None, QColor("#FFCCFF")),
    "markselection44": (None, QColor("#CCCCFF")),
    "markselection55": (None, QColor("#E5CCFF")),
    "markselection66": (None, QColor("#CCF2FF")),
    "markselection77": (None, QColor("#FFD9B3")),
}

class Type(Enum):
    MESSAGE = auto()
    SIGNAL = auto()

class _Node:
    __slots__ = ("parent", "children", "type", "payload", "trend", "text", "tag", "highlight_tag", "edited_cols", "signals_loaded", "initial_edit_values")

    def __init__(self, parent: Optional["_Node"], type: Type, payload: Any):
        self.parent = parent
        self.children: list[_Node] = []
        self.type = type           # Type.MESSAGE or Type.SIGNAL
        self.payload = payload     # CANLogLine or Signal
        self.trend = ""            # "○" or "●" for message
        self.text = ""             # displayed line (col 1)
        self.tag = ""              # "normal/change/signormal/sigchange"
        self.highlight_tag = ""    # markselection.. (background highlight)
        self.edited_cols: set[int] = set()
        self.signals_loaded = False
        self.initial_edit_values: dict[int, str] = {}


class _TreeLogEditDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._dlc_raw_binder = DlcRawBinder()

    def createEditor(self, parent, option, index):
        if not index.isValid():
            return None

        model = index.model()
        node: _Node = index.internalPointer()
        if node is None:
            return None

        col = index.column()
        if node.type == Type.SIGNAL and col == model.COL_SIG_VALUE:
            editor = SignalEditBox(parent)
            editor.set_widget_height(option.rect.height())
            return editor

        if node.type != Type.MESSAGE:
            return None

        if col == model.COL_STR_DIFF:
            return TimeEditBox(parent)
        if col == model.COL_DIRECTION:
            editor = QComboBox(parent)
            editor.addItems(["Rx", "Tx"])
            return editor
        if col == model.COL_NAME:
            return QLineEdit(parent)
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
        node: _Node = index.internalPointer()
        if (
            node is None
            or not getattr(model, "_editable_mode", False)
            or node.type != Type.MESSAGE
            or index.column() != model.COL_RAW_DATA_BYTES
        ):
            super().paint(painter, option, index)
            return

        initial_text = model.get_initial_edit_value(node, index.column())
        current_text = str(model.data(index, Qt.DisplayRole) or "")
        if initial_text is None or current_text == initial_text:
            super().paint(painter, option, index)
            return

        opt = option
        style = opt.widget.style() if opt.widget else None
        if style is None:
            super().paint(painter, option, index)
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

    def setEditorData(self, editor, index):
        node: _Node = index.internalPointer()
        model = index.model()
        if hasattr(model, "capture_initial_edit_value"):
            model.capture_initial_edit_value(index)

        if isinstance(editor, SignalEditBox):
            sig: Signal = node.payload
            editor.set_signal(sig)
            editor._initial_raw = sig.get_raw_value()
            return

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
            node: _Node = index.internalPointer()
            if node is not None and node.type == Type.MESSAGE:
                try:
                    dlc_value = int(getattr(node.payload, "data_len", 0))
                except Exception:
                    dlc_value = 0
                self._dlc_raw_binder.normalize_raw_editor_for_row(editor, dlc_value)
            return
        super().setEditorData(editor, index)

    def setModelData(self, editor, model, index):
        if isinstance(editor, SignalEditBox):
            node: _Node = index.internalPointer()
            sig: Signal = node.payload
            old_raw = getattr(editor, "_initial_raw", sig.get_raw_value())
            new_raw = sig.get_raw_value()
            model.setData(index, {"old_raw": old_raw, "new_raw": new_raw}, Qt.EditRole)
            return

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

class TreeLogSelectionModel(QItemSelectionModel):
    def __init__(self, model: QAbstractItemModel, candb: CANDBManager, parent=None):
        super().__init__(model, parent)
        self.my_model = candb
        self.currentChanged.connect(self._on_current_changed)

    def _on_current_changed(self, current: QModelIndex, previous: QModelIndex):
        LOG.debug("_on_current_changed")
        if not current.isValid():
            return
        if current == previous:
            return
        item: _Node = current.internalPointer()  # message / signal object
        selection_sig = SignalFilter()
        if item.type == Type.MESSAGE:
            entry: CANLogLine = item.payload
            LOG.debug(f"Line number: {entry.line_number}")
            """ Must cover the case message_obj is None !!! That is when no DBC loaded """
            selection_sig.msg_info = entry.message_obj.msg_info if entry.message_obj else None
        if item.type == Type.SIGNAL:
            signal: Signal = item.payload
            selection_sig.signal_info = signal.sig_info
            selection_sig.rawvalue = signal.raw_value
        self.my_model.cur_sig = selection_sig

class TreeLogModel(QAbstractItemModel):
    COL_TREND = 0
    COL_LOG_MESSAGES = 1

    COL_STR_TIMESTAMP = 0
    COL_STR_DIFF = 1
    COL_DIRECTION = 2
    COL_CAN_ID_STR = 3
    COL_NAME = 4
    COL_DATA_LEN = 5
    COL_RAW_DATA_BYTES = 6
    COL_SIG_NAME = COL_NAME
    COL_SIG_UNIT = COL_DATA_LEN
    COL_SIG_VALUE = COL_RAW_DATA_BYTES

    def __init__(self, parent=None,  
                 model: CANDBManager = None,
                 editable_mode: bool = False):
        super().__init__(parent)
        self._root = _Node(None, "root", None)
        self.my_model = model
        self._data: list[CANLogLine] = []
        self._loaded = 0
        self.chunk_size = 300
        self._editable_mode = bool(editable_mode)
        self._columns = 7 if self._editable_mode else 2

    def set_editable_mode(self, enabled: bool):
        enabled = bool(enabled)
        if enabled == self._editable_mode:
            return

        old_columns = self._columns
        self._editable_mode = enabled
        self._columns = 7 if self._editable_mode else 2
        self._reset_edit_tracking()

        self.headerDataChanged.emit(Qt.Horizontal, 0, max(old_columns, self._columns) - 1)
        if self._root.children:
            top_left = self.index(0, 0, QModelIndex())
            bottom_right = self.index(len(self._root.children) - 1, self._columns - 1, QModelIndex())
            if top_left.isValid() and bottom_right.isValid():
                self.dataChanged.emit(top_left, bottom_right, [Qt.DisplayRole, Qt.ForegroundRole])
        self.layoutChanged.emit()

    def set_data(self, data: list[CANLogLine]):
        self.beginResetModel()
        self._data = data
        self._root.children.clear()
        
        # Create message nodes (no signal children yet; added on demand)
        for entry in self._data:
            msg_node = _Node(self._root, Type.MESSAGE, entry)
            msg_node.trend = "●" if entry.changed else "○"
            msg_node.tag = "normal"  # Messages always black; only signals show color
            self._root.children.append(msg_node)
        
        self._loaded = 0
        self.endResetModel()
        
        # Load initial chunk of messages
        if self._data:
            self.fetchMore(QModelIndex())

    def canFetchMore(self, parent=QModelIndex()):
        if parent.isValid():
            return False
        # Only root-level (messages) support chunking
        return self._loaded < len(self._root.children)

    def columnCount(self, parent=QModelIndex()):
        return self._columns
    
    def rowCount(self, parent=QModelIndex()):
        if not parent.isValid():
            # Root level: return full message count so scrollbar reflects full data
            return len(self._root.children)
        
        # Non-root: return children of the parent node
        node = parent.internalPointer()
        if node is None:
            return 0
        
        if node.type == Type.MESSAGE:
            # Message nodes have signal children
            return len(node.children)
        
        # Signal nodes have no children
        return 0

    def index(self, row, column, parent=QModelIndex()):
        if not parent.isValid():
            # Root level: messages
            if row < len(self._root.children):
                node = self._root.children[row]
                return self.createIndex(row, column, node)
            return QModelIndex()
        
        # Non-root: children of parent node
        parent_node = parent.internalPointer()
        if parent_node is None or row >= len(parent_node.children):
            return QModelIndex()
        
        child_node = parent_node.children[row]
        return self.createIndex(row, column, child_node)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        node: _Node = index.internalPointer()
        if node is None:
            return None

        # Keep full scrollbar range while hydrating rows in chunks.
        if node.type == Type.MESSAGE and index.row() >= self._loaded:
            self._load_until_row(index.row())
        
        # Handle ForegroundRole (text color)
        if role == Qt.ForegroundRole:
            if self._editable_mode:
                if index.column() in node.edited_cols:
                    if node.type == Type.MESSAGE and index.column() == self.COL_RAW_DATA_BYTES:
                        return TAG_FG["normal"]
                    return QColor("#FF0000")
                return TAG_FG["normal"]

            tag = node.tag if node.tag else ("change" if node.type == Type.MESSAGE and node.payload.changed else "normal")
            return TAG_FG.get(tag, QColor("#FFFFFF"))

        if role == Qt.BackgroundRole:
            if node.type == Type.SIGNAL:
                return QColor("#242424")
            return None

        if role == Qt.ToolTipRole and self._editable_mode:
            col = index.column()
            if node.type == Type.MESSAGE and col in (
                self.COL_STR_DIFF,
                self.COL_DIRECTION,
                self.COL_NAME,
                self.COL_DATA_LEN,
                self.COL_RAW_DATA_BYTES,
            ):
                return "Double click to edit"
            if node.type == Type.SIGNAL and col == self.COL_SIG_VALUE:
                return "Double click to edit"
            return None
        
        # Handle DisplayRole (text content)
        if role not in (Qt.DisplayRole, Qt.EditRole):
            return None

        if node.type == Type.MESSAGE:
            self._ensure_message_signals_loaded(node)
            node.signals_loaded = True

        if self._editable_mode:
            return self._editable_data(node, index.column())
        
        # Handle message nodes
        if node.type == Type.MESSAGE:
            entry: CANLogLine = node.payload
            
            if index.column() == 0:
                return node.trend
            
            if index.column() == 1:
                return entry.format_line_log(
                    self.my_model.candb.message_name_max_len if self.my_model.candb else 0
                )
        
        # Handle signal nodes
        elif node.type == Type.SIGNAL:
            sig: Signal = node.payload
            
            if index.column() == 0:
                return ""
            
            if index.column() == 1:
                return f"・{sig.get_format_signal_show()}"
        
        return None

    def _editable_data(self, node: _Node, column: int):
        if node.type == Type.SIGNAL:
            sig: Signal = node.payload
            if column == self.COL_SIG_NAME:
                return f"・{str(sig.signal_name or '')}"
            if column == self.COL_SIG_VALUE:
                return str(sig.value or "")
            if column == self.COL_SIG_UNIT:
                return str(sig.value_unit or "")
            return ""

        if node.type != Type.MESSAGE:
            return ""

        entry: CANLogLine = node.payload

        if column == self.COL_STR_TIMESTAMP:
            val = entry.timestamp
            return str(val)

        if column == self.COL_STR_DIFF:
            return str(entry.timediff)

        if column == self.COL_DIRECTION:
            return str(entry.direction)

        if column == self.COL_CAN_ID_STR:
            return f"{entry.can_id:X}"

        if column == self.COL_NAME:
            return entry.message_name

        if column == self.COL_DATA_LEN:
            return int(entry.data_len)

        if column == self.COL_RAW_DATA_BYTES:
            return str(entry.raw_data)

        return ""

    def _refresh_calculated_data(self, node: _Node):
        if node.type != Type.MESSAGE or not node.signals_loaded:
            return
        if self.my_model is None:
            return

        entry: CANLogLine = node.payload
        signals = entry.message_obj.signals

        if len(node.children) == len(signals):
            for child, sig in zip(node.children, signals):
                child.payload = sig
                child.text = f"・{sig.get_format_signal_show()}"
                child.tag = "sigchange" if sig.changed else "signormal"
        else:
            node.children = []
            for sig in signals:
                sig_node = _Node(node, Type.SIGNAL, sig)
                sig_node.text = f"・{sig.get_format_signal_show()}"
                sig_node.tag = "sigchange" if sig.changed else "signormal"
                node.children.append(sig_node)
            self.layoutChanged.emit()

        msg_row = node.parent.children.index(node) if node.parent is not None else -1
        if msg_row < 0:
            return
        parent_index = self.index(msg_row, 0, QModelIndex())
        if not parent_index.isValid() or not node.children:
            return

        top_left = self.index(0, 0, parent_index)
        bottom_right = self.index(len(node.children) - 1, self._columns - 1, parent_index)
        if top_left.isValid() and bottom_right.isValid():
            self.dataChanged.emit(
                top_left,
                bottom_right,
                [Qt.DisplayRole, Qt.ForegroundRole, Qt.BackgroundRole],
            )

    def setData(self, index, value, role=Qt.EditRole):
        if role != Qt.EditRole or not index.isValid() or not self._editable_mode:
            return False

        node: _Node = index.internalPointer()
        if node is None:
            return False

        self.capture_initial_edit_value(index)

        if node.type == Type.SIGNAL:
            if index.column() != self.COL_RAW_DATA_BYTES:
                return False

            old_raw = None
            new_raw = None
            if isinstance(value, dict):
                old_raw = value.get("old_raw")
                new_raw = value.get("new_raw")

            try:
                old_i = int(old_raw)
                new_i = int(new_raw)
            except (TypeError, ValueError):
                return False

            if old_i == new_i:
                initial = self.get_initial_edit_value(node, self.COL_RAW_DATA_BYTES)
                current = str(self._editable_data(node, self.COL_RAW_DATA_BYTES))
                if initial is not None and current == initial:
                    node.edited_cols.discard(self.COL_RAW_DATA_BYTES)
                    left = self.index(index.row(), self.COL_NAME, index.parent())
                    right = self.index(index.row(), self.COL_RAW_DATA_BYTES, index.parent())
                    self.dataChanged.emit(left, right, [Qt.DisplayRole, Qt.EditRole, Qt.ForegroundRole])
                return False

            parent_index = index.parent()
            parent_node: _Node = parent_index.internalPointer() if parent_index.isValid() else None
            if parent_node is None or parent_node.type != Type.MESSAGE:
                return False

            entry: CANLogLine = parent_node.payload
            if entry is None or entry.message_obj is None:
                return False

            old_data_len = int(entry.data_len)

            try:
                entry.message_obj.encode()
            except Exception as exc:
                LOG.critical(f"Failed to encode edited signal for CANID[{entry.can_id:X}]: {exc}")
                return False

            entry.data_len = int(entry.message_obj.data_len)
            entry.raw_data = " ".join(f"{b:02X}" for b in entry.message_obj.data)

            node.edited_cols.add(self.COL_RAW_DATA_BYTES)
            initial = self.get_initial_edit_value(node, self.COL_RAW_DATA_BYTES)
            current = str(self._editable_data(node, self.COL_RAW_DATA_BYTES))
            if initial is not None and current == initial:
                node.edited_cols.discard(self.COL_RAW_DATA_BYTES)

            parent_node.edited_cols.add(self.COL_RAW_DATA_BYTES)
            if int(entry.data_len) != old_data_len:
                parent_node.edited_cols.add(self.COL_DATA_LEN)
            else:
                parent_node.edited_cols.discard(self.COL_DATA_LEN)

            left = self.index(index.row(), self.COL_NAME, index.parent())
            right = self.index(index.row(), self.COL_RAW_DATA_BYTES, index.parent())
            self.dataChanged.emit(left, right, [Qt.DisplayRole, Qt.EditRole, Qt.ForegroundRole])

            msg_row = parent_index.row()
            msg_left = self.index(msg_row, self.COL_STR_TIMESTAMP, QModelIndex())
            msg_right = self.index(msg_row, self.COL_RAW_DATA_BYTES, QModelIndex())
            self.dataChanged.emit(msg_left, msg_right, [Qt.DisplayRole, Qt.EditRole, Qt.ForegroundRole])
            return True


        if node.type != Type.MESSAGE:
            return False

        col = index.column()
        if col in (self.COL_STR_TIMESTAMP, self.COL_CAN_ID_STR):
            return False

        entry: CANLogLine = node.payload
        changed = False

        try:
            if col == self.COL_STR_DIFF:
                new_text = str(value).strip()
                old_text = str(entry.timediff)
                if new_text == old_text:
                    return False
                entry.timediff = new_text
                changed = True
            elif col == self.COL_DIRECTION:
                direction = str(value).strip()
                if direction not in ("Rx", "Tx"):
                    return False
                if direction == str(entry.direction):
                    return False
                entry.direction = direction
                changed = True
            elif col == self.COL_NAME:
                text = str(value)
                old_name = entry.message_name
                if text == old_name:
                    return False
                entry.message_name = text
                changed = True
            elif col == self.COL_DATA_LEN:
                new_len = int(value)
                old_len = int(entry.data_len)
                if new_len == old_len:
                    return False
                entry.data_len = new_len
                changed = True
            elif col == self.COL_RAW_DATA_BYTES:
                text = str(value).strip()
                parser = RawBytesEditBox()
                parsed = parser._parse_raw_bytes(text)
                if parsed is None:
                    return False
                new_raw = " ".join(f"{b:02X}" for b in parsed)
                old_raw = str(entry.raw_data).upper()
                if new_raw.upper() == old_raw:
                    return False
                entry.raw_data = new_raw
                changed = True
            else:
                return False
        except Exception:
            return False

        if not changed:
            initial = self.get_initial_edit_value(node, col)
            current = str(self._editable_data(node, col))
            if initial is not None and current == initial:
                if col in node.edited_cols:
                    node.edited_cols.discard(col)
                    self.dataChanged.emit(index, index, [Qt.DisplayRole, Qt.EditRole, Qt.ForegroundRole])
            return False

        initial = self.get_initial_edit_value(node, col)
        current = str(self._editable_data(node, col))
        if initial is not None and current == initial:
            node.edited_cols.discard(col)
        else:
            node.edited_cols.add(col)

        if col in (self.COL_DATA_LEN, self.COL_RAW_DATA_BYTES):
            self._recalculate_message_signals(node)

        self.dataChanged.emit(index, index, [Qt.DisplayRole, Qt.EditRole, Qt.ForegroundRole])
        return True

    def capture_initial_edit_value(self, index: QModelIndex):
        if not index.isValid() or not self._editable_mode:
            return
        node: _Node = index.internalPointer()
        if node is None:
            return
        col = index.column()
        if col not in node.initial_edit_values:
            node.initial_edit_values[col] = str(self._editable_data(node, col))

    def get_initial_edit_value(self, node: _Node, col: int) -> Optional[str]:
        return node.initial_edit_values.get(col)

    def _reset_edit_tracking(self):
        def walk(n: _Node):
            n.edited_cols.clear()
            n.initial_edit_values.clear()
            for child in n.children:
                walk(child)
        walk(self._root)
        
    def fetchMore(self, parent=QModelIndex()):
        if parent.isValid():
            return

        self._load_until_row(self._loaded + self.chunk_size - 1)

    def _load_until_row(self, row: int):
        total = len(self._root.children)
        if total == 0:
            return
        if self._loaded >= total:
            return

        target_loaded = min(total, max(self._loaded, row + 1))
        if target_loaded <= self._loaded:
            return

        old_loaded = self._loaded
        self._loaded = target_loaded

        top_left = self.index(old_loaded, 0, QModelIndex())
        bottom_right = self.index(self._loaded - 1, self._columns - 1, QModelIndex())
        if top_left.isValid() and bottom_right.isValid():
            self.dataChanged.emit(top_left, bottom_right, [Qt.DisplayRole, Qt.ForegroundRole])

    def ensure_message_row_loaded(self, row: int, extra_after: int = 0) -> bool:
        total = len(self._root.children)
        if row < 0 or row >= total:
            return False
        self._load_until_row(min(total - 1, row + max(0, extra_after)))
        return True

    def parent(self, index):
        if not index.isValid():
            return QModelIndex()
        
        node = index.internalPointer()
        if node is None or node.parent is None or node.parent is self._root:
            return QModelIndex()
        
        parent_node = node.parent
        grand_parent = parent_node.parent
        if grand_parent is None:
            return QModelIndex()
        
        # Find row of parent in its parent's children
        row = grand_parent.children.index(parent_node) if parent_node in grand_parent.children else 0
        return self.createIndex(row, 0, parent_node)

    def flags(self, index):
        if not index.isValid():
            return Qt.NoItemFlags

        flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        if not self._editable_mode:
            return flags

        node: _Node = index.internalPointer()
        if node is None:
            return flags

        if node.type == Type.SIGNAL:
            if index.column() == self.COL_RAW_DATA_BYTES:
                flags |= Qt.ItemIsEditable
            return flags

        if node.type != Type.MESSAGE:
            return flags

        if index.column() in (self.COL_STR_DIFF, self.COL_DIRECTION, self.COL_NAME, self.COL_DATA_LEN, self.COL_RAW_DATA_BYTES):
            flags |= Qt.ItemIsEditable
        return flags

    def headerData(self, section, orientation, role):
        if role != Qt.DisplayRole or orientation != Qt.Horizontal:
            return None
        if not self._editable_mode:
            return "#" if section == 0 else "Log Messages"

        headers = ["Timestamp", "Diff", "Direction", "CAN ID", "Message Name", "DLC", "Data"]
        if 0 <= section < len(headers):
            return headers[section]
        return None

    # ---- helpers ----
    def _node_from_index(self, index: QModelIndex) -> _Node:
        return index.internalPointer() if index.isValid() else self._root

    def clear(self):
        self.beginResetModel()
        self._root.children.clear()
        self.endResetModel()

    def remove_can_id(self, can_id: int):
        self.beginResetModel()
        try:
            self._data = [entry for entry in self._data if int(entry.can_id) != int(can_id)]
            self._root.children = [node for node in self._root.children if int(node.payload.can_id) != int(can_id)]
            self._loaded = min(self._loaded, len(self._root.children))
        finally:
            self.endResetModel()

    # ---- highlight / clear ----
    def set_highlight(self, index: QModelIndex, highlight_tag: str):
        if not index.isValid():
            return
        node: _Node = index.internalPointer()
        node.highlight_tag = highlight_tag
        self.dataChanged.emit(index, index)

    def clear_highlight(self, index: QModelIndex):
        if not index.isValid():
            return
        node: _Node = index.internalPointer()
        node.highlight_tag = ""
        self.dataChanged.emit(index, index)

    def clear_all_highlights(self):
        def walk(n: _Node):
            n.highlight_tag = ""
            for c in n.children:
                walk(c)
        walk(self._root)
        self.layoutChanged.emit()

    # ---- selection helper like your get_cur_sel_tree_item ----
    def selection_info(self, index: QModelIndex):
        """
        Returns (Type.MESSAGE, CANLogLine, None) or (Type.SIGNAL, CANLogLine, Signal)
        """
        if not index.isValid():
            return None
        node: _Node = index.internalPointer()
        if node.type == Type.SIGNAL:
            sig: Signal = node.payload
            msg_node = node.parent
            msg: CANLogLine = msg_node.payload
            return (Type.SIGNAL, msg, sig)
        if node.type == Type.MESSAGE:
            msg: CANLogLine = node.payload
            return (Type.MESSAGE, msg, None)
        return None
    
    def clear_mark(self, index: QModelIndex):
        node = index.internalPointer()
        if not node:
            return
        node.tag = "normal"
        self.dataChanged.emit(index, index, [Qt.ForegroundRole])

    def clear_all_marks(self):
        self._clear_marks_recursive(self._root)
        self.layoutChanged.emit()

    def _clear_marks_recursive(self, node):
        node.tag = "normal"
        node.edited_cols.clear()
        for c in node.children:
            self._clear_marks_recursive(c)


from PySide6.QtWidgets import QWidget, QVBoxLayout, QTreeView, QMenu, QApplication
from PySide6.QtCore import Qt, QPoint

class TreeLogTable(QWidget):
    def __init__(self, parent=None, 
                 model: CANDBManager = None,
                 canlog: LogContextViewModel = None,
                 editable_mode: bool = False):
        super().__init__(parent)
        self._current_focus_message_row: Optional[int] = None
        self._editable_mode = bool(editable_mode)

        self.view = QTreeView(self)
        self.model_ = TreeLogModel(self, model, editable_mode=self._editable_mode)
        self.ctx_model = canlog
        self.view.setModel(self.model_)
        self.select_model = TreeLogSelectionModel(self.model_, model, self.view)
        self.view.setSelectionModel(self.select_model)
        self._edit_delegate = _TreeLogEditDelegate(self.view)

        # FONT
        mono = QFont("Consolas", 10)
        mono.setStyleHint(QFont.Monospace)
        self.view.setFont(mono)

        # HEADER
        header = self.view.header()
        self.view.setColumnWidth(0, 80)
        self.view.header().setStretchLastSection(False)
        header.setSectionResizeMode(QHeaderView.Fixed)
        self.view.setColumnWidth(1, 1600)
        header.setFixedHeight(20)
        font = header.font()
        font.setPointSize(font.pointSize())   # or setPointSize(11 / 12)
        # font.setBold(True)
        header.setFont(font)

        self.view.setSelectionMode(QTreeView.ExtendedSelection)
        self.view.setUniformRowHeights(True)   # good for performance
        self.view.setAnimated(False)
        self.view.setAutoScroll(False)  # prevent horizontal scroll on click/expand

        #self._apply_mode_config()

        self.view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.view.customContextMenuRequested.connect(self._show_context_menu)

        # Auto-scroll to bottom on data changes
        self._auto_scroll_enabled = False
        self._user_scrolling = False
        self.model_.rowsInserted.connect(self._auto_scroll_to_bottom)
        self.model_.modelReset.connect(self._auto_scroll_to_bottom)
        #self.model_.layoutChanged.connect(self._auto_scroll_to_bottom)

        vbar = self.view.verticalScrollBar()
        vbar.sliderPressed.connect(self._on_user_scroll_start)
        vbar.sliderReleased.connect(self._on_user_scroll_end)
        vbar.valueChanged.connect(self._on_scrollbar_value_changed)
        self.view.viewport().installEventFilter(self)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.view)
        self._context_cb = None  # your callback hook

    def _apply_mode_config(self):
        if self._editable_mode:
            self.model_.set_editable_mode(True)
            self.view.setEditTriggers(
                QAbstractItemView.DoubleClicked
                | QAbstractItemView.EditKeyPressed
                | QAbstractItemView.SelectedClicked
            )
            self.view.setItemDelegate(self._edit_delegate)
            self.view.setColumnWidth(0, 110)
            self.view.setColumnWidth(1, 90)
            self.view.setColumnWidth(2, 90)
            self.view.setColumnWidth(3, 90)
            self.view.setColumnWidth(4, 220)
            self.view.setColumnWidth(5, 70)
            self.view.setColumnWidth(6, 1200)
        else:
            self.model_.set_editable_mode(False)
            self.view.setEditTriggers(QAbstractItemView.NoEditTriggers)
            self.view.setColumnWidth(0, 80)
            self.view.setColumnWidth(1, 1600)

    def set_editable_mode(self, enabled: bool):
        self._editable_mode = bool(enabled)
        self._apply_mode_config()

    def set_data(self, data: list[CANLogLine]):
        self.model_.set_data(data)
        self._auto_scroll_to_bottom()

    def enable_auto_scroll(self):
        self._auto_scroll_enabled = True
        self._auto_scroll_to_bottom()

    def disable_auto_scroll(self):
        self._auto_scroll_enabled = False

    def _auto_scroll_to_bottom(self, *args):
        if not self._auto_scroll_enabled:
            return
        QTimer.singleShot(0, self.view.scrollToBottom)

    def _on_user_scroll_start(self):
        self._user_scrolling = True

    def _on_user_scroll_end(self):
        self._user_scrolling = False
        self._update_auto_scroll_from_scrollbar()

    def _on_scrollbar_value_changed(self, _value):
        if not self._user_scrolling:
            return
        self._update_auto_scroll_from_scrollbar()

    def _update_auto_scroll_from_scrollbar(self):
        vbar = self.view.verticalScrollBar()
        if vbar.value() >= vbar.maximum():
            self._auto_scroll_enabled = True
        else:
            self._auto_scroll_enabled = False

    def eventFilter(self, obj, event):
        if obj is self.view.viewport() and event.type() == QEvent.Wheel:
            self._user_scrolling = True
            self._update_auto_scroll_from_scrollbar()
            QTimer.singleShot(200, self._on_user_scroll_end)
        return super().eventFilter(obj, event)

    def clear_all(self):
        self.model_.clear()

    def focus_message_row(self, row: int) -> bool:
        row_h = self.view.rowHeight(self.model_.index(0, 0, QModelIndex()))
        if row_h <= 0:
            row_h = max(1, self.view.fontMetrics().height() + 6)

        visible_rows = max(1, self.view.viewport().height() // row_h)
        preload_after = max(visible_rows // 2, 10)

        if not self.model_.ensure_message_row_loaded(row, extra_after=preload_after):
            return False

        index = self.model_.index(row, 1, QModelIndex())
        if not index.isValid():
            return False

        self.select_model.setCurrentIndex(
            index,
            QItemSelectionModel.ClearAndSelect | QItemSelectionModel.Rows,
        )
        hbar = self.view.horizontalScrollBar()
        h_value = hbar.value()
        self.view.scrollTo(index, QTreeView.PositionAtCenter)
        hbar.setValue(h_value)
        self.view.setFocus()
        self._current_focus_message_row = row
        return True

    def get_current_focus_message_row(self) -> Optional[int]:
        return self._current_focus_message_row

    # -------------------------------------------------
    # Copy visible items (like your TreeWithContextMenu.copy_visible_items_to_clipboard)
    # -------------------------------------------------
    def copy_visible_items_to_clipboard(self):
        m = self.model_
        v = self.view
        lines: list[str] = []

        def recurse(parent_index: QModelIndex, indent: int = 0):
            rows = m.rowCount(parent_index)
            for r in range(rows):
                idx0 = m.index(r, 0, parent_index)
                idx1 = m.index(r, 1, parent_index)

                # Only copy if visible row (expanded path & not hidden)
                if v.isRowHidden(r, parent_index):
                    continue

                trend = str(m.data(idx0, Qt.DisplayRole) or "")
                text = str(m.data(idx1, Qt.DisplayRole) or "")
                line = ("    " * indent) + (trend + " " if trend else "") + text
                lines.append(line.rstrip())

                # recurse only if expanded (matches Tk "open")
                if v.isExpanded(idx0):
                    recurse(idx0, indent + 1)

        recurse(QModelIndex(), 0)

        out = "\n".join(lines)
        if out:
            QApplication.clipboard().setText(out)

    # -------------------------------------------------
    # Context menu (mirrors your Tk structure)
    # -------------------------------------------------
    def _show_context_menu(self, pos: QPoint):
        if not self.ctx_model:
            return
        index = self.view.indexAt(pos)
        menu = QMenu(self.view)

        # always available
        menu.addAction("Copy Visible", self.copy_visible_items_to_clipboard)

        export_visible = menu.addMenu("Export Visible As")
        export_visible.addAction(".txt", lambda: self._handle_action("export_visible_txt"))
        export_visible.addAction(".csv", lambda: self._handle_action("export_visible_csv"))

        # export_log = menu.addMenu("Export Log As")
        # export_log.addAction(".txt", lambda: self._handle_action("export_log_txt"))
        # export_log.addAction(".csv", lambda: self._handle_action("export_log_csv"))
        # export_log.addAction(".asc", lambda: self._handle_action("export_log_asc"))

        # no selection → stop like your Tk
        if not index.isValid():
            menu.exec(self.view.viewport().mapToGlobal(pos))
            return

        info = self.model_.selection_info(index)
        if not info:
            menu.exec(self.view.viewport().mapToGlobal(pos))
            return

        kind, msg, sig = info
        if kind == Type.SIGNAL:
            pass
            # menu.addSeparator()
            # menu.addAction("Copy Signal Name", lambda: self._handle_action("copy_signal_name"))
            # menu.addAction("Copy Signal Value", lambda: self._handle_action("copy_signal_value"))
            # menu.addAction("Copy Signal Raw Value", lambda: self._handle_action("copy_signal_raw_value"))
            #menu.addAction("Enable Export Log", lambda: self._handle_action("export_log"))
        else:
            menu.addSeparator()
            menu.addAction("Copy Selection Line", lambda: self._handle_action("copy_message_line"))
            # menu.addAction("Clear Mark Color", lambda: self._handle_action("clear_mark_color"))
            # menu.addAction("Clear All Color", lambda: self._handle_action("clear_all_color"))
            #menu.addAction("Enable Export Screen", lambda: self._handle_action("log_screen"))

        menu.exec(self.view.viewport().mapToGlobal(pos))

    def _handle_action(self, action: str):
        """
        Handles all context-menu actions based on current selection.
        """

        index: QModelIndex = self.currentIndex()
        if not index.isValid():
            return

        info = self.model_.selection_info(index)
        if not info:
            return

        kind, msg, sig = info
        clipboard = QApplication.clipboard()

        # -----------------------------
        # MESSAGE ACTIONS
        # -----------------------------
        if kind == Type.MESSAGE:
            if action == "copy_message_line":
                clipboard.setText(msg.format_line_log(
                    self.model_.my_model.candb.message_name_max_len
                ))
                return
        
        if action == "export_visible_txt":
            save_path, _ = QFileDialog.getSaveFileName(
                self.view,
                "Save filtered log as",
                "out.txt",
                "Text Files (*.txt);;All Files (*.*)"
            )
            if not save_path:
                return

            self.copy_visible_items_to_clipboard()
            open_in_editor(save_path)

        if action == "export_visible_csv":
            save_path, _ = QFileDialog.getSaveFileName(
                self.view,
                "Save filtered log as",
                "out.csv",
                "CSV Files (*.csv);;All Files (*.*)"
            )
            if not save_path:
                return

            self.ctx_model.mCLM.write_log_csv(
                filepath=self.ctx_model.current_context_filepath,
                lines=self.ctx_model.cur_ctx.canlog_filter,
                save_filepath=save_path,
            )
            open_in_editor(save_path)
            return

if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton
    from PySide6.QtCore import Qt
    setup_logger(env="DEV", backup_count=30)
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    win = QWidget()
    win.setWindowTitle("TreeLogView Test")
    layout = QVBoxLayout(win)

    model = CANDBManager()
    model.load_database(
        "/home/gnar911/Desktop/20260122 APP WEBSITE - CAN ANALYZER 3.0 CBCM TOOL APP ARC/CAN_Analyzer_MVVM/Database/EEA10_CANFD_R00c_withADAS_Main.dbc")
    ctx = LogContextViewModel()

    test_lines = [
        "2132132 CANFD   1 Rx        417                                   1 0 8 8  14 3C 40 00 00 00 09 BC",
        "2132133 CANFD   1 Rx        48E                                   1 0 8 8  40 92 49 60 80 4D 00 00",
        "2132132 CANFD   1 Rx        100                                   1 0 8 8  14 3C 40 00 00 00 10 BC",
        "2132135 CANFD   1 Rx         84                                   1 0 8 8  3F 85 3E 76 81 02 2F 3F",
        "2132137 CANFD   1 Rx        41E                                   1 0 8 8  40 92 14 60 80 4D 00 00",
        "2132138 CANFD   1 Rx        38E                                   1 0 8 8  40 80 49 60 80 4D 00 00",
        "2132139 CANFD   1 Rx        18E                                   1 0 8 8  40 92 49 10 80 4D 00 00",
        "2132135 CANFD   1 Rx         85                                   1 0 8 8  3F 85 3E 76 81 02 2F 3F",
        "2132137 CANFD   1 Rx         86                                   1 0 8 8  40 92 14 60 80 4D 00 00",
        "2132138 CANFD   1 Rx         87                                   1 0 8 8  40 80 49 60 80 4D 00 00",
        "2132139 CANFD   1 Rx         88                                   1 0 8 8  40 92 49 10 80 4D 00 00",
    ]

    parser = LogParser()

    parsed_lines = []
    base_ts = 2132132

    for i in range(10_000):
        line = test_lines[i % len(test_lines)]

        # tweak timestamp + CAN ID slightly
        ts = base_ts + i
        can_id = f"{(0x100 + i) & 0x7FF:03X}"

        # replace timestamp and CAN ID columns (fixed-width safe)
        new_line = (
            f"{ts:<7}"
            + line[7:31]
            + f"{can_id:>8}"
            + line[39:]
        )

        parsed_lines.append(parser._parse_line(new_line, i))

    tree = TreeLogTable(model=model,
                        canlog=ctx)
    
    tree.model_.set_data(parsed_lines)

    layout.addWidget(tree)

    focus_btn = QPushButton("Focus Next Test Row")
    focus_targets = [10, 100, 1000]
    focus_state = {"click": 0}

    def on_focus_click():
        click = focus_state["click"]
        if click < len(focus_targets):
            target_row = focus_targets[click]
        else:
            target_row = 2000 + (click - len(focus_targets)) * 1000

        ok = tree.focus_message_row(target_row)
        print(f"focus_message_row({target_row}) -> {ok}, current_focus_row={tree.get_current_focus_message_row()}")
        focus_state["click"] = click + 1

    focus_btn.clicked.connect(on_focus_click)
    layout.addWidget(focus_btn)

    edit_btn = QPushButton("Enable Edit Mode")
    edit_state = {"enabled": False}

    def on_toggle_edit_mode():
        edit_state["enabled"] = not edit_state["enabled"]
        tree.set_editable_mode(edit_state["enabled"])
        edit_btn.setText("Disable Edit Mode" if edit_state["enabled"] else "Enable Edit Mode")
        print(f"Editable mode: {edit_state['enabled']}")

    edit_btn.clicked.connect(on_toggle_edit_mode)
    layout.addWidget(edit_btn)

    win.resize(800, 500)
    win.show()

    sys.exit(app.exec())
