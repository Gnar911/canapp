from PySide6.QtWidgets import (
    QWidget, QLabel, QSpinBox, QVBoxLayout, QHBoxLayout)
from PySide6.QtCore import Qt
from can_sdk.logger_setup import LOG, setup_logger
from can_sdk.data_object import SignalFilter
from ultility import wrap_text_by_word_boundary
from can_sdk.dbc_manager import CANDBManager

from dataclasses import dataclass
from collections import defaultdict
from typing import Dict, List, Any, Optional
from PySide6.QtCore import Qt, QPoint, QObject, Signal, Slot
from PySide6.QtWidgets import (
    QGroupBox, QWidget, QVBoxLayout, QGridLayout, QHBoxLayout,
    QPushButton, QTreeWidget, QTreeWidgetItem, QMenu, QMessageBox)
from can_sdk.canlog_viewmodel import LogContextManager, State, FilterMode, LogContext  
from can_sdk.data_object import SignalFilter
# from ui_sdk.components.signal_graph import Signal_Graph_Drawer, np
from ui_sdk.components.matplot_warpper import *
from ultility import *
import threading
from can_sdk.logger_setup import LOG, setup_logger
from can_sdk.dbc_manager import CANDBManager
from ui_sdk.components.pyqt.SigFilterTable import FilterSignalTable, FilterSignalViewModel

# ------------------------------------------------------------
# Worker signals (thread-safe callback into UI)
# ------------------------------------------------------------
class _WorkerSignals(QObject):
    finished = Signal(dict, dict, list)   # timestamps, signals_data, static_data
    error = Signal(str)


