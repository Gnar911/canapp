from enum import Enum, auto
from typing import List, Dict, Optional, Any

from PySide6.QtCore import Qt, QModelIndex, QPersistentModelIndex, QEvent, QTimer
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QLineEdit, QToolTip, QWidget
from lw.logger_setup import setup_logger, LOG
from canapp.data_object import CANLogLine, SignalFilter, Signal
from can_sdk.dbc_manager import CANDBManager
from canapp.widgets.TreeLogMessage import (
    TreeLogMessage,
    TreeLogMessageModel,
    TreeLogSelectionModel,
    _TreeLogMessageDelegate,
    _MessageNode,
)
from canapp.widgets.SignalEditBox import SignalEditBox
from can_sdk.test_ultility import TEST_generated_CANLogLine_batch, TEST_set_up_DBModel

class Type(Enum):
    MESSAGE = auto()
    SIGNAL = auto()

class _Node(_MessageNode):
    """Extended node that adds signal-decoding attributes on top of _MessageNode."""
    __slots__ = ("highlight_tag", "edited_cols", "signals_loaded", "initial_edit_values")

    def __init__(self, parent: Optional["_Node"], type, payload: Any):
        super().__init__(parent, type, payload)
        self.highlight_tag = ""
        self.edited_cols: set[int] = set()
        self.signals_loaded = False
        self.initial_edit_values: dict[int, str] = {}


