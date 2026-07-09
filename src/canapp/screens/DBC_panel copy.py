from PySide6.QtWidgets import (
    QWidget, QGroupBox, QPushButton, QListWidget,
    QLineEdit, QLabel, QGridLayout, QVBoxLayout,
    QMessageBox, QFileDialog, QComboBox, QCheckBox, QSizePolicy)
from PySide6.QtCore import Qt, Slot
from pathlib import Path
import re
from ui_sdk.components.pyqt.basic_component.ReadonlyListbox import ReadOnlyListWidget
from can_sdk.dbc_manager import CANDBManager, SignalFilter
from can_sdk.logger_setup import LOG, setup_logger

SUPPORTED_EXT = {".asc", ".log", ".txt", ".csv", ".blf", ".xls", ".xlsx"}

class CANDBCPanel(QWidget):
    def __init__(self, parent, model: CANDBManager):
        super().__init__(parent)
        self.my_model = model          # CANDBManager
        self.my_model.event_on_db_changed.subscribe(self.on_event_db_select_changed)
        self.my_model.event_on_db_list_changed.subscribe(self.on_event_db_list_changed)
        #self.model1.event_on_list_changed.subscribe(self.on_event_contexts_list_changed)

        self._build_ui()
        self._bind_events()

        # initial sync
        self.on_event_db_select_changed()
        self.on_event_db_list_changed()
        # self.on_event_contexts_list_changed(self.model1.cur_ctx)

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
    def _build_ui(self):
        main = QVBoxLayout(self)

        # ---- Top buttons ----
        top = QWidget()
        top_layout = QGridLayout(top)

        self.btn_load_db = QPushButton("Load CAN DBC")
        # self.btn_load_logs = QPushButton("Load CAN Log Folder")
        # self.btn_load_log = QPushButton("Read CAN Log")
        # self.btn_delete_log = QPushButton("Delete CAN Log")

        top_layout.addWidget(self.btn_load_db, 0, 0, 1, 2)
        # top_layout.addWidget(self.btn_load_logs, 1, 0)
        # top_layout.addWidget(self.btn_load_log, 0, 1)
        # top_layout.addWidget(self.btn_delete_log, 1, 1)


        # ---- Combobox (under the button) ----
        self.status_can_db = QComboBox()
        self.status_can_db.setEditable(False)
        self.status_can_db.setSizePolicy(
            QSizePolicy.Ignored,
            QSizePolicy.Fixed
        )
        self.status_can_db.setMinimumWidth(0)
        self.status_can_db.addItem("None")

        # ---- Total message label ----
        self.total_msg_label = QLabel("Total messages: 0")

        top_layout.addWidget(self.status_can_db, 1, 0)
        top_layout.addWidget(self.total_msg_label, 1, 1)
        top_layout.setColumnStretch(0, 1)
        top_layout.setColumnStretch(1, 0)
        
        # ---- DB info panel ----
        self.db_group = QGroupBox("")
        grid = QGridLayout(self.db_group)

        # Message filter + list
        self.tb_msg_filter = QLineEdit()
        self.tb_msg_filter.setPlaceholderText("Message Filter")
        self.tb_msg_filter.setClearButtonEnabled(True)
        self.tb_msg_filter.setMinimumWidth(0)
        self.lb_msg_list = QListWidget()
        self.lb_msg_list.setMinimumWidth(0)
        grid.addWidget(self.tb_msg_filter, 0, 0)
        grid.addWidget(QLabel("CAN Message List"), 1, 0)
        grid.addWidget(self.lb_msg_list, 2, 0)

        # Signal filter + list
        self.tb_signal_filter = QLineEdit()
        self.tb_signal_filter.setPlaceholderText("Signal Filter")
        self.tb_signal_filter.setClearButtonEnabled(True)
        self.tb_signal_filter.setMinimumWidth(0)
        self.lb_signal_list = QListWidget()
        self.lb_signal_list.setMinimumWidth(0)

        # Checkbox to enable global signal search mode
        self.cb_signal_global = QCheckBox("All")
        self.cb_signal_global.setToolTip("Search signals across all messages when checked")

        # Create horizontal layout for "Signal List" label and checkbox
        signal_label_widget = QWidget()
        signal_label_layout = QGridLayout(signal_label_widget)
        signal_label_layout.setContentsMargins(0, 0, 0, 0)
        signal_label_layout.addWidget(QLabel("Signal List"), 0, 0)
        signal_label_layout.setColumnStretch(1, 1)  # Add stretch in middle
        signal_label_layout.addWidget(self.cb_signal_global, 0, 2)  # Checkbox at right

        grid.addWidget(self.tb_signal_filter, 0, 1)
        grid.addWidget(signal_label_widget, 1, 1)
        grid.addWidget(self.lb_signal_list, 2, 1)

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

        main.addWidget(top)
        main.addWidget(self.db_group, 1)

    # ------------------------------------------------------------------
    # Bindings
    # ------------------------------------------------------------------
    def _bind_events(self):
        self.btn_load_db.clicked.connect(self.on_btn_load_candb_clicked)
        # self.btn_load_logs.clicked.connect(self.on_btn_add_logs_clicked)
        # self.btn_load_log.clicked.connect(self.on_btn_load_log_clicked)
        # self.btn_delete_log.clicked.connect(self.on_btn_delete_log_clicked)

        self.status_can_db.currentIndexChanged.connect(self.on_cbx_db_selected)

        self.tb_msg_filter.textChanged.connect(self.on_msg_filter_change)
        self.tb_signal_filter.textChanged.connect(self.on_signal_filter_change)
        # toggle global search refresh
        try:
            self.cb_signal_global.stateChanged.connect(lambda _: self.update_signal_list(self.tb_signal_filter.text()))
        except Exception:
            pass

        self.lb_msg_list.currentRowChanged.connect(self.on_msg_selected)
        self.lb_signal_list.currentRowChanged.connect(self.on_signal_selected)

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------

    def update_total_message_label(self):
        size = self.my_model.get_messages_len(self.my_model.get_main_db_file())
        self.total_msg_label.setText(f"Total messages: {size}")

    def on_event_db_list_changed(self):
        LOG.debug("on_event_db_list_changed")
        self.update_total_message_label()

        cbx = self.status_can_db
        cbx.blockSignals(True)
        cbx.clear()

        all_db_files = self.my_model.get_list_all_db_filename()

        if not all_db_files:
            cbx.addItem("None")
            cbx.setCurrentIndex(0)
            cbx.blockSignals(False)
            return

        cbx.addItems(all_db_files)

        cur_item = self.my_model.get_main_db_filename()
        LOG.debug(f"Current main db: {cur_item}")

        if cur_item in all_db_files:
            cbx.setCurrentIndex(all_db_files.index(cur_item))
        else:
            cbx.setCurrentIndex(0)

        cbx.blockSignals(False)

    def on_event_contexts_list_changed(self, ctx=None):
        pass

    def on_event_db_select_changed(self):
        self.lb_msg_list.clear()
        self.lb_signal_list.clear()
        self.lb_msg_info.clear()
        self.lb_signal_info.clear()

        all_db = self.my_model.get_list_all_db_filename()
        self.btn_load_db.setText("Add CAN DBC" if all_db else "Load CAN DBC")

        if all_db:
            self.update_msg_list()
            self.update_total_message_label()

    # ------------------------------------------------------------------
    # Message / Signal Logic
    # ------------------------------------------------------------------
    def update_msg_list(self, filter_text=""):
        self.lb_msg_list.clear()
        self.lb_signal_list.clear()
        self.lb_msg_info.clear()
        self.lb_signal_info.clear()

        data = self.my_model.messages_view
        filtered = self._filtered_list(data, filter_text)
        self.lb_msg_list.addItems(filtered)

    def update_signal_list(self, filter_text=""):
        self.lb_signal_list.clear()
        self.lb_signal_info.clear()
        # Determine mode: global if checkbox checked, otherwise local if message selected
        use_global = getattr(self, 'cb_signal_global', None) and self.cb_signal_global.isChecked()

        msg = self.my_model.selected_message_info

        # If not global mode and a message is selected -> search within that message
        if not use_global and msg:
            signals = msg.signals
            view = [f"{s.start} - {s.length}: {s.name}" for s in signals]
            filtered = self._filtered_list(view, filter_text)
            self.lb_signal_list.addItems(filtered)
            return

        # If not global mode and no message selected -> show nothing
        if not use_global and not msg:
            return

        # Global mode: search across all messages
        items = []
        try:
            candb = self.my_model.candb
            for frm_id, msg_obj in candb.messages.items():
                for s in msg_obj.signals:
                    item = f"[{frm_id:03X}] {msg_obj.name} - {s.name}"
                    items.append(item)
        except Exception:
            return

        filtered = self._filtered_list(items, filter_text)
        self.lb_signal_list.addItems(filtered)

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


    def on_btn_load_candb_clicked(self):
        LOG.debug("Click add candb button")

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Load CAN DBC",
            "",
            "CAN Database (DBC files) (*.dbc)"
        )

        if not file_path:
            return

        # Load or add database
        if not self.my_model.get_main_db_file():
            res = self.my_model.load_database(file_path)
        else:
            res = self.my_model.add_database(file_path)

        if res and len(res) > 0:
            QMessageBox.information(
                self,
                "Database Add Completed",
                f"Have {len(res)} messages be added to current Database"
            )
            self.my_model.set_main_db_file(file_path)
        else:
            QMessageBox.information(
                self,
                "Database Already Existed",
                "Have 0 messages be added to current Database"
            )


    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------
    @Slot(int)
    def on_cbx_db_selected(self, index: int):
        LOG.debug("on_cbx_db_selected")

        files = self.my_model.get_list_all_db_file()
        if 0 <= index < len(files):
            selected_item = files[index]
            self.my_model.set_main_db_file(selected_item)


    @Slot(int)
    def on_msg_selected(self, row):
        if row < 0:
            return

        text = self.lb_msg_list.item(row).text()
        try:
            can_id = int(text.split("]")[0].replace("[", ""), 16)
        except Exception:
            return
        
        msg = self.my_model.get_message(can_id)
        if not msg:
            return
        
        self.my_model.cur_sig = SignalFilter(_msg_info = msg)

        # Auto-uncheck global checkbox when user clicks a message
        if self.cb_signal_global.isChecked():
            self.cb_signal_global.setChecked(False)

        self.update_signal_list()
        self.update_message_info()

    @Slot(int)
    def on_signal_selected(self, row):
        if row < 0:
            return

        text = self.lb_signal_list.item(row).text()

        # Format A (per-message): "start - length: name"
        if ":" in text:
            name = text.split(":", 1)[1].strip()
            # self.my_model.get_signal()
            self.my_model.update_selected_signal_info(name)
            self.update_signal_info()
            return

        # Format B (global): "[ID] MessageName - SignalName"
        import re
        m = re.match(r"\[([0-9A-Fa-f]+)\]\s*(.*)", text)
        if m:
            can_hex = m.group(1)
            rest = m.group(2)
            if " - " in rest:
                sig_name = rest.split(" - ")[-1].strip()
            else:
                sig_name = rest.strip()
            try:
                can_id = int(can_hex, 16)
                # Manually select message in model WITHOUT triggering events
                if can_id in self.my_model.candb.messages:
                    msg_obj = self.my_model.candb.messages[can_id]
                    sig = SignalFilter(_msg_info=msg_obj)
                    self.my_model.cur_sig = sig
                    
                    # Visually highlight message in list without triggering slot
                    display = f"[{msg_obj.frame_id:03X}] {msg_obj.name}"
                    msgs = self.my_model.messages_view
                    if display in msgs:
                        idx = msgs.index(display)
                        self.lb_msg_list.blockSignals(True)
                        self.lb_msg_list.setCurrentRow(idx)
                        self.lb_msg_list.blockSignals(False)
            except Exception:
                pass
            self.my_model.update_selected_signal_info(sig_name)
            self.update_signal_info()
            return

        # Fallback: try to extract after colon
        if ":" in text:
            name = text.split(":", 1)[1].strip()
            # self.my_model.update_selected_signal_info(name)
            self.update_signal_info()

    # ------------------------------------------------------------------
    # Filters
    # ------------------------------------------------------------------
    def on_msg_filter_change(self, text):
        if text == "Message Filter":
            return
        self.update_msg_list(text)

    def on_signal_filter_change(self, text):
        if text == "Signal Filter":
            return
        self.update_signal_list(text)

    # ------------------------------------------------------------------
    # Utils
    # ------------------------------------------------------------------
    def _filtered_list(self, data, text):
        text = text.strip()
        if not text:
            return data
        try:
            pat = re.compile(text, re.IGNORECASE)
            return [x for x in data if pat.search(x)]
        except re.error:
            return data

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

    frame = CANDBCPanel(
        parent=win, 
        model= candb)
    
    layout.addWidget(frame)
    win.resize(800, 500)
    win.show()

    sys.exit(app.exec())