# ------------------------------------------------------------
# SignalFilterPanel (Qt port)
# ------------------------------------------------------------
class SignalFilterPanel(QGroupBox):
    def __init__(self, parent, 
                 model: CANDBManager,
                 model1: LogContextManager):
        super().__init__("", parent)
        self.candb = model
        self.ctx_model = model1
        self.last_position_log_show: int = 0
        self.signal_graph: Dict[int, Any] = {}
        self.signal_graph_showed: Dict[int, List[str]] = {}
        self.marked_color_sigs = []
        self.pretreeid = 0

        self._last_mode = None

        self._build_ui()
        self._bind_events()

    # ---- UI ----
    def _build_ui(self):
        # row 1 buttons
        self.btn_add_filter_sig = QPushButton("Add")
        self.btn_remove_filter_sig = QPushButton("Remove")
        self.btn_remove_all_filter_sig = QPushButton("Clear")

        # table
        self.lb_filter_signal_ = FilterSignalTable(self, self.candb, self.ctx_model)

        # view buttons
        self.btn_view_filtering_sig = QPushButton("View Filtered Signal")
        self.btn_view_filter_sig_change = QPushButton("View Filter Changed Only")
        self.btn_view_draw_sig = QPushButton("View Signal Graph")

        # root layout
        self._root_layout = QVBoxLayout(self)
        self._root_layout.setContentsMargins(0, 0, 0, 0)
        self._root_layout.setSpacing(6)

        # initial layout
        self._apply_layout("portrait")

    def _clear_layout(self, layout: QVBoxLayout | QHBoxLayout):
        while layout.count():
            item = layout.takeAt(0)
            if item.layout():
                self._clear_layout(item.layout())
            # widgets are kept; no deletion

    def _apply_layout(self, mode: str):
        self._clear_layout(self._root_layout)

        if mode == "landscape":
            row = QHBoxLayout()
            row.setAlignment(Qt.AlignLeft | Qt.AlignTop)

            row.addWidget(self.lb_filter_signal_, 1)

            btn_col = QVBoxLayout()
            btn_col.setAlignment(Qt.AlignLeft | Qt.AlignTop)
            btn_col.addWidget(self.btn_add_filter_sig)
            btn_col.addWidget(self.btn_remove_filter_sig)
            btn_col.addWidget(self.btn_remove_all_filter_sig)
            btn_col.addWidget(self.btn_view_filtering_sig)
            btn_col.addWidget(self.btn_view_filter_sig_change)
            btn_col.addWidget(self.btn_view_draw_sig)
            btn_col.addStretch(1)

            row.addLayout(btn_col)
            self._root_layout.addLayout(row, 1)
        else:
            btn_row = QHBoxLayout()
            btn_row.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            btn_row.addWidget(self.btn_add_filter_sig)
            btn_row.addWidget(self.btn_remove_filter_sig)
            btn_row.addWidget(self.btn_remove_all_filter_sig)

            self._root_layout.addLayout(btn_row)
            self._root_layout.addWidget(self.lb_filter_signal_, 1)
            self._root_layout.addWidget(self.btn_view_filtering_sig)
            self._root_layout.addWidget(self.btn_view_filter_sig_change)
            self._root_layout.addWidget(self.btn_view_draw_sig)

        self._last_mode = mode

    def resizeEvent(self, event):
        super().resizeEvent(event)

        w = self.width()
        h = self.height()

        if w > h * 1.2:
            mode = "landscape"
        else:
            mode = "portrait"

        if mode != self._last_mode:
            self._apply_layout(mode)

    def _bind_events(self):
        #self.btn_view_draw_sig.clicked.connect(self.on_btn_draw_signal_clicked)
        self.btn_view_filtering_sig.clicked.connect(self.on_btn_view_filtering_sig_clicked)
        self.btn_view_filter_sig_change.clicked.connect(self.on_btn_view_filter_sig_change_clicked)
        self.btn_add_filter_sig.clicked.connect(self.on_btn_add_filter_sig_clicked)
        self.btn_remove_filter_sig.clicked.connect(self.on_btn_remove_filter_sig_clicked)
        self.btn_remove_all_filter_sig.clicked.connect(self.on_btn_remove_all_filter_sig_clicked)

    @property
    def tree_table(self) -> FilterSignalTable:
        return self.lb_filter_signal_

    @Slot()
    def on_btn_view_filtering_sig_clicked(self):
        ctx = self.ctx_model.cur_ctx
        if ctx is None:
            return
        LOG.debug(f"Click view filtering sig button: {ctx.filter_state}")

        if ctx.filter_state == FilterMode.FILTERSIG:
            ctx.on_all_messages()
            return

        items = self.tree_table.current_selected_items()
        if len(items) == 0:
            return

        ctx.on_filter_signals_by_value(items)
        return True

    @Slot()
    def on_btn_view_filter_sig_change_clicked(self):
        LOG.debug("Click view filtering sig change button")
        QMessageBox.critical(self, "Warning", "This feature is unsupported on this version")

    @Slot()
    def on_btn_add_filter_sig_clicked(self):
        LOG.debug("Click add sig button")
        if not self.candb.cur_sig:
            LOG.debug("No selected target")
            return
        
        if not self.candb.selected_signal_info:
            LOG.debug("No selected signal")
            QMessageBox.critical(self, "Warning", "Please select a signal")
            return
        
        self.lb_filter_signal_.add_item(self.candb.cur_sig)

    @Slot()
    def on_btn_remove_filter_sig_clicked(self):
        LOG.debug("Click remove sig button")
        if not self.candb.cur_sig:
            LOG.debug("No selected target")
            return
        
        if not self.candb.selected_signal_info:
            LOG.debug("No selected signal")
            QMessageBox.critical(self, "Warning", "Please select a signal")
            return

        self.lb_filter_signal_.remove_selected()

    @Slot()
    def on_btn_remove_all_filter_sig_clicked(self):
        res = QMessageBox.question(
            self,
            "Confirm",
            "Are you sure you want to remove all filtered signals?",
            QMessageBox.Yes | QMessageBox.Cancel,
            QMessageBox.Cancel
        )

        if res == QMessageBox.Yes:
            self.lb_filter_signal_.remove_all()
            
