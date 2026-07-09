from typing import Optional

from PySide6.QtCore import Qt, QTimer, QModelIndex, QPersistentModelIndex
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import QStyle

from can_sdk.data_object import CANLogLine, CANLogPlay, SendState
from can_sdk.dbc_manager import CANDBManager
from can_sdk.connection_viewmodel import CANConnectManager

from ui_sdk.components.pyqt.TreeLogMessageSignals import (
    TreeLogMessageSignals,
    TreeLogMessageSignalsModel,
    TreeLogSelectionSignalsModel,
    _TreeLogMessageSignalsDelegate,
    _Node,
    Type,
)
from ui_sdk.components.pyqt.TreeLogMessage import TreeLogMessageModel
from ui_sdk.components.pyqt.ChannelComboBox import ChannelComboBox, ChannelEditBox

class _TreeSenderSignalsDelegate(_TreeLogMessageSignalsDelegate):
    def __init__(self, parent=None, connection_model: Optional[CANConnectManager] = None):
        super().__init__(parent)
        self._status_anim_frame: int = 0
        self._status_anim_frames = ("···", "▶··", "·▶·", "··▶")
        self._connection_model = connection_model

    def set_connection_model(self, connection_model: Optional[CANConnectManager]):
        self._connection_model = connection_model

    def createEditor(self, parent, option, index):
        if index.isValid():
            model = index.model()
            node = index.internalPointer()
            if (
                isinstance(node, _Node)
                and node.type == Type.MESSAGE
                and index.column() == getattr(model, "COL_CHANNEL", -1)
            ):
                editor = ChannelEditBox(parent, connection_model=self._connection_model)
                return editor
        return super().createEditor(parent, option, index)

    def setEditorData(self, editor, index):
        if isinstance(editor, ChannelEditBox):
            model = index.model()
            if hasattr(model, "capture_initial_edit_value"):
                model.capture_initial_edit_value(index)
            node = index.internalPointer() if index.isValid() else None
            if isinstance(node, _Node) and isinstance(node.payload, CANLogLine):
                editor.set_entry(node.payload)
                editor._initial_channel = node.payload.channel
            return
        return super().setEditorData(editor, index)

    def setModelData(self, editor, model, index):
        if isinstance(editor, ChannelEditBox):
            entry = editor.entry()
            if entry is not None:
                old_channel = getattr(editor, "_initial_channel", entry.channel)
                new_channel = entry.channel
                model.setData(index, {"old_channel": old_channel, "new_channel": new_channel}, Qt.EditRole)
            return
        return super().setModelData(editor, model, index)

    def set_status_anim_frame(self, frame: int):
        try:
            self._status_anim_frame = int(frame)
        except Exception:
            self._status_anim_frame = 0

    def paint(self, painter, option, index):
        if not index.isValid():
            super().paint(painter, option, index)
            return

        model = index.model()
        node: _Node = index.internalPointer()
        status_col = getattr(model, "COL_STATUS", -1)

        if (
            isinstance(node, _Node)
            and node.type == Type.MESSAGE
            and index.column() == status_col
        ):
            opt = option
            style = opt.widget.style() if opt.widget else None
            if style is None:
                super().paint(painter, option, index)
                return

            style.drawControl(QStyle.CE_ItemViewItem, opt, painter, opt.widget)
            text_rect = style.subElementRect(QStyle.SE_ItemViewItemText, opt, opt.widget)

            status_text = ""
            entry: CANLogPlay = node.payload
            if isinstance(entry, CANLogPlay):
                send_state = getattr(entry, "send_state", None)
                if isinstance(send_state, SendState):
                    if send_state == SendState.SENDING:
                        status_text = self._status_anim_frames[self._status_anim_frame % len(self._status_anim_frames)]
                    elif send_state == SendState.PAUSED:
                        status_text = "❚❚"
                    elif send_state == SendState.DISCONNETED:
                        status_text = "✖"
                else:
                    status_text = "▶" if bool(getattr(entry, "is_send", False)) else "❚❚"

            painter.save()
            pen_color = opt.palette.color(
                QPalette.HighlightedText if opt.state & QStyle.State_Selected else QPalette.Text
            )
            painter.setPen(pen_color)
            painter.drawText(text_rect, Qt.AlignCenter, status_text)
            painter.restore()
            return

        super().paint(painter, option, index)


