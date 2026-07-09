from PySide6.QtCore import Qt
from can_sdk.dbc_manager import CANDBManager 
from can_sdk.connection_viewmodel import CANConnectManager, Handle, CANSendManager
from can_sdk.logger_setup import LOG, setup_logger
from typing import Optional
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QMessageBox, QPushButton, QApplication)
from PySide6.QtCore import Slot, Qt
from ui_sdk.components.pyqt.TreeSenderTable import TreeSenderTable
from ui_sdk.components.pyqt.DBCCombobox import DBCComboBox
from ui_sdk.components.pyqt.ChannelComboBox import ChannelComboBox
from ui_sdk.components.pyqt.ParseableEditBox import CanIdEditBox, RawBytesEditBox
from ui_sdk.components.pyqt.DLCSpinbox import DLCSpinBox
from can_sdk.data_object import CANLogLine, CANLogPlay, SignalFilter, SendState
from can_sdk.global_event import event_on_signal_select
from ultility import bytes_to_hex_raw, hex_raw_to_bytes 
# TEST module
from can_sdk.parser import LogParser
from can_sdk.connection_viewmodel import CANConnectManager, Handle, CANDeviceType, ChannelContext
import sys
import re
import math
from dataclasses import dataclass
from typing import Any, Optional, Callable, Dict, List, Tuple
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt

# -----------------------------
# Helpers / Small widgets
# -----------------------------

_HEX_BYTE_RE = re.compile(r"^[0-9a-fA-F]{0,2}$")


class HexByteLineEdit(QtWidgets.QLineEdit):
    """
    1-byte hex editor:
    - accepts 0..FF (no 0x)
    - always displays uppercase
    - grey if 00, blue if != 00, red if invalid
    """
    valueChanged = QtCore.Signal(int)  # emits 0..255

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None):
        super().__init__(parent)
        self.setMaxLength(2)
        self.setFixedSize(26, 22)
        self.setAlignment(Qt.AlignCenter)
        self.setTextMargins(0, 0, 0, 0)
        self.setStyleSheet("QLineEdit { padding: 0px; margin: 0px; }")

        # validator: allow empty or 1-2 hex digits
        self._validator = QtGui.QRegularExpressionValidator(
            QtCore.QRegularExpression(r"^[0-9a-fA-F]{0,2}$"),
            self,
        )
        self.setValidator(self._validator)

        self.textEdited.connect(self._on_text_edited)
        self.editingFinished.connect(self._normalize)
        self._apply_color()

        self._is_default_value = True
        self._has_baseline = False
        self._baseline_value = 0

        # better monospace for bytes
        f = self.font()
        f.setFamily("Monospace")
        self.setFont(f)

    def _on_text_edited(self, _t: str):
        self._is_default_value = False
        self._apply_color()
        v = self.value()
        if v is not None:
            self.valueChanged.emit(v)

    def _normalize(self):
        # normalize to 2-digit uppercase (or empty -> "00")
        t = self.text().strip()
        if t == "":
            self.setText("00")
        else:
            try:
                v = int(t, 16)
                v = max(0, min(255, v))
                self.setText(f"{v:02X}")
            except Exception:
                # keep as-is if invalid
                pass
        self._apply_color()

    def _apply_color(self):
        t = self.text().strip()
        if t == "":
            # neutral
            self.setStyleSheet("QLineEdit{color:#303030;}")
            return
        if not _HEX_BYTE_RE.fullmatch(t):
            self.setStyleSheet("QLineEdit{color:red;}")
            return
        try:
            int(t, 16)
        except Exception:
            self.setStyleSheet("QLineEdit{color:red;}")
            return
        if not self._is_default_value:
            self.setStyleSheet("QLineEdit{color:#0066CC;}")
            return
        self.setStyleSheet("QLineEdit{color:#FFFFFF;}")

    def value(self) -> Optional[int]:
        t = self.text().strip()
        if t == "":
            return 0
        if not _HEX_BYTE_RE.fullmatch(t):
            return None
        try:
            return int(t, 16)
        except Exception:
            return None

    def set_value(self, v: int, is_default: bool = False):
        v = max(0, min(255, int(v)))
        self._is_default_value = is_default
        self.setText(f"{v:02X}")
        self._apply_color()

    def set_baseline(self, v: int):
        self._has_baseline = True
        self._baseline_value = max(0, min(255, int(v)))
        self._apply_color()

    def clear_baseline(self):
        self._has_baseline = False
        self._baseline_value = 0
        self._apply_color()


class Debouncer(QtCore.QObject):
    """
    Simple debouncer for text parsing / UI updates.
    """
    timeout = QtCore.Signal()

    def __init__(self, ms: int, parent: Optional[QtCore.QObject] = None):
        super().__init__(parent)
        self._timer = QtCore.QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(ms)
        self._timer.timeout.connect(self.timeout.emit)

    def start(self):
        self._timer.start()

    def stop(self):
        self._timer.stop()