class InspectorPanel(QWidget):
    def __init__(self, parent, model: CANDBManager, *args, **kwargs):
        super().__init__(parent)
        self.my_model = model
        self._add_widget()
        self.event_binding()

    def event_binding(self):
        self._spbrawvalue.valueChanged.connect(self.on_raw_value_input_changed)
        self._spbrawvalue.editingFinished.connect(self.on_focus_out)

    @property
    def spbrawvalue(self):
        return self._spbrawvalue
    
    @property
    def msg_name_var(self):
        return self._msg_name_var
    
    @property
    def sig_name_var(self):
        return self._sig_name_var
    
    @property
    def value_var(self):
        return self._value_var
    
    @property
    def raw_value_var(self):
        return self._raw_value_var
    
    @property
    def unit_var(self):
        return self._unit_var

    def _add_widget(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        # Message Name row
        msg_layout = QHBoxLayout()
        msg_label = QLabel("Message Name:")
        self._msg_name_label = QLabel("--")
        msg_layout.addWidget(msg_label)
        msg_layout.addWidget(self._msg_name_label)
        msg_layout.addStretch()
        main_layout.addLayout(msg_layout)

        # Signal Name row
        sig_layout = QHBoxLayout()
        sig_label = QLabel("Signal Name:")
        self._sig_name_label = QLabel("--")
        sig_layout.addWidget(sig_label)
        sig_layout.addWidget(self._sig_name_label)
        sig_layout.addStretch()
        main_layout.addLayout(sig_layout)

        # Raw Value row
        raw_layout = QHBoxLayout()
        raw_label = QLabel("Raw Value:")
        self._spbrawvalue = QSpinBox()
        self._spbrawvalue.setMinimum(0)
        self._spbrawvalue.setMaximum(0)
        self._spbrawvalue.setStyleSheet("color: gray;")
        # self._spbrawvalue.setKeyboardTracking(True)
        # self._spbrawvalue.setFocusPolicy(Qt.StrongFocus)
        raw_layout.addWidget(raw_label)
        raw_layout.addWidget(self._spbrawvalue)
        raw_layout.addStretch()
        main_layout.addLayout(raw_layout)

        # Value row
        value_layout = QHBoxLayout()
        value_label = QLabel("Value:")
        self._value_label = QLabel("--")
        self._value_label.setWordWrap(True)
        value_layout.addWidget(value_label)
        value_layout.addWidget(self._value_label)
        value_layout.addStretch()
        main_layout.addLayout(value_layout)

        # Unit row
        unit_layout = QHBoxLayout()
        unit_label = QLabel("Unit:")
        self._unit_label = QLabel("--")
        unit_layout.addWidget(unit_label)
        unit_layout.addWidget(self._unit_label)
        unit_layout.addStretch()
        main_layout.addLayout(unit_layout)

        # Message info
        self.lb_msg_info = ReadOnlyListWidget()
        self.lb_msg_info.setMinimumWidth(0)
        grid.addWidget(QLabel("Message Information"), 3, 0)
        grid.addWidget(self.lb_msg_info, 4, 0)

        # Signal info
        self.lb_signal_info = ReadOnlyListWidget()
        self.lb_signal_info.setMinimumWidth(0)
        grid.addWidget(QLabel("Signal Information"), 3, 1)
        grid.addWidget(self.lb_signal_info, 4, 1)


        # Add stretch at the end
        main_layout.addStretch()

        # Store text values
        self._msg_name_var = "--"
        self._sig_name_var = "--"
        self._raw_value_var = "--"
        self._value_var = "--"
        self._unit_var = "--"

    def on_focus_in(self, event):
        self.focus_in_value_input_box()

    def on_focus_out(self, event=None):
        self.focus_out_value_input_box()

    def focus_in_value_input_box(self):
        self._spbrawvalue.setStyleSheet("color: black;")

    def focus_out_value_input_box(self):
        if self._spbrawvalue.text() == "":
            self._spbrawvalue.setStyleSheet("color: gray;")

    def reset_value_input_box(self):
        if self.my_model.rawvalue:
            self._spbrawvalue.setValue(int(self.my_model.rawvalue))
            self._spbrawvalue.setStyleSheet("color: black;")
        else:
            self._spbrawvalue.setValue(0)
            self._spbrawvalue.setStyleSheet("color: gray;")

    def on_raw_value_input_changed(self, value):
        if self._spbrawvalue.text() == "" or value == 0:
            self.my_model.rawvalue = None
            return
        self.my_model.rawvalue = int(value)
        self.update_signal_metadata_display()

    def reset_metadata_state1(self):
        self._value_var = "--"
        self._value_label.setText(self._value_var)
        self._raw_value_var = "--"
        # self._raw_value_label.setText(self._raw_value_var)

    def reset_metadata_state2(self):
        self._sig_name_var = "--"
        self._sig_name_label.setText(self._sig_name_var)
        self._unit_var = "--"
        self._unit_label.setText(self._unit_var)
    
    def update_signal_metadata_display(self, data: SignalFilter = None):
        if not data or not data.msg_info:
            self._msg_name_var = "--"
            self._msg_name_label.setText(self._msg_name_var)
            self._value_var = "--"
            self._value_label.setText(self._value_var)
            self._raw_value_var = "--"
            # self._raw_value_label.setText(self._raw_value_var)
            self._sig_name_var = "--"
            self._sig_name_label.setText(self._sig_name_var)
            self._unit_var = "--"
            self._unit_label.setText(self._unit_var)
            return
        
        self._msg_name_var = data.msg_info.name
        self._msg_name_label.setText(self._msg_name_var)
        
        if not data.signal_info:
            self._sig_name_var = "--"
            self._sig_name_label.setText(self._sig_name_var)
            self._unit_var = "--"
            self._unit_label.setText(self._unit_var)
            self._value_var = "--"
            self._value_label.setText(self._value_var)
            self._raw_value_var = "--"
            # self._raw_value_label.setText(self._raw_value_var)
            return
        
        self._sig_name_var = data.sig_name
        self._sig_name_label.setText(self._sig_name_var)
        (min_value, max_value) = data.min_max
        self._spbrawvalue.setMinimum(min_value)
        self._spbrawvalue.setMaximum(max_value)
        self._unit_var = data.unit
        self._unit_label.setText(self._unit_var)

        if data.rawvalue is None:
            self._value_var = "--"
            self._value_label.setText(self._value_var)
            self._raw_value_var = "--"
            # self._raw_value_label.setText(self._raw_value_var)
            return
        
        raw_value = data.rawvalue
        raw_value = max(min_value, min(raw_value, max_value))
        LOG.debug(raw_value)
        self._raw_value_var = str(raw_value)
        # self._raw_value_label.setText(self._raw_value_var)
        self._spbrawvalue.setValue(raw_value)
    
        value = data.value
        wrapped_text_value = wrap_text_by_word_boundary(str(value), 25)
        self._value_var = wrapped_text_value
        self._value_label.setText(self._value_var)

    def update_message_info(self):
        self.lb_msg_info.clear()
        msg = self.my_model.selected_message_info
        if not msg:
            return

        items = []
        # Identity
        items += [
            f"- CAN ID: 0x{msg.frame_id:X} ({msg.frame_id})",
            f"- Frame Format: {'Extended (29-bit)' if msg.is_extended_frame else 'Standard (11-bit)'}",
            f"- Protocol: {msg.protocol or 'Not defined'}",
            f"- Bus Name: {msg.bus_name or 'Not defined'}",
        ]

        # Definition
        items += [
            f"- Message Name: {msg.name}",
            f"- DLC / Length: {msg.length} bytes",
            f"- CAN Type: {'CAN-FD' if msg.is_fd else 'Classic CAN'}",
            f"- Container Message: {'Yes' if msg.is_container else 'No'}",
            f"- Unused Bit Pattern: 0x{msg.unused_bit_pattern:02X}",
        ]

        # Timing & Transmission
        items += [
            f"- Cycle Time: {str(msg.cycle_time) + ' ms' if msg.cycle_time is not None else 'Not defined'}",
            f"- Send Type: {msg.send_type or 'Not defined'}",
            f"- Senders: {', '.join(msg.senders) if msg.senders else 'Not defined'}",
            f"- Receivers: {', '.join(sorted(msg.receivers)) if msg.receivers else 'Not defined'}",
        ]

        # Payload & Signals
        items += [
            f"- Signals Count: {len(msg.signals)}",
            f"- Multiplexed: {'Yes' if msg.is_multiplexed() else 'No'}",
            f"- Signal Groups: {len(msg.signal_groups) if msg.signal_groups else 0}",
        ]

        # Container details
        if msg.is_container:
            items += [
                f"- Container Header ID: 0x{msg.header_id:X}" if msg.header_id is not None else "- Container Header ID: Not defined",
                f"- Header Byte Order: {msg.header_byte_order}",
                "- Contained Messages:",
            ]
            for cmsg in msg.contained_messages or []:
                items.append(f"  - {cmsg.name}")

        # Documentation
        items += [
            f"- Comment: {msg.comment or 'Not defined'}",
            f"- DBC Metadata: {'Present' if msg.dbc else 'None'}",
            f"- AUTOSAR Metadata: {'Present' if msg.autosar else 'None'}",
        ]

        self.lb_msg_info.addItems(items)

    def update_signal_info(self):
        self.lb_signal_info.clear()
        sig = self.my_model.selected_signal_info
        if not sig:
            return

        items = []

        # Identity & Role
        items += [
            f"- Signal Name: {sig.name}",
            f"- Role: {'Multiplexer' if sig.is_multiplexer else 'Multiplexed' if sig.multiplexer_signal else 'Normal'}",
            f"- Multiplexer Signal: {sig.multiplexer_signal or 'Not defined'}",
            f"- Multiplexer IDs: {sig.multiplexer_ids if sig.multiplexer_ids else 'Not defined'}",
            f"- J1939 SPN: {sig.spn if sig.spn is not None else 'Not defined'}",
        ]

        # Bit Layout
        items += [
            f"- Start Bit: {sig.start}",
            f"- Length: {sig.length} bits",
            f"- Byte Order: {'Little Endian (Intel)' if sig.byte_order == 'little_endian' else 'Big Endian (Motorola)'}",
            f"- Signedness: {'Signed' if sig.is_signed else 'Unsigned'}",
        ]

        # Scaling & Interpretation
        items += [
            f"- Scale (Factor): {sig.scale}",
            f"- Offset: {sig.offset}",
            f"- Value Type: {'Float' if sig.is_float else 'Integer'}",
            f"- Unit: {sig.unit or 'Not defined'}",
        ]

        # Validity & Ranges
        items += [
            f"- Minimum: {sig.minimum if sig.minimum is not None else 'Not defined'}",
            f"- Maximum: {sig.maximum if sig.maximum is not None else 'Not defined'}",
            f"- Initial Raw Value: {sig.raw_initial if sig.raw_initial is not None else 'Not defined'}",
            f"- Initial Physical Value: {sig.initial if sig.initial is not None else 'Not defined'}",
            f"- Invalid Raw Value: {sig.raw_invalid if sig.raw_invalid is not None else 'Not defined'}",
            f"- Invalid Physical Value: {sig.invalid if sig.invalid is not None else 'Not defined'}",
        ]

        # Choices / Enums
        if sig.choices:
            items.append("Value Table:")
            for raw, text in sig.choices.items():
                items.append(f"  {raw} → {text}")
        else:
            items.append("Value Table: None")

        # Metadata
        items += [
            f"- Receivers: {', '.join(sig.receivers) if sig.receivers else 'Not defined'}",
            f"- DBC Metadata: {'Present' if sig.dbc else 'None'}",
            f"- Comment: {sig.comment or 'Not defined'}",
        ]

        self.lb_signal_info.addItems(items)

if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout
    from PySide6.QtCore import Qt

    setup_logger(env="DEV", backup_count=30)
    app = QApplication(sys.argv)
    win = QWidget()
    win.setWindowTitle("TreeLogTable Test")
    layout = QVBoxLayout(win)

    candb = CANDBManager()
    candb.load_database(
        "/home/gnar911/Desktop/20260122 APP WEBSITE - CAN ANALYZER 3.0 CBCM TOOL APP ARC/CAN_Analyzer_MVVM/Database/EEA10_CANFD_R00c_withADAS_Main.dbc")

    frame = InspectorPanel(
        parent=win, 
        model= candb)
    
    layout.addWidget(frame)
    win.resize(800, 500)
    win.show()

    sys.exit(app.exec())