class _TreeLogMessageSignalsDelegate(_TreeLogMessageDelegate):
    # ── Import parent's Type so per-char red paint works ───────────────
    # Parent paint() checks `node.type != Type.MESSAGE` using its OWN
    # Type enum, but child nodes carry the CHILD's Type.MESSAGE (a
    # different enum class).  We temporarily coerce the type so the
    # parent's per-char diff paint executes for MESSAGE rows.
    from canapp.widgets.TreeLogMessage import Type as _ParentType

    def paint(self, painter, option, index):
        node = index.internalPointer() if index.isValid() else None
        if isinstance(node, _Node) and node.type == Type.MESSAGE:
            # Swap to parent enum so parent paint recognises it
            node.type = self._ParentType.MESSAGE
            try:
                super().paint(painter, option, index)
            finally:
                node.type = Type.MESSAGE
            return
        super().paint(painter, option, index)

    def createEditor(self, parent, option, index):
        if not index.isValid():
            return None
        model = index.model()
        node = index.internalPointer()
        if isinstance(node, _Node) and node.type == Type.MESSAGE and index.column() == getattr(model, "COL_NAME", -1):
            return QLineEdit(parent)
        if isinstance(node, _Node) and node.type == Type.SIGNAL:
            value_col = getattr(model, "COL_SIG_VALUE", getattr(model, "COL_RAW_DATA_BYTES", -1))
            if index.column() == value_col:
                editor = SignalEditBox(parent)
                editor.set_widget_height(option.rect.height())
                return editor
        return super().createEditor(parent, option, index)

    def setEditorData(self, editor, index):
        node = index.internalPointer() if index.isValid() else None
        if isinstance(editor, SignalEditBox) and isinstance(node, _Node) and node.type == Type.SIGNAL:
            sig = node.payload
            if isinstance(sig, Signal):
                editor.set_signal(sig)
                editor._initial_raw = sig.get_raw_value()
                return
        return super().setEditorData(editor, index)

    def setModelData(self, editor, model, index):
        node = index.internalPointer() if index.isValid() else None
        if isinstance(editor, SignalEditBox) and isinstance(node, _Node) and node.type == Type.SIGNAL:
            sig = node.payload
            if isinstance(sig, Signal):
                old_raw = getattr(editor, "_initial_raw", sig.get_raw_value())
                new_raw = sig.get_raw_value()
                model.setData(index, {"old_raw": old_raw, "new_raw": new_raw}, Qt.EditRole)
                return
        return super().setModelData(editor, model, index)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Selection model – handles both MESSAGE and SIGNAL nodes
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class TreeLogSelectionSignalsModel(TreeLogSelectionModel):
    """Extends parent selection model with Signal-level selection."""
    TAG_FG = {
        **TreeLogMessageModel.TAG_FG,
        "signormal": QColor("#0000FF"),
        "sigchange": QColor("#FF0000"),
    }
    NODE_TYPE = _Node

    def _create_data_for_selection(self, current: QModelIndex) -> SignalFilter:
        #LOG.debug("_create_data_for_selection")
        item = current.internalPointer()
        if not isinstance(item, _Node):
            return super()._create_data_for_selection(current)

        if item.type == Type.MESSAGE:
            self._build_signal_nodes(current, item)

        selection_sig = super()._create_data_for_selection(current)

        if item.type == Type.SIGNAL:
            signal: Signal = item.payload
            if isinstance(signal, Signal):
                selection_sig.signal_info = signal.sig_info
                selection_sig.rawvalue = signal.raw_value

            msg_node = item.parent
            if isinstance(msg_node, _Node) and isinstance(msg_node.payload, CANLogLine):
                msg_entry: CANLogLine = msg_node.payload
                selection_sig.msg_info = msg_entry.message_obj.msg_info if msg_entry.message_obj else None

        return selection_sig

    def _build_signal_nodes(self, parent_index: QModelIndex, node: _Node):
        """
        set_data: 3.0825s | render: 1.3365s | total: 4.4190s
        """
        if node.signals_loaded:
            return

        model = self.model()
        if not isinstance(model, TreeLogMessageSignalsModel):
            return

        model._calculate_message(node)

        entry: CANLogLine = node.payload
        if not isinstance(entry, CANLogLine) or entry.message_obj is None:
            return

        msg_info = entry.message_obj.msg_info
        if msg_info is None:
            return

        signals = entry.message_obj.cal_signal_value()
        if not signals:
            node.signals_loaded = True
            return

        parent_col0 = parent_index.siblingAtColumn(0) if parent_index.isValid() else QModelIndex()
        if not parent_col0.isValid():
            parent_col0 = model.index(node.row, 0, QModelIndex())
        if not parent_col0.isValid():
            return

        new_children = []
        for i, (name, sig) in enumerate(signals.items()):
            sig.sig_info = msg_info.get_signal_by_name(name)
            sig_node = _Node(node, Type.SIGNAL, sig)
            sig_node.text = f"・{sig.get_format_signal_show()}"
            sig_node.tag = "sigchange" if sig.changed else "signormal"
            sig_node.row = i
            new_children.append(sig_node)

        if new_children:
            model.beginInsertRows(parent_col0, 0, len(new_children) - 1)
            node.children = new_children
            model.endInsertRows()

        node.signals_loaded = True

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Model – extends TreeLogMessageModel with signal child rows from DBC
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class TreeLogMessageSignalsModel(TreeLogMessageModel):
    NODE_TYPE = _Node
    COL_NAME = 4
    COL_DATA_LEN = 5
    COL_RAW_DATA_BYTES = 6
    COL_SIG_NAME = COL_NAME
    COL_SIG_UNIT = COL_DATA_LEN
    COL_SIG_VALUE = COL_RAW_DATA_BYTES
    """Extends TreeLogMessageModel with signal decoding via CANDBManager.

    Each message row may expand into decoded signal child rows.
    Inherits flat message handling (set_data, clear, headerData, etc.) from parent.
    """
    def __init__(self, parent=None, model: CANDBManager = None):
        super().__init__(parent)
        self.my_model = model
        # if self.my_model is not None and hasattr(self.my_model, "event_on_db_changed"):
        #     self.my_model.event_on_db_changed.subscribe(self._on_db_changed)

    # ── Node factory override ──────────────────────────────────────────
    def _build_message_node(self, row: int, entry: CANLogLine):
        """set_data: 0.1233s | render: 1.3268s | total: 1.4501s"""
        node = super()._build_message_node(row, entry)
        node.type = Type.MESSAGE
        self._calculate_message(node)
        # if self.my_model is not None:
        #     self._build_signals_node(node)
        return node

    # ── DB change handler ──────────────────────────────────────────────
    # def _on_db_changed(self, *_):
    #     pass
    # ── Tree structure overrides (add signal children) ─────────────────

    def rowCount(self, parent=QModelIndex()):
        if not parent.isValid():
            return self._total_rows()
        node = parent.internalPointer()
        if isinstance(node, _Node) and node.type == Type.MESSAGE:
            return len(node.children)
        return 0

    def hasChildren(self, parent=QModelIndex()):
        if not parent.isValid():
            return self._total_rows() > 0
        node = parent.internalPointer()
        if not isinstance(node, _Node) or node.type != Type.MESSAGE:
            return False
        if node.children:
            return True
        # Show expand arrow when DBC match exists (children loaded lazily)
        entry = node.payload
        if isinstance(entry, CANLogLine) and entry.message_obj is not None:
            return True
        return False

    def index(self, row, column, parent=QModelIndex()):
        if not parent.isValid():
            return super().index(row, column, parent)
        # Signal child index
        parent_node = parent.internalPointer()
        if not isinstance(parent_node, _Node) or row < 0 or row >= len(parent_node.children):
            return QModelIndex()
        return self.createIndex(row, column, parent_node.children[row])

    def parent(self, index):
        if not index.isValid():
            return QModelIndex()
        node = index.internalPointer()
        if not isinstance(node, _Node):
            return QModelIndex()
        # Signal node → return its message parent
        if node.type == Type.SIGNAL:
            parent_node = node.parent
            if isinstance(parent_node, _Node) and parent_node.row >= 0:
                if self._message_nodes.get(parent_node.row) is parent_node:
                    return self.createIndex(parent_node.row, 0, parent_node)
            return QModelIndex()
        # Message node → root (invisible)
        return QModelIndex()

    # ── Data display override ──────────────────────────────────────────

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        node = index.internalPointer()
        if not isinstance(node, _Node):
            return None

        if role == Qt.ForegroundRole:
            if self._editable_mode and index.column() in node.edited_cols:
                """ If it is message, keep normal and handle paint red in def paint"""
                #LOG.debug(f"NODE TYPE SIGNAL: {node.type}")
                if node.type == Type.MESSAGE and index.column() == self.COL_RAW_DATA_BYTES:
                    return self.TAG_FG["normal"]
                """ If it is signal -> paint Full cell"""
                return QColor("#FF0000")
            return self.TAG_FG.get(node.tag, QColor("#FFFFFF"))

        # ── Signal node rendering ──
        if node.type == Type.SIGNAL:
            if role == Qt.BackgroundRole:
                return QColor("#242424")
            if role not in (Qt.DisplayRole, Qt.EditRole):
                return None
            column = index.column()
            sig: Signal = node.payload
            # Read mode: show signal text in the wide message column
            if not self._editable_mode:
                if column == self.COL_LOG_MESSAGES:
                    return node.text or f"・{sig.get_format_signal_show()}"
                return ""
            # Edit mode columns
            if column == self.COL_SIG_NAME:
                return f"・{str(sig.signal_name or '')}"
            if column == self.COL_SIG_VALUE:
                return str(sig.value or "")
            if column == self.COL_SIG_UNIT:
                return str(sig.value_unit or "")            
            return ""

        # ── Message node – add name column at this class level ──
        if role in (Qt.DisplayRole, Qt.EditRole) and index.column() == self.COL_NAME:
            entry: CANLogLine = node.payload
            return str(entry.message_name or "")

        return super().data(index, role)

    def headerData(self, section, orientation, role):
        if role != Qt.DisplayRole or orientation != Qt.Horizontal:
            return None
        if self._editable_mode:
            headers = ["Timestamp", "Diff", "Direction", "CAN ID", "Message Name", "DLC", "Data"]
            if 0 <= section < len(headers):
                return self._header_overrides.get(section, headers[section])
            return None
        return super().headerData(section, orientation, role)

    def set_editable_mode(self, enabled: bool):
        enabled = bool(enabled)
        if enabled == self._editable_mode:
            return

        old_columns = self._columns
        self._editable_mode = enabled
        self._columns = 7 if self._editable_mode else 2
        if self._editable_mode:
            self.begin_edit_session()

        self.headerDataChanged.emit(Qt.Horizontal, 0, max(old_columns, self._columns) - 1)
        total = self._total_rows()
        if total > 0:
            top_left = self.index(0, 0, QModelIndex())
            bottom_right = self.index(total - 1, self._columns - 1, QModelIndex())
            if top_left.isValid() and bottom_right.isValid():
                self.dataChanged.emit(top_left, bottom_right, [Qt.DisplayRole, Qt.ForegroundRole])
        self.layoutChanged.emit()

    def capture_initial_edit_value(self, index: QModelIndex):
        if not index.isValid():
            return
        node = index.internalPointer()
        if isinstance(node, _Node) and node.type == Type.SIGNAL and index.column() == self.COL_SIG_VALUE:
            col = int(index.column())
            if col not in node.initial_edit_values:
                sig: Signal = node.payload
                node.initial_edit_values[col] = str(sig.get_raw_value())
            return
        super().capture_initial_edit_value(index)

    def flags(self, index):
        if not index.isValid():
            return Qt.NoItemFlags

        node = index.internalPointer()
        if isinstance(node, _Node) and node.type == Type.SIGNAL:
            flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable
            if self._editable_mode and index.column() == self.COL_SIG_VALUE:
                flags |= Qt.ItemIsEditable
            return flags

        flags = super().flags(index)
        if self._editable_mode and index.column() == self.COL_NAME:
            flags |= Qt.ItemIsEditable
        if index.column() in (self.COL_DATA_LEN, self.COL_RAW_DATA_BYTES):
            return flags & ~Qt.ItemIsEditable
        return flags

    def setData(self, index, value, role=Qt.EditRole):
        if role != Qt.EditRole or not index.isValid() or not self._editable_mode:
            return False

        node = index.internalPointer()
        if not isinstance(node, _Node):
            return super().setData(index, value, role)

        if node.type == Type.SIGNAL:
            if index.column() != self.COL_SIG_VALUE:
                return False

            sig: Signal = node.payload
            parent_node = node.parent if isinstance(node.parent, _Node) else None
            parent_entry: Optional[CANLogLine] = parent_node.payload if isinstance(parent_node, _Node) else None

            # ── Capture initial from editor's pre-edit value ──────────
            # SignalEditBox mutates sig directly, so sig.get_raw_value()
            # already holds the POST-edit value by this point.
            # Use old_raw from the dict (editor._initial_raw) for a
            # correct pre-edit capture.
            col = int(index.column())
            if col not in node.initial_edit_values:
                if isinstance(value, dict) and value.get("old_raw") is not None:
                    node.initial_edit_values[col] = str(int(value["old_raw"]))
                else:
                    node.initial_edit_values[col] = str(sig.get_raw_value())

            parent_raw_index = QModelIndex()
            parent_dlc_index = QModelIndex()
            if isinstance(parent_node, _Node) and parent_node.row >= 0:
                parent_raw_index = self.index(parent_node.row, self.COL_RAW_DATA_BYTES, QModelIndex())
                parent_dlc_index = self.index(parent_node.row, self.COL_DATA_LEN, QModelIndex())
                if parent_raw_index.isValid():
                    self.capture_initial_edit_value(parent_raw_index)
                if parent_dlc_index.isValid():
                    self.capture_initial_edit_value(parent_dlc_index)

            if isinstance(value, dict):
                new_raw = value.get("new_raw")
                old_raw = value.get("old_raw")
                if new_raw is None:
                    return False
                try:
                    if old_raw is not None and int(new_raw) == int(old_raw):
                        return False
                except Exception:
                    pass
                sig.set_raw_value(new_raw)
            else:
                text = str(value).strip()
                if not text:
                    return False
                try:
                    sig.set_raw_value(int(float(text)))
                except Exception:
                    return False

            if isinstance(parent_entry, CANLogLine):
                self._calculate_message(parent_node)
                msg_obj = parent_entry.message_obj
                if msg_obj is not None:
                    try:
                        payload = msg_obj.encode(scaling=False, padding=False, strict=True)
                        parent_entry.data_len = int(msg_obj.data_len)
                        parent_entry.raw_data = " ".join(f"{b:02X}" for b in payload)
                    except Exception:
                        return False

            initial_sig = self.get_initial_edit_value(node, self.COL_SIG_VALUE)
            current_sig = str(sig.get_raw_value())
            if initial_sig is not None and current_sig == initial_sig:
                node.edited_cols.discard(self.COL_SIG_VALUE)
            else:
                node.edited_cols.add(self.COL_SIG_VALUE)

            node.text = f"・{sig.get_format_signal_show()}"
            left = index.siblingAtColumn(self.COL_SIG_NAME)
            right = index.siblingAtColumn(self.COL_SIG_VALUE)
            self.dataChanged.emit(left, right, [Qt.DisplayRole, Qt.EditRole, Qt.ForegroundRole])

            if isinstance(parent_node, _Node):
                parent_node.text = ""
                if parent_raw_index.isValid():
                    initial_raw = self.get_initial_edit_value(parent_node, self.COL_RAW_DATA_BYTES)
                    current_raw = str(self.data(parent_raw_index, Qt.DisplayRole) or "")
                    if initial_raw is not None and current_raw == initial_raw:
                        parent_node.edited_cols.discard(self.COL_RAW_DATA_BYTES)
                    else:
                        parent_node.edited_cols.add(self.COL_RAW_DATA_BYTES)

                if parent_dlc_index.isValid():
                    initial_dlc = self.get_initial_edit_value(parent_node, self.COL_DATA_LEN)
                    current_dlc = str(self.data(parent_dlc_index, Qt.DisplayRole) or "")
                    if initial_dlc is not None and current_dlc == initial_dlc:
                        parent_node.edited_cols.discard(self.COL_DATA_LEN)
                    else:
                        parent_node.edited_cols.add(self.COL_DATA_LEN)

                if parent_dlc_index.isValid() and parent_raw_index.isValid():
                    self.dataChanged.emit(
                        parent_dlc_index,
                        parent_raw_index,
                        [Qt.DisplayRole, Qt.EditRole, Qt.ForegroundRole],
                    )

            self._last_edited_index = QPersistentModelIndex(index)
            return True

        if index.column() in (self.COL_DATA_LEN, self.COL_RAW_DATA_BYTES):
            return False

        if node.type != Type.MESSAGE:
            return super().setData(index, value, role)

        if index.column() == self.COL_NAME:
            self.capture_initial_edit_value(index)
            entry: CANLogLine = node.payload
            new_name = str(value)
            if new_name == str(entry.message_name or ""):
                return False
            entry.message_name = new_name

            initial = self.get_initial_edit_value(node, index.column())
            current = str(self.data(index, Qt.DisplayRole) or "")
            if initial is not None and current == initial:
                node.edited_cols.discard(index.column())
            else:
                node.edited_cols.add(index.column())

            node.text = ""
            self._last_edited_index = QPersistentModelIndex(index)
            self.dataChanged.emit(index, index, [Qt.DisplayRole, Qt.EditRole, Qt.ForegroundRole])
            return True

        return super().setData(index, value, role)

    def revert_index_edit(self, index: QModelIndex) -> bool:
        if not index.isValid():
            return False

        node = index.internalPointer()
        if not isinstance(node, _Node):
            return False

        if node.type == Type.SIGNAL:
            signal_value_index = index.siblingAtColumn(self.COL_SIG_VALUE)
            if not signal_value_index.isValid():
                return False
            initial = self.get_initial_edit_value(node, self.COL_SIG_VALUE)
            if initial is None:
                return False
            return bool(self.setData(signal_value_index, initial, Qt.EditRole))

        initial = self.get_initial_edit_value(node, index.column())
        if initial is None:
            return False

        if node.type == Type.MESSAGE and index.column() in (self.COL_DATA_LEN, self.COL_RAW_DATA_BYTES):
            return bool(TreeLogMessageModel.setData(self, index, initial, Qt.EditRole))

        return bool(self.setData(index, initial, Qt.EditRole))

    def revert_row_edits(self, index: QModelIndex) -> bool:
        if not index.isValid():
            return False

        node = index.internalPointer()
        if not isinstance(node, _Node):
            return False

        if node.type == Type.SIGNAL:
            signal_value_index = index.siblingAtColumn(self.COL_SIG_VALUE)
            if not signal_value_index.isValid():
                return False
            return bool(self.revert_index_edit(signal_value_index))

        if node.type != Type.MESSAGE:
            return False

        any_success = False
        parent_col0 = index.siblingAtColumn(0)

        for child in list(node.children):
            if not isinstance(child, _Node) or child.type != Type.SIGNAL:
                continue
            if self.COL_SIG_VALUE not in child.edited_cols:
                continue
            child_index = self.index(child.row, self.COL_SIG_VALUE, parent_col0)
            if child_index.isValid() and self.revert_index_edit(child_index):
                any_success = True

        for col in sorted(int(c) for c in list(node.edited_cols)):
            cell_index = index.siblingAtColumn(col)
            if not cell_index.isValid():
                continue
            if self.revert_index_edit(cell_index):
                any_success = True

        return any_success

    def ensure_signals_loaded_for_message_index(self, index: QModelIndex) -> bool:
        if not index.isValid():
            return False
        message_index = index.siblingAtColumn(0)
        if not message_index.isValid():
            return False

        node = message_index.internalPointer()
        if not isinstance(node, _Node) or node.type != Type.MESSAGE:
            return False
        if node.signals_loaded:
            return bool(node.children)

        self._calculate_message(node)

        entry: CANLogLine = node.payload
        if not isinstance(entry, CANLogLine) or entry.message_obj is None or entry.message_obj.msg_info is None:
            node.signals_loaded = True
            return False

        signals = entry.message_obj.cal_signal_value()
        if not signals:
            node.signals_loaded = True
            return False

        new_children = []
        msg_info = entry.message_obj.msg_info
        for i, (name, sig) in enumerate(signals.items()):
            sig.sig_info = msg_info.get_signal_by_name(name)
            sig_node = _Node(node, Type.SIGNAL, sig)
            sig_node.text = f"・{sig.get_format_signal_show()}"
            sig_node.tag = "sigchange" if sig.changed else "signormal"
            sig_node.row = i
            new_children.append(sig_node)

        if new_children:
            self.beginInsertRows(message_index, 0, len(new_children) - 1)
            node.children = new_children
            self.endInsertRows()

        node.signals_loaded = True
        return bool(node.children)

    def _calculate_message(self, node: _Node):
        entry: CANLogLine = node.payload
        msg_info = self.my_model.get_message(entry.can_id)
        if msg_info is None:
            return
        entry.cal_message_obj(msg_info)

    # def _calculate_signals(self, node: _Node) -> Dict[str, Signal]:
    #     entry: CANLogLine = node.payload
    #     if not isinstance(entry, CANLogLine) or entry.message_obj is None:
    #         return {}
    #     return entry.message_obj.cal_signal_value()

    # def _ensure_message_signals_calculated(self, node: _Node) -> Dict[str, Signal]:
    #     self._calculate_message(node)
    #     return self._calculate_signals(node)

    # def _create_index_for_absolute_row(self, abs_row: int, column: int = 0) -> QModelIndex:
    #     return self.index(abs_row, column, QModelIndex())

    # ── Utilities ──────────────────────────────────────────────────────

    def _node_from_index(self, index: QModelIndex) -> _Node:
        return index.internalPointer() if index.isValid() else self._root

    def selection_info(self, index: QModelIndex):
        if not index.isValid():
            return None
        node = index.internalPointer()
        if not isinstance(node, _Node):
            return None
        if node.type == Type.SIGNAL:
            sig: Signal = node.payload
            msg_node = node.parent
            msg: CANLogLine = msg_node.payload
            return (Type.SIGNAL, msg, sig)
        if node.type == Type.MESSAGE:
            msg: CANLogLine = node.payload
            return (Type.MESSAGE, msg, None)
        return None

