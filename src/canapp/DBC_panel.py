from PySide6.QtWidgets import (
    QWidget, QGroupBox, QPushButton, QListWidget,
    QLineEdit, QLabel, QGridLayout, QVBoxLayout, QHBoxLayout, QBoxLayout,
    QMessageBox, QFileDialog, QComboBox, QCheckBox, QSizePolicy,
    QRadioButton, QButtonGroup, QScrollArea)
from PySide6.QtCore import Qt, Slot
from pathlib import Path
import re
from typing import Optional
from canapp.widgets.basic_component.ReadonlyListbox import ReadOnlyListWidget
from canapp.widgets.basic_component.CollapsibleSection import CollapsibleSection
from canapp.vm.dbc_view_model import DbcViewModel, ListModel
from lw.logger_setup import LOG
# from can_sdk.logger_setup import LOG, setup_logger
# from can_sdk.global_event import event_on_signal_select

SUPPORTED_EXT = {".asc", ".log", ".txt", ".csv", ".blf", ".xls", ".xlsx"}

class CANDBCPanel(QWidget):
    def __init__(self, parent, model: DbcViewModel):
        super().__init__(parent)
        self.vm = model          # CANDBManager
        # self.cur_sig: SignalFilter = None
        self._last_mode: Optional[str] = None

        self._build_ui()

        self.btn_load_db.clicked.connect(self.on_btn_load_candb_clicked)

        self.status_can_db.currentIndexChanged.connect(
            lambda _: setattr(
                self.vm,
                "dbc_id",
                self.status_can_db.currentData(
                    ListModel.ItemRole
                ),
            )
        )
        self.tb_msg_filter.textChanged.connect(
            lambda text: setattr(self.vm, "msgFilter", text)
        )

        self.tb_signal_filter.textChanged.connect(
            lambda text: setattr(self.vm, "sigFilter", text)
        )
        # toggle global search refresh
        # try:
        #     self.cb_signal_global.stateChanged.connect(lambda _: self.update_signal_list(self.tb_signal_filter.text()))
        # except Exception:
        #     pass
        self.lb_msg_list.currentRowChanged.connect(
            lambda _: setattr(
                self.vm,
                "curMessage",
                self.lb_msg_list.currentIndex().data(
                    ListModel.ItemRole
                ),
            )
        )

        self.lb_signal_list.currentRowChanged.connect(
            lambda _: setattr(
                self.vm,
                "curSignal",
                self.lb_signal_list.currentIndex().data(
                    ListModel.ItemRole
                ),
            )
        )
        self.vm.dbcChanged.connect(self._reevaluate)
        self._reevaluate()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
    def _build_ui(self):
        main = QVBoxLayout(self)

        # ---- Top buttons ----
        top = QWidget()
        top_layout = QGridLayout(top)

        self.btn_load_db = QPushButton("Load CAN DBC")
        top_layout.addWidget(self.btn_load_db, 0, 0, 1, 2)

        # ---- Combobox (under the button) ----
        self.status_can_db = QComboBox()
        self.status_can_db.setModel(
            self.vm.dbcs
        )
        self.status_can_db.setModel(self.vm)
        self.status_can_db.setModelColumn(0)

        self.status_can_db.setEditable(True)
        self.status_can_db.setSizePolicy(
            QSizePolicy.Ignored,
            QSizePolicy.Fixed
        )
        self.status_can_db.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
        )
        self.status_can_db.setMinimumContentsLength(1)
        self.status_can_db.setInsertPolicy(QComboBox.NoInsert)
        if self.status_can_db.lineEdit() is not None:
            self.status_can_db.lineEdit().setReadOnly(True)
            self.status_can_db.lineEdit().setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.status_can_db.setMinimumWidth(0)
        self.status_can_db.addItem("None")

        # ---- Total message label ----
        self.total_msg_label = QLabel("Total messages: 0")
        self.total_msg_label.setMinimumWidth(0)
        self.total_msg_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
        self.total_msg_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        top_layout.addWidget(self.status_can_db, 1, 0)
        top_layout.addWidget(self.total_msg_label, 1, 1)
        top_layout.setColumnStretch(0, 1)
        top_layout.setColumnStretch(1, 0)
        
        # ---- DB info panel ----
        self.db_group = QGroupBox("")
        self._db_layout = QVBoxLayout(self.db_group)
        self._db_layout.setContentsMargins(0, 0, 0, 0)
        self._db_layout.setSpacing(4)

        self._lists_container = QWidget(self.db_group)
        self._lists_layout = QBoxLayout(QBoxLayout.LeftToRight, self._lists_container)
        self._lists_layout.setContentsMargins(0, 0, 0, 0)
        self._lists_layout.setSpacing(6)

        # Message filter + list
        self.msg_panel = QWidget(self._lists_container)
        self.msg_panel_layout = QVBoxLayout(self.msg_panel)
        self.msg_panel_layout.setContentsMargins(0, 0, 0, 0)
        self.msg_panel_layout.setSpacing(4)

        self.tb_msg_filter = QLineEdit(self.msg_panel)
        self.tb_msg_filter.setPlaceholderText("Message Filter")
        self.tb_msg_filter.setClearButtonEnabled(True)
        self.tb_msg_filter.setMinimumWidth(0)
        self.lb_msg_list = QListWidget(self.msg_panel)
        self.lb_msg_list.setModel(self.vm.messages)
        self.lb_msg_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.lb_msg_list.setMinimumWidth(0)

        self.lb_msg_title = QLabel("CAN Message List", self.msg_panel)
        self.msg_panel_layout.addWidget(self.lb_msg_title)
        self.msg_panel_layout.addWidget(self.tb_msg_filter)
        self.msg_panel_layout.addWidget(self.lb_msg_list, 1)

        # Signal filter + list
        self.sig_panel = QWidget(self._lists_container)
        self.sig_panel_layout = QVBoxLayout(self.sig_panel)
        self.sig_panel_layout.setContentsMargins(0, 0, 0, 0)
        self.sig_panel_layout.setSpacing(4)

        self.tb_signal_filter = QLineEdit(self.sig_panel)
        self.tb_signal_filter.setPlaceholderText("Signal Filter")
        self.tb_signal_filter.setClearButtonEnabled(True)
        self.tb_signal_filter.setMinimumWidth(0)
        self.lb_signal_list = QListWidget(self.sig_panel)
        self.lb_msg_list.setModel(self.vm.signals)
        self.lb_signal_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.lb_signal_list.setMinimumWidth(0)

        # Checkbox to enable global signal search mode
        self.cb_signal_global = QCheckBox("All")
        self.cb_signal_global.setToolTip("Search signals across all messages when checked")

        # Create horizontal layout for "Signal List" label and checkbox
        signal_label_widget = QWidget()
        signal_label_layout = QGridLayout(signal_label_widget)
        signal_label_layout.setContentsMargins(0, 0, 0, 0)
        signal_label_layout.setVerticalSpacing(0)
        self.lb_signal_title = QLabel("Signal List")
        signal_label_layout.addWidget(self.lb_signal_title, 0, 0, Qt.AlignLeft | Qt.AlignTop)
        signal_label_layout.setColumnStretch(1, 1)  # Add stretch in middle
        signal_label_layout.addWidget(self.cb_signal_global, 0, 2, Qt.AlignRight | Qt.AlignTop)  # Checkbox at right
        self.sig_panel_layout.addWidget(signal_label_widget)
        self.sig_panel_layout.addWidget(self.tb_signal_filter)
        self.sig_panel_layout.addWidget(self.lb_signal_list, 1)

        self._lists_layout.addWidget(self.msg_panel, 1)
        self._lists_layout.addWidget(self.sig_panel, 1)

        # # ---- CAN ID collision inspector ----
        # self.section_collision = CollapsibleSection("CAN ID Collision Inspector")
        # collision_layout = QVBoxLayout()

        # self.lb_collision_hint = QLabel(
        #     "Displays CAN IDs shared by messages from different loaded DBC files"
        # )

        # self.collision_scroll = QScrollArea()
        # self.collision_scroll.setWidgetResizable(True)
        # self.collision_scroll.setMinimumHeight(0)
        # self.collision_scroll.setMaximumHeight(220)

        # self.collision_container = QWidget()
        # self.collision_container_layout = QVBoxLayout(self.collision_container)
        # self.collision_container_layout.setContentsMargins(0, 0, 0, 0)
        # self.collision_container_layout.setSpacing(8)
        # self.collision_container_layout.addStretch(1)
        # self.collision_scroll.setWidget(self.collision_container)

        # collision_layout.addWidget(self.lb_collision_hint)
        # collision_layout.addWidget(self.collision_scroll, 1)
        # self.section_collision.setContentLayout(collision_layout)
        # self.section_collision.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

        self._db_layout.addWidget(self._lists_container, 1)
        self._db_layout.addWidget(self.section_collision, 0)

        main.addWidget(top)
        main.addWidget(self.db_group, 1)

        self._apply_layout_mode("landscape")

    def _apply_layout_mode(self, mode: str):
        if mode == self._last_mode:
            return

        if mode == "portrait":
            self._lists_layout.setDirection(QBoxLayout.TopToBottom)
            self.collision_scroll.setMaximumHeight(140)
        else:
            self._lists_layout.setDirection(QBoxLayout.LeftToRight)
            self.collision_scroll.setMaximumHeight(220)

        self._last_mode = mode

    def resizeEvent(self, event):
        super().resizeEvent(event)

        w = self.width()
        h = self.height()
        mode = "landscape" if w > h * 1.2 else "portrait"
        self._apply_layout_mode(mode)

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------
    def _reevaluate(self):
        # LOG.debug("Re-eval")
        self.total_msg_label.setText(f"Total messages: {self.vm.dbcMessagesCount}")
        self.lb_msg_list.clear()
        self.lb_signal_list.clear()
        self.lb_msg_list.addItems(self.vm.messagesList)
        self.lb_signal_list.addItems(self.vm.signalList)

    # ------------------------------------------------------------------
    # Message / Signal Logic
    # ------------------------------------------------------------------
    # def update_msg_list(self, filter_text=""):
    #     self.lb_msg_list.clear()
    #     self.lb_signal_list.clear()

    #     if self.vm.is_mixed_selected():
    #           data = self.vm.get_mixed_messages_view()
    #     else:
    #         data = self.vm.messages_view
    #     #LOG.debug(f"total {len(data)} messages")
    #     filtered = self._filtered_list(data, filter_text)
    #     self.lb_msg_list.addItems(filtered)

    # def update_signal_list(self, filter_text=""):
    #     self.lb_signal_list.clear()
    #     # Determine mode: global if checkbox checked, otherwise local if message selected
    #     use_global = getattr(self, 'cb_signal_global', None) and self.cb_signal_global.isChecked()

    #     # Global mode: skip local message logic entirely
    #     if not use_global:
    #         msg = self.cur_sig.msg_info if self.cur_sig else None

    #         # If a message is selected -> search within that message
    #         if msg:
    #             signals = msg.signals
    #             view = [f"{s.start} - {s.length}: {s.name}" for s in signals]
    #             filtered = self._filtered_list(view, filter_text)
    #             self.lb_signal_list.addItems(filtered)
    #         return

    #     # Global mode: search across all messages
    #     items = []
    #     try:
    #         candb = self.vm.candb
    #         for frm_id, msg_obj in candb.messages.items():
    #             msg_list = msg_obj if isinstance(msg_obj, list) else [msg_obj]
    #             for message in msg_list:
    #                 for s in message.signals:
    #                     item = f"[{frm_id:03X}] {message.name} - {s.name}"
    #                     items.append(item)
    #     except Exception:
    #         return

    #     filtered = self._filtered_list(items, filter_text)
    #     self.lb_signal_list.addItems(filtered)


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

        self.vm.loadDBC(file_path)

        # Load or add database
        # if not self.vm.get_main_db_file():
        #     res = self.vm.load_database(file_path)
        # else:
        #     res = self.vm.load_database(file_path)
        # if res and len(res) > 0:
        #     QMessageBox.information(
        #         self,
        #         "Database Add Completed",
        #         f"Have {len(res)} messages be added to current Database"
        #     )
        #     self.vm.set_main_db_file(file_path)
        # else:
        #     QMessageBox.information(
        #         self,
        #         "Database Already Existed",
        #         "Have 0 messages be added to current Database"
        #     )

    # def update_collision_inspector(self):
    #     if not self.vm.is_mixed_selected():
    #         self.section_collision.setVisible(False)
    #         return

    #     self.section_collision.setVisible(True)
    #     self._clear_collision_blocks()

    #     collisions = self.vm.get_mixed_can_id_collisions()
    #     if not collisions:
    #         self.lb_collision_hint.setText("No duplicated CAN IDs found in mixed database")
    #         return

    #     self.lb_collision_hint.setText(
    #         f"Found {len(collisions)} duplicated CAN IDs in mixed database"
    #     )

    #     for can_id in sorted(collisions.keys()):
    #         entries = collisions[can_id]
    #         file_count = len({file_name for file_name, _ in entries})

    #         can_group = QGroupBox(f"CAN ID [{can_id:03X}] ({len(entries)} messages in {file_count} files)")
    #         can_layout = QVBoxLayout(can_group)
    #         can_layout.setContentsMargins(6, 6, 6, 6)
    #         can_layout.setSpacing(6)

    #         option_group = QButtonGroup(can_group)
    #         option_group.setExclusive(True)

    #         for file_name, msg_name in entries:
    #             option_text = f"[{can_id:03X}] <{msg_name}> <{file_name}>"
    #             rb = QRadioButton(option_text)
    #             rb.toggled.connect(
    #                 lambda checked, cid=can_id, m=msg_name, f=file_name: (
    #                     self.on_collision_option_selected(cid, m, f) if checked else None
    #                 )
    #             )
    #             option_group.addButton(rb)
    #             can_layout.addWidget(rb)

    #         rb_none = QRadioButton("None")
    #         rb_none.setChecked(True)
    #         option_group.addButton(rb_none)
    #         can_layout.addWidget(rb_none)

    #         self.collision_container_layout.insertWidget(
    #             self.collision_container_layout.count() - 1,
    #             can_group
    #         )

    # def _clear_collision_blocks(self):
    #     while self.collision_container_layout.count() > 1:
    #         item = self.collision_container_layout.takeAt(0)
    #         widget = item.widget()
    #         if widget is not None:
    #             widget.deleteLater()

    # def on_collision_option_selected(self, can_id: int, msg_name: str, file_name: str):
    #     target_file = None
    #     for path in self.vm.get_list_all_db_file() or []:
    #         if Path(path).name == file_name:
    #             target_file = path
    #             break

    #     if target_file:
    #         try:
    #             self.vm.set_main_db_file(target_file)
    #         except Exception as ex:
    #             LOG.debug(f"Failed to set decode DBC '{target_file}': {ex}")

    #     display = f"[{can_id:03X}] {msg_name}"
    #     try:
    #         msgs = self.vm.messages_view
    #         if display in msgs:
    #             idx = msgs.index(display)
    #             self.lb_msg_list.blockSignals(True)
    #             self.lb_msg_list.setCurrentRow(idx)
    #             self.lb_msg_list.blockSignals(False)
    #         self.on_msg_selected(self.lb_msg_list.currentRow())
    #     except Exception as ex:
    #         LOG.debug(f"Failed to select message '{display}' for decode: {ex}")

    # Mock collision data removed


    # @Slot(int)
    # def on_msg_selected(self, row):
    #     if row < 0:
    #         return

    #     text = self.lb_msg_list.item(row).text()
    #     try:
    #         can_id = int(text.split("]")[0].replace("[", ""), 16)
    #         msg_name = text.split("]", 1)[1].strip() if "]" in text else ""
    #     except Exception:
    #         return

    #     msg = self.vm.get_message_by_id_and_name(can_id, msg_name)
    #     if not msg:
    #         return
        
    #     self.cur_sig = SignalFilter(_msg_info = msg)
    #     event_on_signal_select.notify(self.cur_sig)

    #     # Auto-uncheck global checkbox when user clicks a message
    #     if self.cb_signal_global.isChecked():
    #         self.cb_signal_global.setChecked(False)

    #     self.update_signal_list()

    # @Slot(int)
    # def on_signal_selected(self, row):
    #     if row < 0:
    #         return

    #     text = self.lb_signal_list.item(row).text()

    #     # Format A (per-message): "start - length: name"
    #     if ":" in text:
    #         name = text.split(":", 1)[1].strip()
    #         # self.vm.get_signal()
    #         self.vm.update_selected_signal_info(name)
    #         return

    #     # Format B (global): "[ID] MessageName - SignalName"
    #     import re
    #     m = re.match(r"\[([0-9A-Fa-f]+)\]\s*(.*)", text)
    #     if m:
    #         can_hex = m.group(1)
    #         rest = m.group(2)
    #         if " - " in rest:
    #             sig_name = rest.split(" - ")[-1].strip()
    #         else:
    #             sig_name = rest.strip()
    #         try:
    #             can_id = int(can_hex, 16)
    #             msg_name = rest.split(" - ")[0].strip() if " - " in rest else rest.strip()
    #             # Manually select message in model WITHOUT triggering events
    #             if can_id in self.vm.candb.messages:
    #                 msg_obj = self.vm.get_message_by_id_and_name(can_id, msg_name)
    #                 if not msg_obj:
    #                     return
    #                 sig = SignalFilter(_msg_info=msg_obj)
    #                 self.cur_sig = sig
    #                 event_on_signal_select.notify(sig)
                    
    #                 # Visually highlight message in list without triggering slot
    #                 display = f"[{msg_obj.frame_id:03X}] {msg_obj.name}"
    #                 msgs = self.vm.messages_view
    #                 if display in msgs:
    #                     idx = msgs.index(display)
    #                     self.lb_msg_list.blockSignals(True)
    #                     self.lb_msg_list.setCurrentRow(idx)
    #                     self.lb_msg_list.blockSignals(False)
    #         except Exception:
    #             pass
    #         self.vm.update_selected_signal_info(sig_name)
    #         return

    #     # Fallback: try to extract after colon
    #     if ":" in text:
    #         name = text.split(":", 1)[1].strip()
    #         # self.vm.update_selected_signal_info(name)

    # ------------------------------------------------------------------
    # Filters
    # ------------------------------------------------------------------
    # def on_msg_filter_change(self, text):
    #     if text == "Message Filter":
    #         return
    #     self.update_msg_list(text)

    # def on_signal_filter_change(self, text):
    #     if text == "Signal Filter":
    #         return
    #     self.update_signal_list(text)

    # ------------------------------------------------------------------
    # Utils
    # ------------------------------------------------------------------
    # def _filtered_list(self, data, text):
    #     text = text.strip()
    #     if not text:
    #         return data
    #     try:
    #         pat = re.compile(text, re.IGNORECASE)
    #         return [x for x in data if pat.search(x)]
    #     except re.error:
    #         return data

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