# -----------------------------
# Main panel
# -----------------------------
class CustomSendMessagePanel(QtWidgets.QWidget):
    send_status_signal = QtCore.Signal(object)

    def __init__(
        self,
        parent: QWidget,
        candb: CANDBManager,
        cnt_model: CANConnectManager,                  # CANConnectManager
        handle: Handle,           # ChannelContext (preferred)
    ):
        super().__init__(parent)
        self.handle = handle
        self.candb = candb
        self.cnt_model = cnt_model
        self.chl_ctx: Optional[ChannelContext] = self.cnt_model.get_context(self.handle)
        self.sender: Optional[CANSendManager] = self.cnt_model.get_sender()
        self.cnt_model.event_on_channels_state_changed.subscribe(self._on_channels_state_changed)
        event_on_signal_select.subscribe(self._on_event_signal_select)
        
        # UI state
        self._added: Dict[int, CANLogPlay] = {}          # can_id -> last added line
        #self._status: Dict[int, str] = {}                 # can_id -> status
        self._last_selected_can_id: Optional[int] = None
        self._suppress_raw_empty_action = False
        self._raw_baseline: Optional[bytes] = None
        self._send_button_mode: str = "SEND_FIRST"         # SEND_FIRST / PAUSE / RESUME
        self._send_all_button_mode: str = "SEND_ALL"      # SEND_ALL / PAUSE_ALL / RESUME_ALL
        self._has_any_send_activity: bool = False

        # Build UI
        self._build_ui()
        self._wire_events()
        self.send_status_signal.connect(self._handle_sender_status_on_ui, QtCore.Qt.QueuedConnection)

        # Initialize button states
        self._refresh_buttons()
        self._update_disconnect_overlay()

    # -----------------------------
    # UI construction
    # -----------------------------

    def _build_ui(
        self,
    ):
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        # Top row: Message combo + cycle + dlc + channel
        top = QtWidgets.QGridLayout()
        top.setHorizontalSpacing(6)
        top.setVerticalSpacing(4)

        header_frame = QtWidgets.QFrame(self)
        header_layout = QtWidgets.QHBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(6)

        lbl_msg = QtWidgets.QLabel("ID - Message Name")
        lbl_msg.setStyleSheet("QLabel { color: #C8CDD3; }")
        header_layout.addWidget(lbl_msg)

        self.chk_use_dbc = QtWidgets.QCheckBox("Use DBC")
        f = self.chk_use_dbc.font()
        f.setPointSize(f.pointSize() - 2)
        self.chk_use_dbc.setFont(f)
        self.chk_use_dbc.setStyleSheet("QCheckBox { color: #C8CDD3; }")
        self.chk_use_dbc.setChecked(True)
        header_layout.addWidget(self.chk_use_dbc)

        top.addWidget(header_frame, 0, 0, 1, 2)

        lbl_cycle = QtWidgets.QLabel("Cycle ms")
        lbl_cycle.setStyleSheet("QLabel { color: #C8CDD3; }")
        top.addWidget(lbl_cycle, 0, 2)

        lbl_dlc = QtWidgets.QLabel("DLC")
        lbl_dlc.setStyleSheet("QLabel { color: #C8CDD3; }")
        top.addWidget(lbl_dlc, 0, 3)

        lbl_channel = QtWidgets.QLabel("Channel")
        lbl_channel.setStyleSheet("QLabel { color: #C8CDD3; }")
        top.addWidget(lbl_channel, 0, 4)

        self.msg_stack = QtWidgets.QStackedWidget(self)

        self.combo_msg = DBCComboBox(self, self.candb)
        self.msg_stack.addWidget(self.combo_msg)

        self.edit_msg = CanIdEditBox(self)
        self.msg_stack.addWidget(self.edit_msg)

        top.addWidget(self.msg_stack, 1, 0, 1, 2)

        # Cycle spin
        self.spin_cycle = QtWidgets.QSpinBox(self)
        self.spin_cycle.setRange(1, 10000)
        self.spin_cycle.setValue(300)
        self.spin_cycle.setSuffix(" ms")
        self.spin_cycle.setFixedWidth(110)
        top.addWidget(self.spin_cycle, 1, 2)

        # DLC spin (CAN FD up to 15)
        self.spin_dlc = DLCSpinBox(self)
        # self.spin_dlc.setRange(0, 15)
        # self.spin_dlc.setValue(15)
        self.spin_dlc.set_len_value(8)
        self.spin_dlc.setFixedWidth(70)
        top.addWidget(self.spin_dlc, 1, 3)

        self.combo_channel = ChannelComboBox(self, connection_model=self.cnt_model)
        self.combo_channel.setFixedWidth(210)
        top.addWidget(self.combo_channel, 1, 4)

        top.setColumnStretch(0, 1)
        top.setColumnStretch(1, 1)

        root.addLayout(top)

        btn_row_widget = QtWidgets.QWidget(self)
        btn_row = QtWidgets.QHBoxLayout(btn_row_widget)
        btn_row.setContentsMargins(0, 0, 0, 0)
        btn_row.setSpacing(8)
        btn_row.addStretch(1)

        self.btn_add = QtWidgets.QPushButton("Add", self)
        self.btn_add.setFixedWidth(80)
        btn_row.addWidget(self.btn_add)

        self.btn_remove = QtWidgets.QPushButton("Remove", self)
        self.btn_remove.setFixedWidth(90)
        btn_row.addWidget(self.btn_remove)

        self.btn_send = QtWidgets.QPushButton("Send", self)
        self.btn_send.setFixedWidth(80)
        btn_row.addWidget(self.btn_send)

        self.btn_pause_all = QtWidgets.QPushButton("Pause all", self)
        self.btn_pause_all.setFixedWidth(100)
        self.btn_pause_all.setEnabled(False)
        btn_row.addWidget(self.btn_pause_all)

        self.btn_remove_all = QtWidgets.QPushButton("Remove All", self)
        self.btn_remove_all.setFixedWidth(110)
        self.btn_remove_all.setEnabled(False)
        btn_row.addWidget(self.btn_remove_all)

        root.addWidget(btn_row_widget)

        # Raw bytes paste input
        self.raw_row_widget = QtWidgets.QWidget(self)
        raw_row = QtWidgets.QHBoxLayout(self.raw_row_widget)
        raw_row.setContentsMargins(0, 0, 0, 0)
        raw_row.setSpacing(8)
        self.lbl_raw_bytes = QtWidgets.QLabel("Raw Bytes:", self.raw_row_widget)
        raw_row.addWidget(self.lbl_raw_bytes)

        self.edit_raw_bytes = RawBytesEditBox(self.raw_row_widget)
        raw_row.addWidget(self.edit_raw_bytes, 1)

        # self.lbl_raw_status = QtWidgets.QLabel("")
        # self.lbl_raw_status.setMinimumWidth(180)
        # raw_row.addWidget(self.lbl_raw_status)

        root.addWidget(self.raw_row_widget)

        # Data bytes group
        self.grp_data = QtWidgets.QGroupBox("", self)
        self.grp_data_layout = QtWidgets.QGridLayout(self.grp_data)
        self.grp_data_layout.setContentsMargins(0, 0, 0, 0)
        self.grp_data_layout.setHorizontalSpacing(0)
        self.grp_data_layout.setVerticalSpacing(0)

        root.addWidget(self.grp_data)

        # Build initial byte editors based on DLC
        self._hex_edits: List[HexByteLineEdit] = []
        self._rebuild_hex_editors(self.spin_dlc.current_len_value())

        self.tree = TreeSenderTable(self, model=self.candb)
        root.addWidget(self.tree, 1)

        selected_name = self._channel_name_for_channel_value(getattr(self.handle, "channel_idx", None))
        if selected_name:
            idx = self.combo_channel.findText(str(selected_name), Qt.MatchExactly)
            if idx >= 0:
                self.combo_channel.setCurrentIndex(idx)

        self._disconnected_overlay = QtWidgets.QFrame(self)
        self._disconnected_overlay.setObjectName("sendPanelDisconnectOverlay")
        self._disconnected_overlay.setStyleSheet(
            "QFrame#sendPanelDisconnectOverlay { background: rgba(20, 20, 20, 110); }"
        )

        overlay_layout = QtWidgets.QVBoxLayout(self._disconnected_overlay)
        overlay_layout.setContentsMargins(16, 16, 16, 16)
        overlay_layout.setAlignment(Qt.AlignCenter)

        self._disconnected_label = QtWidgets.QLabel("Channel disconnected", self._disconnected_overlay)
        self._disconnected_label.setAlignment(Qt.AlignCenter)
        self._disconnected_label.setStyleSheet(
            "QLabel { color: white; font-size: 18px; font-weight: 600; }"
        )
        overlay_layout.addWidget(self._disconnected_label)

        self._disconnected_overlay.hide()

        self.setLayout(root)

    def _wire_events(self):
        self.spin_dlc.valueChanged.connect(self._on_dlc_changed)
        self.spin_cycle.valueChanged.connect(self._refresh_buttons)
        self.chk_use_dbc.toggled.connect(self._on_use_dbc_toggled)
        self.combo_msg.currentIndexChanged.connect(self._on_message_changed)
        self.edit_msg.textChanged.connect(self._on_message_changed)
        self.btn_add.clicked.connect(self._on_add_or_update_clicked)
        self.btn_remove.clicked.connect(self._on_remove_clicked)
        self.btn_send.clicked.connect(self._on_send_pause_resume_clicked)
        self.btn_pause_all.clicked.connect(self._on_pause_all_clicked)
        self.btn_remove_all.clicked.connect(self._on_remove_all_clicked)
        self._raw_debouncer = Debouncer(150, self)
        self.edit_raw_bytes.textChanged.connect(lambda _t: self._raw_debouncer.start())
        self._raw_debouncer.timeout.connect(self._on_raw_bytes_debounced)

        # If user edits hex fields, mark dirty and possibly switch Add->Update
        for e in self._hex_edits:
            e.textEdited.connect(self._refresh_buttons)

        #self.candb.event_on_signal_select.subscribe()
        self.sender.event_on_send_status_changed.subscribe(self._on_sender_status_changed)
        self._on_use_dbc_toggled(self.chk_use_dbc.isChecked())

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "_disconnected_overlay"):
            self._disconnected_overlay.setGeometry(self.rect())
            if self._disconnected_overlay.isVisible():
                self._disconnected_overlay.raise_()

    def _on_channels_state_changed(self, *_):
        if hasattr(self, "combo_channel"):
            prev_channel_name = self.combo_channel.currentText().strip()
            self.combo_channel.refresh_channels()
            if prev_channel_name:
                idx = self.combo_channel.findText(prev_channel_name, Qt.MatchExactly)
                if idx >= 0:
                    self.combo_channel.setCurrentIndex(idx)
        self._update_disconnect_overlay()

    def _is_channel_disconnected(self) -> bool:
        if self.handle is None:
            return True

        checker = getattr(self.cnt_model, "is_channel_disconnected", None)
        if checker is None:
            return False

        try:
            return bool(checker(self.handle))
        except TypeError:
            return bool(checker())

    def _update_disconnect_overlay(self):
        if not hasattr(self, "_disconnected_overlay"):
            return
        disconnected = self._is_channel_disconnected()
        if disconnected:
            self._disconnected_overlay.setGeometry(self.rect())
            self._disconnected_overlay.show()
            self._disconnected_overlay.raise_()
        else:
            self._disconnected_overlay.hide()

    def _on_use_dbc_toggled(self, checked: bool):
        self.spin_dlc.setEnabled(not checked)
        self.raw_row_widget.setVisible(not checked)
        self.grp_data.setVisible(not checked)
        self.tree.set_allow_edit_raw_data(not checked)
        self.tree.set_message_name_visible(checked)
        if checked:
            self.msg_stack.setCurrentWidget(self.combo_msg)
            if self.combo_msg.current_value() is None and self.combo_msg.count() > 0:
                self.combo_msg.setCurrentIndex(0)
        else:
            self.msg_stack.setCurrentWidget(self.edit_msg)
            # if not self._is_syncing_event:
            #     self.spin_dlc.set_len_value(8)
            #     self._raw_baseline = None
            #     self._rebuild_hex_editors(8)
            #     self._set_hex_data(bytes([0] * 8), default_mask=[True] * 8)
        self._on_message_changed("")

    def _on_event_signal_select(self, selection: SignalFilter):
        self._refresh_buttons()

    # -----------------------------
    # Sender events integration
    # -----------------------------
    def _on_sender_status_changed(self, payload):
        self.send_status_signal.emit(payload)

    def _log_added_state(self, source: str):
        if not self._added:
            LOG.debug("[SEND_PANEL][_added] %s | count=0 | entries=[]", source)
            return

        entries = []
        for can_id, entry in sorted(self._added.items(), key=lambda it: int(it[0])):
            state = getattr(entry, "send_state", SendState.NONE)
            state_name = state.name if hasattr(state, "name") else str(state)
            entries.append(f"0x{int(can_id):X}:{state_name}")

        LOG.debug(
            "[SEND_PANEL][_added] %s | count=%d | entries=[%s]",
            source,
            len(self._added),
            ", ".join(entries),
        )

    @QtCore.Slot(object)
    def _handle_sender_status_on_ui(self, payload):
        LOG.debug(f"[SEND_PANEL][STATUS] payload={payload}")

        status, channel_id, can_id = payload
        self._log_added_state(f"before status={status} can_id={can_id}")
        own_channel_id = self._channel_id_from_handle()
        if own_channel_id is None:
            return
        if channel_id is not None and int(channel_id) != own_channel_id:
            return

        selected_can_id = self._current_selected_can_id()
        selected_can_id = int(selected_can_id) if selected_can_id is not None else None

        if can_id is None:
            if status == "PAUSED_ALL":
                self.btn_pause_all.setText("Resume all")
                for entry in self._added.values():
                    if entry.send_state == SendState.SENDING:
                        entry.send_state = SendState.PAUSED
                self.tree.set_data(self.entries)
                LOG.debug("[SEND_PANEL][STATUS] PAUSED_ALL -> btn_pause_all=Resume all")
            elif status == "RESUMED_ALL":
                self._has_any_send_activity = True
                self.btn_pause_all.setText("Pause all")
                for entry in self._added.values():
                    if entry.send_state in {SendState.PAUSED, SendState.NONE}:
                        entry.send_state = SendState.SENDING
                self.tree.set_data(self.entries)
                LOG.debug("[SEND_PANEL][STATUS] RESUMED_ALL -> btn_pause_all=Pause all")
            elif status == "CHANNEL_UNREGISTERED":
                changed = False
                channel_match = int(channel_id) if channel_id is not None else None
                for entry in self._added.values():
                    try:
                        if channel_match is not None and int(getattr(entry, "channel", -1)) != channel_match:
                            continue
                    except Exception:
                        continue
                    if entry.send_state != SendState.DISCONNETED:
                        entry.send_state = SendState.DISCONNETED
                        changed = True
                if changed:
                    self.tree.set_data(self.entries)
                LOG.debug("[SEND_PANEL][STATUS] CHANNEL_UNREGISTERED -> mark entries DISCONNETED")
            elif status == "CHANNEL_REGISTERED":
                changed = False
                channel_match = int(channel_id) if channel_id is not None else None
                for entry in self._added.values():
                    try:
                        if channel_match is not None and int(getattr(entry, "channel", -1)) != channel_match:
                            continue
                    except Exception:
                        continue
                    if entry.send_state == SendState.DISCONNETED:
                        entry.send_state = SendState.NONE
                        changed = True
                if changed:
                    self.tree.set_data(self.entries)
                LOG.debug("[SEND_PANEL][STATUS] CHANNEL_REGISTERED -> restore entries NONE")
            elif status in {"CLEAR", "CLEARED", "REMOVED_ALL"}:
                if self._added:
                    self._added.clear()
                    self.tree.set_data(self.entries)
                self._send_button_mode = "SEND_FIRST"
                self.btn_send.setText("Send")
                LOG.debug("[SEND_PANEL][STATUS] %s -> cleared all entries", status)
            self._log_added_state(f"after status={status} can_id=None")
            self._sync_pause_all_button_state()
            self._refresh_buttons()
            return

        can_id = int(can_id)
        LOG.debug(
            f"[SEND_PANEL][STATUS] status={status}, can_id={can_id}, "
            f"selected_can_id={selected_can_id}, mode_before={self._send_button_mode}"
        )

        if status in {"ADDED", "UPDATED"}:
            if can_id in self._added:
                self._added[can_id].send_state = SendState.NONE
                self.tree.set_data(self.entries)

            if selected_can_id == can_id:
                self._send_button_mode = "SEND_FIRST"
                self.btn_send.setText("Send")
            LOG.debug("[SEND_PANEL][STATUS] -> mode=SEND_FIRST, btn_send=Send")

        elif status == "RESUMED":
            self._has_any_send_activity = True
            if can_id in self._added:
                self._added[can_id].send_state = SendState.SENDING
                self.tree.set_data(self.entries)
            if selected_can_id == can_id:
                self._send_button_mode = "PAUSE"
                self.btn_send.setText("Pause")
            LOG.debug("[SEND_PANEL][STATUS] -> mode=PAUSE, btn_send=Pause")

        elif status == "PAUSED":
            if can_id in self._added:
                self._added[can_id].send_state = SendState.PAUSED
                self.tree.set_data(self.entries)

            if selected_can_id == can_id:
                self._send_button_mode = "RESUME"
                self.btn_send.setText("Resume")
            LOG.debug("[SEND_PANEL][STATUS] -> mode=RESUME, btn_send=Resume")

        elif status == "REMOVED":
            if can_id in self._added:
                self._added[can_id].send_state = SendState.NONE
            self._added.pop(can_id, None)
            # self._status.pop(can_id, None)
            self.tree.set_data(self.entries)
            self._send_button_mode = "SEND_FIRST"
            self.btn_send.setText("Send")
            LOG.debug("[SEND_PANEL][STATUS] -> mode=SEND_FIRST, btn_send=Send, removed entry")

        else:
            LOG.debug(f"[SEND_PANEL][STATUS] Unhandled status={status}")

        self._log_added_state(f"after status={status} can_id={can_id}")
        LOG.debug(f"[SEND_PANEL][STATUS] mode_after={self._send_button_mode}")
        self._sync_pause_all_button_state()
        self._refresh_buttons()

    # -----------------------------
    # Message list / Combo integration
    # -----------------------------
    def _rebuild_hex_editors(self, data_len: int, data: Optional[bytes] = None, baseline: Optional[bytes] = None):
        # Clear layout items
        while self.grp_data_layout.count():
            item = self.grp_data_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

        self._hex_edits = []
        #self.grp_data.setTitle(f"Data Bytes ({data_len})")
        cols = 16
        rows = max(1, math.ceil(data_len / cols))

        for i in range(data_len):
            e = HexByteLineEdit(self.grp_data)
            if baseline is not None and i < len(baseline):
                e.set_baseline(baseline[i])
            else:
                e.clear_baseline()

            if data is not None and i < len(data):
                e.set_value(data[i], is_default=True)
            else:
                e.set_value(0, is_default=True)
            r = i // cols
            c = i % cols
            self.grp_data_layout.addWidget(e, r, c)
            self._hex_edits.append(e)

        # add spacers so grid looks clean
        for r in range(rows):
            self.grp_data_layout.setRowStretch(r, 0)
        self.grp_data_layout.setColumnStretch(cols, 1)

        # hook edit events
        for e in self._hex_edits:
            e.textEdited.connect(self._refresh_buttons)

    def _set_hex_data(self, data: bytes, default_mask: Optional[List[bool]] = None, baseline: Optional[bytes] = None):
        for i, e in enumerate(self._hex_edits):
            if baseline is not None and i < len(baseline):
                e.set_baseline(baseline[i])
            elif baseline is not None:
                e.clear_baseline()
            v = data[i] if i < len(data) else 0
            is_default = False
            if default_mask is not None and i < len(default_mask):
                is_default = default_mask[i]
            e.set_value(v, is_default=is_default)
    # -----------------------------
    # Event handlers
    # -----------------------------

    def _get_default_mask(self) -> List[bool]:
        """
        True  = byte is still default (not user-edited)
        False = user modified
        """
        mask = []
        for e in self._hex_edits:
            mask.append(e._is_default_value)
        return mask

    def _on_dlc_changed(self, dlc: int):
        prev_data = hex_raw_to_bytes(self.get_hex_raw_string())
        prev_default_mask = self._get_default_mask()
        data_len = self.candb.get_length_from_dlc(dlc)
        # Trim or extend data safely
        new_data = prev_data[:data_len]
        new_mask = prev_default_mask[:data_len]

        # Extend with DEFAULT zeros if DLC increased
        while len(new_data) < data_len:
            new_data += b"\x00"
            new_mask.append(True)  # <-- KEY LINE

        baseline = self._raw_baseline
        if baseline is not None:
            baseline = baseline[:data_len]

        self._rebuild_hex_editors(
            data_len,
            data=new_data,
            baseline=baseline
        )

        # Restore default/user intent state explicitly
        for i, e in enumerate(self._hex_edits):
            e._is_default_value = new_mask[i]
            e._apply_color()
        self._refresh_buttons()

    def _on_message_changed(self, _t: str):
        cid = self._current_selected_can_id()
        if cid is None:
            self._refresh_buttons()
            return

        cid = int(cid)
        existing = self._added.get(cid)
        if existing is not None:
            try:
                cycle_ms = max(1, int(float(existing.timediff or 0.0) * 1000.0))
                self.spin_cycle.setValue(cycle_ms)
            except Exception:
                pass

            if hasattr(self, "combo_channel"):
                selected_name = self._channel_name_for_channel_value(getattr(existing, "channel", None))
                if selected_name:
                    idx = self.combo_channel.findText(str(selected_name), Qt.MatchExactly)
                    if idx >= 0:
                        self.combo_channel.setCurrentIndex(idx)

            data_len = max(0, int(existing.data_len or 0))
            self.spin_dlc.set_len_value(data_len)
            payload = hex_raw_to_bytes(str(existing.raw_data or ""))
            payload = payload[:data_len].ljust(data_len, b"\x00")
            self._rebuild_hex_editors(data_len)
            self._set_hex_data(payload, default_mask=[True] * data_len)
            self._refresh_buttons()
            return

        if self.chk_use_dbc.isChecked():
            can_id = self.combo_msg.current_value()
            if can_id is None and self.combo_msg.count() > 0:
                self.combo_msg.setCurrentIndex(0)
                can_id = self.combo_msg.current_value()
            if can_id is not None:
                msg = self.candb.get_message(can_id)
                if msg.cycle_time is not None:
                    self.spin_cycle.setValue(int(msg.cycle_time))
                else:
                    self.spin_cycle.setValue(0)
                self.spin_dlc.set_len_value(msg.length)
            self._rebuild_hex_editors(self.spin_dlc.current_len_value())
            self._set_hex_data(
                bytes([0] * self.spin_dlc.current_len_value()),
                default_mask=[True] * self.spin_dlc.current_len_value(),
            )

        self._refresh_buttons()

    def _on_raw_bytes_debounced(self):
        data = self.edit_raw_bytes.current_value()
        if not data:
            self._raw_baseline = None
            if not self.chk_use_dbc.isChecked():
                self.spin_dlc.set_len_value(8)
                self._rebuild_hex_editors(8)
                self._set_hex_data(bytes([0] * 8), default_mask=[True] * 8)
                self._refresh_buttons()
            return
        self.spin_dlc.set_len_value(len(data))
        padded = data.ljust(len(data), b"\x00")
        self._raw_baseline = padded
        self._rebuild_hex_editors(len(data), data=padded, baseline=padded)
        self._refresh_buttons()

    def get_hex_raw_string(self) -> str:
        """
        Read current values from self._hex_edits (List[HexByteLineEdit])
        and return CANLogLine-compatible raw hex string.

        Example:
            "00 1A FF"
        """
        parts: list[str] = []

        for e in self._hex_edits:
            v = e.value()          # HexByteLineEdit.value() -> Optional[int]
            if v is None:
                parts.append("00")
            else:
                parts.append(f"{int(v):02X}")

        return " ".join(parts)

    @property
    def entries(self) -> List[CANLogPlay]:
        return list(self._added.values())

    def _on_add_or_update_clicked(self):
        LOG.debug("_on_add_or_update_clicked")
        self._log_added_state("button Add/Update pressed (before request)")
        cid = self._current_selected_can_id()
        if cid is None:
            return
        cid = int(cid)
        entry = self._build_line_from_ui(cid)
        if cid in self._added:
            entry.send_state = getattr(self._added[cid], "send_state", SendState.NONE)
        else:
            entry.send_state = SendState.NONE

        periodic_s = float(entry.timediff or 0.0)
        if periodic_s <= 0:
            LOG.warning("[SEND_PANEL][ADD] invalid periodic for can_id=%s", cid)
            return

        self._added[cid] = entry
        self.tree.set_data(self.entries)

        self.sender.send_msg_loop_from_line(entry, initial_periodic=periodic_s)

        # Keep current values as clean baseline after Add/Update.
        # This ensures Update is disabled until user changes something again.
        self._raw_baseline = None
        self.edit_raw_bytes.setText("")

        current_data = hex_raw_to_bytes(entry.raw_data or "")
        self._set_hex_data(
            current_data,
            default_mask=[True] * self.spin_dlc.current_len_value(),
        )
        self._log_added_state("button Add/Update pressed (after request)")
        self._refresh_buttons()

    def _on_remove_clicked(self):
        LOG.debug("_on_remove_clicked")
        self._log_added_state("button Remove pressed (before request)")
        cid = self._current_selected_can_id()
        if cid is None:
            return
        cid = int(cid)
        channel_id = self._channel_id_from_handle()
        if channel_id is None:
            LOG.warning("[SEND_PANEL][REMOVE] invalid handle for channel_id, can_id=%s", cid)
            return
        LOG.debug(f"[SEND_PANEL][REMOVE] request remove for can_id={cid}")
        self.sender.remove_msg(channel_id, cid)
        self._log_added_state("button Remove pressed (after request, waiting status)")

    def _on_send_pause_resume_clicked(self):
        LOG.debug("_on_send_pause_resume_clicked")
        cid = self._current_selected_can_id()
        if cid is None:
            return
        cid = int(cid)
        channel_id = self._channel_id_from_handle()
        if channel_id is None:
            LOG.warning("[SEND_PANEL][SEND] invalid handle for channel_id, can_id=%s", cid)
            return
        if cid not in self._added:
            return
        entry = self._added[cid]
        if getattr(entry, "send_state", SendState.NONE) == SendState.DISCONNETED:
            LOG.debug("[SEND_PANEL][SEND] blocked action for disconnected entry can_id=%s", cid)
            return

        cycle_ms = float(self.spin_cycle.value())
        periodic_s = cycle_ms / 1000.0

        # Decide action based on current button mode
        if self._send_button_mode == "SEND_FIRST":
            if cycle_ms < 1:
                self.sender.send_once_from_entry(entry)
                return
            self.sender.resume(channel_id, cid)
            return

        if self._send_button_mode == "PAUSE":
            self.sender.stop(channel_id, cid)
            return

        if self._send_button_mode == "RESUME":
            self.sender.resume(channel_id, cid)
            return

    def _on_pause_all_clicked(self):
        LOG.debug("_on_pause_all_clicked")
        channel_id = self._channel_id_from_handle()
        if channel_id is None:
            LOG.warning("[SEND_PANEL][ALL] invalid handle for channel_id")
            return
        if self._send_all_button_mode == "SEND_ALL":
            self.sender.resume(channel_id, None)
            return

        if self._send_all_button_mode == "PAUSE_ALL":
            self.sender.stop(channel_id, None)
            return

        self.sender.resume(channel_id, None)

    def _on_remove_all_clicked(self):
        LOG.debug("_on_remove_all_clicked")
        if len(self._added) < 2:
            return

        channel_id = self._channel_id_from_handle()
        if channel_id is None:
            LOG.warning("[SEND_PANEL][CLEAR] invalid handle for channel_id")
            return

        clear_fn = getattr(self.sender, "clear", None)
        if callable(clear_fn):
            try:
                clear_fn(channel_id)
                return
            except TypeError:
                clear_fn()
                return

        clear_all_fn = getattr(self.sender, "clear_all", None)
        if callable(clear_all_fn):
            clear_all_fn(channel_id)
            return

        remove_all_fn = getattr(self.sender, "remove_all", None)
        if callable(remove_all_fn):
            remove_all_fn(channel_id)
            return

        self.sender.remove_msg(channel_id, None)

    def _sync_pause_all_button_state(self):
        has_entries = bool(self._added)
        sendable_entries = [
            entry
            for entry in self._added.values()
            if getattr(entry, "send_state", SendState.NONE) != SendState.DISCONNETED
        ]
        any_sending = any(
            getattr(entry, "send_state", SendState.NONE) == SendState.SENDING
            for entry in sendable_entries
        )
        any_paused = any(
            getattr(entry, "send_state", SendState.NONE) == SendState.PAUSED
            for entry in sendable_entries
        )

        self.btn_pause_all.setEnabled(bool(sendable_entries))
        self.btn_remove_all.setEnabled(len(self._added) >= 2)
        if not has_entries:
            self._send_all_button_mode = "SEND_ALL"
            self._has_any_send_activity = False
            self.btn_pause_all.setText("Send all")
            return

        if not sendable_entries:
            self._send_all_button_mode = "SEND_ALL"
            self.btn_pause_all.setText("Send all")
            return

        if any_sending:
            self._send_all_button_mode = "PAUSE_ALL"
            self.btn_pause_all.setText("Pause all")
            return

        if any_paused:
            self._send_all_button_mode = "RESUME_ALL"
            self.btn_pause_all.setText("Resume all")
            return

        self._send_all_button_mode = "SEND_ALL"
        self.btn_pause_all.setText("Send all")

    # -----------------------------
    # State / dirty / buttons
    # -----------------------------
    def _current_selected_can_id(self) -> Optional[int]:
        if self.chk_use_dbc.isChecked():
            return self.combo_msg.current_value()
        return self.edit_msg.current_value()

    def _channel_id_from_handle(self) -> Optional[int]:
        combo = getattr(self, "combo_channel", None)
        if combo is not None:
            selected_name = combo.currentText().strip()
            if selected_name:
                for handle in self.cnt_model.acquired_channels.keys():
                    try:
                        info = self.cnt_model.get_channel_info(handle)
                        name = str(getattr(info, "name", "") or "").strip()
                        if name == selected_name:
                            return int(handle.channel_idx)
                    except Exception:
                        continue
        if self.handle is None:
            return None
        return int(self.handle.channel_idx)

    def _channel_name_for_channel_value(self, channel_value) -> Optional[str]:
        if channel_value is None:
            return None

        target_raw = str(channel_value).strip()
        if not target_raw:
            return None

        target_int = None
        try:
            target_int = int(target_raw)
        except Exception:
            target_int = None

        for handle in self.cnt_model.acquired_channels.keys():
            try:
                info = self.cnt_model.get_channel_info(handle)
                name = str(getattr(info, "name", "") or "").strip()
                if name and name == target_raw:
                    return name

                if target_int is not None:
                    if int(getattr(handle, "channel_idx", -1)) == target_int:
                        return name or None
                    if int(getattr(handle, "native_handle", -1)) == target_int:
                        return name or None
            except Exception:
                continue

        return None

    def _refresh_buttons(self):
        cid = self._current_selected_can_id()
        if cid is None:
            self.btn_add.setText("Add")
            self.btn_add.setEnabled(False)
            self.btn_remove.setEnabled(False)
            self.btn_send.setEnabled(False)
            return

        cid = int(cid)
        existing = self._added.get(cid)

        if existing is None:
            self.btn_add.setText("Add")
            self.btn_add.setEnabled(True)
            self.btn_remove.setEnabled(False)
            self.btn_send.setEnabled(False)
            self._send_button_mode = "SEND_FIRST"
            self.btn_send.setText("Send")
            return

        self.btn_add.setText("Update")
        current_line = self._build_line_from_ui(cid)
        is_dirty = self._line_differs(current_line, existing)
        self.btn_add.setEnabled(is_dirty)
        self.btn_remove.setEnabled(True)
        state = getattr(existing, "send_state", SendState.NONE)
        self.btn_send.setEnabled(state != SendState.DISCONNETED)
        if state == SendState.SENDING:
            self._send_button_mode = "PAUSE"
            self.btn_send.setText("Pause")
        elif state == SendState.PAUSED:
            self._send_button_mode = "RESUME"
            self.btn_send.setText("Resume")
        else:
            self._send_button_mode = "SEND_FIRST"
            self.btn_send.setText("Send")

    def _line_differs(self, a: CANLogPlay, b: CANLogPlay) -> bool:
        return (
            float(a.timediff or 0.0) != float(b.timediff or 0.0)
            or str(a.channel or "") != str(b.channel or "")
            or int(a.data_len or 0) != int(b.data_len or 0)
            or str(a.raw_data or "").strip().upper() != str(b.raw_data or "").strip().upper()
        )

    def _build_line_from_ui(self, can_id: int) -> CANLogPlay:
        cycle_ms = float(self.spin_cycle.value())
        channel_name = self.combo_channel.currentText().strip()
        # dlc = int(self.spin_dlc.value())
        # data_len = self.candb.get_length_from_dlc(dlc)
        return CANLogPlay(
            _timediff=cycle_ms / 1000,
            channel=channel_name,
            can_id=can_id,
            direction="Tx",
            data_len=self.spin_dlc.current_len_value(),
            raw_data=self.get_hex_raw_string(),
        )

    def _load_line_to_ui(self, line: CANLogLine):
        cycle_ms = int((line.timediff or 0.0) * 1000)
        self.spin_cycle.setValue(cycle_ms)
        data_len = int(line.data_len or 0)
        dlc = self.candb.get_dlc_from_length(data_len)
        self.spin_dlc.setValue(dlc)
        self._rebuild_hex_editors(self.candb.get_length_from_dlc(dlc))
        data = hex_raw_to_bytes(line.raw_data or "")
        self._set_hex_data(data, default_mask=[True] * len(data))