class TreeLogMessageSignals(TreeLogMessage):
    """TreeLogMessage + signal decoding.

    Inherits the full QTreeView / layout / font / header setup from TreeLogMessage,
    then swaps the model and selection-model for signal-aware versions.
    """

    def __init__(self, parent=None, model: CANDBManager = None):
        self._hover_collapse_timer = None
        self._hover_dropdown_pinned = False
        # Parent builds: self.view, self.model_, self.select_model, layout, etc.
        super().__init__(parent)

        # Replace the flat message model with signal-decoded model
        self.model_ = TreeLogMessageSignalsModel(self, model=model)
        self.view.setModel(self.model_)

        # Replace the selection model with signal-aware selection
        self.select_model = TreeLogSelectionSignalsModel(self.model_, self.view)
        self.view.setSelectionModel(self.select_model)

        self._edit_delegate = _TreeLogMessageSignalsDelegate(self.view)
        if getattr(self, "_editable_mode", False):
            self.view.setItemDelegate(self._edit_delegate)

        self._hover_collapse_timer = QTimer(self)
        self._hover_collapse_timer.setSingleShot(True)
        self._hover_collapse_timer.timeout.connect(self._collapse_hover_expanded_row)

        # Lazy-load signal children when a row is expanded (read or edit mode)
        self.view.expanded.connect(self._on_row_expanded)

        self._bind_undo_state_tracking()
        self._emit_undo_availability(force=True)

    def _on_row_expanded(self, index: QModelIndex):
        """Lazily load signal children when the user expands a message row."""
        if not isinstance(self.model_, TreeLogMessageSignalsModel):
            return
        self.model_.ensure_signals_loaded_for_message_index(index)

    # def set_db_model(self, model: CANDBManager):
    #     """Hot-swap the DBC model (re-decodes signal children)."""
    #     self.model_.my_model = model
    #     if model is not None and hasattr(model, "event_on_db_changed"):
    #         model.event_on_db_changed.subscribe(self.model_._on_db_changed)

    def _apply_mode_config(self):
        if self._editable_mode:
            self.model_.set_editable_mode(True)
            self.model_.set_allow_edit_raw_data(False)
            if self._edit_delegate is not None and hasattr(self._edit_delegate, "set_edit_red_paint_enabled"):
                self._edit_delegate.set_edit_red_paint_enabled(True)
            self.view.setEditTriggers(
                self.view.EditTrigger.DoubleClicked
                | self.view.EditTrigger.EditKeyPressed
                | self.view.EditTrigger.SelectedClicked
            )
            self.view.setItemDelegate(self._edit_delegate)
            self.view.setStyleSheet("")
            self.view.setColumnWidth(0, 110)
            self.view.setColumnWidth(1, 90)
            self.view.setColumnWidth(2, 90)
            self.view.setColumnWidth(3, 90)
            self.view.setColumnWidth(4, 220)
            self.view.setColumnWidth(5, 70)
            self.view.setColumnWidth(6, 1120)
        else:
            self._hover_tooltip_timer.stop()
            self._hover_tooltip_index = QPersistentModelIndex()
            QToolTip.hideText()
            if self._hover_collapse_timer is not None:
                self._hover_collapse_timer.stop()
            if self._edit_delegate is not None and hasattr(self._edit_delegate, "set_edit_red_paint_enabled"):
                self._edit_delegate.set_edit_red_paint_enabled(True)
            super()._apply_mode_config()

    def _on_item_hovered(self, index: QModelIndex):
        if self._edit_delegate is None:
            return

        if not getattr(self, "_editable_mode", False):
            old_idx = self._edit_delegate.clear_hover()
            if old_idx.isValid():
                self.view.viewport().update(self.view.visualRect(old_idx))
            self._hover_tooltip_timer.stop()
            self._hover_tooltip_index = QPersistentModelIndex()
            QToolTip.hideText()
            if self._hover_collapse_timer is not None:
                self._hover_collapse_timer.stop()
            return

        node = index.internalPointer() if index.isValid() else None
        expanded_parent = QModelIndex(self._hover_expanded_parent)
        is_signal_of_expanded = (
            isinstance(node, _Node)
            and node.type == Type.SIGNAL
            and expanded_parent.isValid()
            and index.parent().isValid()
            and index.parent().siblingAtColumn(0).row() == expanded_parent.row()
            and index.parent().siblingAtColumn(0).parent() == expanded_parent.parent()
        )

        editable_index = index if (index.isValid() and bool(self.model_.flags(index) & Qt.ItemIsEditable)) else QModelIndex()
        old_idx, new_idx = self._edit_delegate.set_hovered_index(editable_index)

        inside_region = editable_index.isValid() or is_signal_of_expanded
        if inside_region or self._hover_dropdown_pinned:
            if self._hover_collapse_timer is not None:
                self._hover_collapse_timer.stop()

        if editable_index.isValid():
            persistent = QPersistentModelIndex(editable_index)
            if self._hover_tooltip_index != persistent:
                self._hover_tooltip_index = persistent
                self._hover_tooltip_timer.start(1000)
        elif is_signal_of_expanded:
            self._hover_tooltip_timer.stop()
            self._hover_tooltip_index = QPersistentModelIndex()
            QToolTip.hideText()
        else:
            self._hover_tooltip_timer.stop()
            self._hover_tooltip_index = QPersistentModelIndex()
            QToolTip.hideText()
            if not self._hover_dropdown_pinned:
                if self._hover_collapse_timer is not None:
                    self._hover_collapse_timer.start(1000)

        if (
            editable_index.isValid()
            and self._hover_expanded_parent.isValid()
            and not is_signal_of_expanded
            and not self._hover_dropdown_pinned
        ):
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

        if isinstance(self.model_, TreeLogMessageSignalsModel):
            self.model_.ensure_signals_loaded_for_message_index(index)

        super()._show_edit_tooltip()

    def eventFilter(self, obj, event):
        if not getattr(self, "_editable_mode", False):
            if obj is self.view.viewport() and event.type() == QEvent.Leave:
                return QWidget.eventFilter(self, obj, event)
            return super().eventFilter(obj, event)

        if obj is self.view.viewport() and event.type() == QEvent.MouseButtonPress:
            pos = event.position().toPoint() if hasattr(event, "position") else event.pos()
            idx = self.view.indexAt(pos)
            expanded_parent = QModelIndex(self._hover_expanded_parent)
            node = idx.internalPointer() if idx.isValid() else None
            is_signal_of_expanded = (
                isinstance(node, _Node)
                and node.type == Type.SIGNAL
                and expanded_parent.isValid()
                and idx.parent().isValid()
                and idx.parent().siblingAtColumn(0).row() == expanded_parent.row()
                and idx.parent().siblingAtColumn(0).parent() == expanded_parent.parent()
            )

            if is_signal_of_expanded:
                self._hover_dropdown_pinned = True
                if self._hover_collapse_timer is not None:
                    self._hover_collapse_timer.stop()
            else:
                self._hover_dropdown_pinned = False

        if obj is self.view.viewport() and event.type() == QEvent.Leave:
            if self._edit_delegate is not None:
                old_idx = self._edit_delegate.clear_hover()
                if old_idx.isValid():
                    self.view.viewport().update(self.view.visualRect(old_idx))

            self._hover_tooltip_timer.stop()
            self._hover_tooltip_index = QPersistentModelIndex()
            QToolTip.hideText()
            if not self._hover_dropdown_pinned:
                if self._hover_collapse_timer is not None:
                    self._hover_collapse_timer.start(1000)
            return QWidget.eventFilter(self, obj, event)

        return super().eventFilter(obj, event)


if __name__ == "__main__":
    import sys
    import time
    from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton
    from lw.logger_setup import setup_logger

    setup_logger(env="DEV", backup_count=30)
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    db_model = TEST_set_up_DBModel()
    parsed_lines = TEST_generated_CANLogLine_batch(10000)

    win = QWidget()
    win.setWindowTitle("TreeLogMessageSignals Test")
    layout = QVBoxLayout(win)
    tree = TreeLogMessageSignals(model=db_model)
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