class TreeSenderModel(TreeLogMessageSignalsModel):
    COL_CHANNEL = 7
    COL_STATUS = 8

    def __init__(self, parent=None, model: CANDBManager = None):
        super().__init__(parent=parent, model=model)
        self._allow_edit_dlc = False

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        node = index.internalPointer()
        if index.column() == self.COL_CHANNEL:
            entry = getattr(node, "payload", None)
            if not isinstance(entry, CANLogLine):
                return super().data(index, role)
            if role == Qt.TextAlignmentRole:
                return Qt.AlignCenter
            if role in (Qt.DisplayRole, Qt.EditRole):
                return entry.channel
            return super().data(index, role)
        if isinstance(node, _Node) and node.type == Type.MESSAGE and index.column() == self.COL_STATUS:
            if role == Qt.TextAlignmentRole:
                return Qt.AlignCenter
            if role in (Qt.DisplayRole, Qt.EditRole):
                entry: CANLogPlay = node.payload
                send_state = getattr(entry, "send_state", None)
                if isinstance(send_state, SendState):
                    if send_state == SendState.SENDING:
                        return "▶"
                    if send_state == SendState.PAUSED:
                        return "❚❚"
                    if send_state == SendState.DISCONNETED:
                        return "✕"
                    return ""
                return "▶" if bool(getattr(entry, "is_send", False)) else "❚❚"
            return None
        return super().data(index, role)

    def set_allow_edit_dlc(self, allow: bool):
        allow = bool(allow)
        if allow == self._allow_edit_dlc:
            return
        self._allow_edit_dlc = allow
        total = self._total_rows()
        if total <= 0:
            return
        top_left = self.index(0, self.COL_DATA_LEN, QModelIndex())
        bottom_right = self.index(total - 1, self.COL_DATA_LEN, QModelIndex())
        if top_left.isValid() and bottom_right.isValid():
            self.dataChanged.emit(top_left, bottom_right, [Qt.DisplayRole, Qt.EditRole, Qt.ForegroundRole])

    def is_allow_edit_dlc(self) -> bool:
        return bool(self._allow_edit_dlc)

    def flags(self, index):
        base = super().flags(index)
        if not index.isValid():
            return base
        # Signal rows have a valid parent (the message row).
        # Parent flags() already set correct editable state for them.
        # Return base unmodified so signal editing is preserved.
        if index.parent().isValid():
            return base
        # From here, only message rows.
        # Do NOT guard on node.type == Type.MESSAGE — during paint,
        # the delegate temporarily swaps node.type to a different enum,
        # which would make that check fail and break hover highlight.
        col = index.column()
        if col == self.COL_DATA_LEN:
            if self._editable_mode and self.is_allow_edit_dlc():
                return base | Qt.ItemIsEditable
            return base & ~Qt.ItemIsEditable
        if col == self.COL_RAW_DATA_BYTES:
            if self._editable_mode and self.is_allow_edit_raw_data():
                return base | Qt.ItemIsEditable
            return base & ~Qt.ItemIsEditable
        if col == self.COL_CHANNEL:
            if self._editable_mode:
                return base | Qt.ItemIsEditable
            return base & ~Qt.ItemIsEditable
        if col == self.COL_STATUS:
            return (base | Qt.ItemIsEnabled | Qt.ItemIsSelectable) & ~Qt.ItemIsEditable
        return base

    def setData(self, index, value, role=Qt.EditRole):
        if role != Qt.EditRole or not index.isValid() or not self._editable_mode:
            return super().setData(index, value, role)

        node = index.internalPointer()
        if isinstance(node, _Node) and node.type == Type.MESSAGE:
            if index.column() == self.COL_CHANNEL:
                self.capture_initial_edit_value(index)
                entry: CANLogPlay = node.payload

                # Accept dict from delegate (like SignalEditBox pattern)
                # or plain str from direct calls.
                if isinstance(value, dict):
                    old_channel = value.get("old_channel", entry.channel)
                    new_channel = value.get("new_channel", entry.channel)
                else:
                    old_channel = entry.channel
                    new_channel = value

                if old_channel == new_channel:
                    return False
                # entry.channel already mutated by ChannelComboBox._select_value,
                # but set it again for non-dict callers.
                entry.channel = new_channel
                initial = self.get_initial_edit_value(node, index.column())
                current = str(self.data(index, Qt.DisplayRole) or "")
                if initial is not None and str(initial) == current:
                    node.edited_cols.discard(index.column())
                else:
                    node.edited_cols.add(index.column())

                self._last_edited_index = QPersistentModelIndex(index)
                self.dataChanged.emit(index, index, [Qt.DisplayRole, Qt.EditRole, Qt.ForegroundRole])
                return True
            if index.column() == self.COL_DATA_LEN:
                if not self.is_allow_edit_dlc():
                    return False
                return TreeLogMessageModel.setData(self, index, value, role)
            if index.column() == self.COL_RAW_DATA_BYTES:
                if not self.is_allow_edit_raw_data():
                    return False
                return TreeLogMessageModel.setData(self, index, value, role)

        return super().setData(index, value, role)

    def headerData(self, section, orientation, role):
        if role != Qt.DisplayRole or orientation != Qt.Horizontal:
            return None
        headers = ["Timestamp", "Diff", "Direction", "CAN ID", "Message Name", "DLC", "Data", "Channel", "Status"]
        if 0 <= section < len(headers):
            return self._header_overrides.get(section, headers[section])
        return super().headerData(section, orientation, role)