def main():
    setup_logger(env="PRD", backup_count=30)

    app = QApplication(sys.argv)

    win = QWidget()
    win.setWindowTitle("CAN Test Panel (PySide6)")
    win.resize(500, 500)

    layout = QVBoxLayout(win)

    # ---------------- Sample log lines ----------------
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

   # ---------------- Test data ----------------
    parser = LogParser()
    parsed_lines = [parser._various_parse_line_test(l, i) for i, l in enumerate(test_lines)]
    model = CANDBManager()
    model.load_database(
        "/home/gnar911/Desktop/20260122 APP WEBSITE - CAN ANALYZER 3.0 CBCM TOOL APP ARC/CAN_Analyzer_MVVM/Database/EEA10_CANFD_R00c_withADAS_Main.dbc")

    # ---------------- Connection Manager ----------------
    m = CANConnectManager(CANDeviceType.SOCKETCAN)
    m.start_scan()

    state = {
        "handle": None,
        "monitor": None,
        "monitors": {},
        "send_idx": 0,
        "periodic_idx": 0,
    }

    # ---------------- Button Actions ----------------

    def test_acquire_chnl():
        if not m.available_channels:
            QMessageBox.warning(win, "Warning", "No available channels")
            return

        handle, channel = next(iter(m.available_channels.items()))

        if m.acquire(handle):
            state["handle"] = handle
            print(f"Acquired: {channel.name}")

            # Create monitor panel
            monitor = CustomSendMessagePanel(
                parent=win,
                candb=model,
                cnt_model=m,
                handle=handle
            )

            layout.addWidget(monitor)
            state["monitor"] = monitor
            state["monitors"][handle] = monitor
        else:
            QMessageBox.warning(win, "Warning", "Acquire failed")

    def test_release_chnl():
        handle = state["handle"]
        if handle is None:
            # If no active handle in state, release any remaining acquired channel.
            acquired = list(m.acquired_channels.keys())
            if not acquired:
                return
            handle = acquired[0]

        m.release(handle)
        print("Released channel")

        if state["handle"] == handle:
            state["handle"] = None

        # Destroy monitor panel safely (for the released handle)
        monitor = state.get("monitors", {}).pop(handle, None)
        if monitor:
            monitor.setParent(None)
            monitor.deleteLater()
            if state.get("monitor") is monitor:
                state["monitor"] = None

    def test_send_once():
        if state["handle"] is None:
            print("No channel acquired")
            return

        sender = m.get_sender()
        if not sender:
            return

        sender.send_once_from_entry(parsed_lines[0])
        print("Send once")

    PERIODIC_SEQ_MS = [10, 9, 8, 7, 6, 5]

    def test_send_loop():
        if state["handle"] is None:
            print("No channel acquired")
            return

        sender = m.get_sender()
        if not sender:
            return

        # ---- rotate log line ----
        line_idx = state["send_idx"] % len(parsed_lines)
        state["send_idx"] += 1


        per_idx = state["periodic_idx"] % len(PERIODIC_SEQ_MS)
        state["periodic_idx"] += 1

        periodic_ms = PERIODIC_SEQ_MS[per_idx]
        periodic_sec = periodic_ms / 1000.0

        print(f"Send loop started | periodic={periodic_ms} ms")

        sender.send_msg_loop_from_line(
            parsed_lines[line_idx],
            periodic_sec
        )

        print(
            f"Send loop started | "
            f"line={line_idx}, "
            f"periodic={periodic_ms} ms"
        )

    # ---------------- UI Buttons ----------------

    btn_acquire = QPushButton("Acquire Channel")
    btn_release = QPushButton("Release Channel")
    # btn_send_once = QPushButton("Send Once")
    # btn_send_loop = QPushButton("Send Loop")

    btn_acquire.clicked.connect(test_acquire_chnl)
    btn_release.clicked.connect(test_release_chnl)
    # btn_send_once.clicked.connect(test_send_once)
    # btn_send_loop.clicked.connect(test_send_loop)

    layout.addWidget(btn_acquire)
    layout.addWidget(btn_release)
    # layout.addWidget(btn_send_once)
    # layout.addWidget(btn_send_loop)
    layout.addStretch(1)

    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()