class TreeSenderTable(TreeLogMessageSignals):
    """TreeLogMessageSignals-based sender table: always edit mode + status column + no red paint."""

    def __init__(self, parent=None, model: Optional[CANDBManager] = None, connection_model: Optional[CANConnectManager] = None):
        super().__init__(parent=parent, model=model)

        self.model_ = TreeSenderModel(self, model=model)
        self.view.setModel(self.model_)
        self.select_model = TreeLogSelectionSignalsModel(self.model_, self.view)
        self.view.setSelectionModel(self.select_model)
        self._auto_dropdown_signals_on_select = True
        self.select_model.currentChanged.connect(self._on_sender_current_changed)
        self.view.setExpandsOnDoubleClick(False)
        self.view.setAutoScroll(False)

        self._edit_delegate = _TreeSenderSignalsDelegate(self.view, connection_model=connection_model)
        self._edit_delegate.set_edit_red_paint_enabled(False)
        self.view.setItemDelegate(self._edit_delegate)

        self._status_anim_timer = QTimer(self)
        self._status_anim_timer.setInterval(180)
        self._status_anim_frame = 0
        self._status_anim_timer.timeout.connect(self._on_status_anim_tick)
        self._status_anim_timer.start()

        self._disable_parent_dropdown_timer()

        self._editable_mode = True
        self.model_._editable_mode = True
        self.model_._columns = 9
        self.model_.begin_edit_session()
        self._apply_mode_config()

    def set_connection_model(self, connection_model: Optional[CANConnectManager]):
        if self._edit_delegate is not None:
            self._edit_delegate.set_connection_model(connection_model)

    def _on_status_anim_tick(self):
        self._status_anim_frame = (self._status_anim_frame + 1) % 10000
        self._edit_delegate.set_status_anim_frame(self._status_anim_frame)
        status_col = getattr(self.model_, "COL_STATUS", -1)
        if status_col < 0:
            self.view.viewport().update()
            return
        x = self.view.columnViewportPosition(status_col)
        w = self.view.columnWidth(status_col)
        if w <= 0:
            return
        self.view.viewport().update(x, 0, w, self.view.viewport().height())

    def _disable_parent_dropdown_timer(self):
        timer = getattr(self, "_hover_collapse_timer", None)
        timer.stop()
        self._hover_tooltip_timer.stop()
        self._hover_tooltip_timer.timeout.disconnect()

    def _expand_hover_row(self, index: QModelIndex):
        """Override: do nothing – sender table does not auto-expand on hover."""
        return

    def set_auto_dropdown_signals_on_select(self, enabled: bool):
        self._auto_dropdown_signals_on_select = bool(enabled)

    def is_auto_dropdown_signals_on_select(self) -> bool:
        return bool(self._auto_dropdown_signals_on_select)

    def _on_sender_current_changed(self, current: QModelIndex, previous: QModelIndex):
        if not self._auto_dropdown_signals_on_select:
            return
        if not current.isValid():
            return
        message_index = current.siblingAtColumn(0)
        node = message_index.internalPointer() if message_index.isValid() else None
        if not isinstance(node, _Node) or node.type != Type.MESSAGE:
            return
        self.model_.ensure_signals_loaded_for_message_index(message_index)
        if not self.view.isExpanded(message_index):
            self.view.expand(message_index)
    def set_message_name_visible(self, visible: bool):
        col = getattr(self.model_, "COL_NAME", 4)
        self.view.setColumnHidden(col, not bool(visible))

    def set_allow_edit_raw_data(self, allow: bool):
        self.model_.set_allow_edit_raw_data(allow)

    def is_allow_edit_raw_data(self) -> bool:
        return self.model_.is_allow_edit_raw_data()

    def unset_allow_edit_raw_data(self):
        self.set_allow_edit_raw_data(False)

    def set_allow_edit_dlc(self, allow: bool):
        self.model_.set_allow_edit_dlc(allow)

    def is_allow_edit_dlc(self) -> bool:
        return self.model_.is_allow_edit_dlc()

    def unset_allow_edit_dlc(self):
        self.set_allow_edit_dlc(False)

    def unset_message_name_visible(self):
        self.set_message_name_visible(False)

    def _apply_mode_config(self):
        self.model_.set_allow_edit_raw_data(False)
        self.model_.set_header_text(self.model_.COL_STR_DIFF, "Cycle")
        channel_col = getattr(self.model_, "COL_CHANNEL", -1)
        status_col = getattr(self.model_, "COL_STATUS", None)
        if status_col is not None:
            self.model_.set_header_text(status_col, "Status")
        if self._edit_delegate is not None:
            self._edit_delegate.set_edit_red_paint_enabled(False)
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
        self.view.setColumnWidth(6, 760)
        if channel_col >= 0:
            self.view.setColumnWidth(channel_col, 90)
        if status_col is not None:
            self.view.setColumnWidth(status_col, 90)

        self.view.setColumnHidden(self.model_.COL_STR_TIMESTAMP, True)
        self.view.setColumnHidden(self.model_.COL_DIRECTION, True)
        if status_col is not None:
            self.view.setColumnHidden(status_col, False)

        header = self.view.header()
        header.setSectionsMovable(True)
        can_id_visual = header.visualIndex(self.model_.COL_CAN_ID_STR)
        channel_visual = header.visualIndex(channel_col) if channel_col >= 0 else -1
        cycle_visual = header.visualIndex(self.model_.COL_STR_DIFF)
        status_visual = header.visualIndex(status_col) if status_col is not None else -1
        if can_id_visual >= 0 and channel_visual >= 0:
            header.moveSection(channel_visual, can_id_visual)
        if cycle_visual >= 0 and status_visual >= 0:
            header.moveSection(status_visual, cycle_visual)


if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton
    from can_sdk.test_ultility import TEST_generated_CANLogLine_batch, TEST_set_up_DBModel, TEST_set_up_all_channels
    from lw.logger_setup import setup_logger

    setup_logger(env="DEV", backup_count=30)
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    db_model = TEST_set_up_DBModel()
    parsed_lines = TEST_generated_CANLogLine_batch(2)
    connect_manager = TEST_set_up_all_channels()

    win = QWidget()
    win.setWindowTitle("TreeSenderTable Test")
    layout = QVBoxLayout(win)

    tree = TreeSenderTable(model=db_model, connection_model=connect_manager)
    layout.addWidget(tree)

    load_btn = QPushButton("Load Sender Data")

    def on_load_click():
        tree.set_data(parsed_lines)

    load_btn.clicked.connect(on_load_click)
    layout.addWidget(load_btn)

    acquire_next_btn = QPushButton("Acquire Next Channel")

    def on_acquire_next_click():
        handles = sorted(
            connect_manager.available_channels.keys(),
            key=lambda h: int(getattr(h, "channel_idx", -1)),
        )
        if not handles:
            acquire_next_btn.setText("No Available Channel")
            return

        handle = handles[0]
        ok = connect_manager.acquire(handle)
        if ok:
            acquire_next_btn.setText(f"Acquired CH{int(getattr(handle, 'channel_idx', -1))}")
        else:
            acquire_next_btn.setText("Acquire Failed")

    acquire_next_btn.clicked.connect(on_acquire_next_click)
    layout.addWidget(acquire_next_btn)

    win.resize(980, 560)
    win.show()

    sys.exit(app.exec())
