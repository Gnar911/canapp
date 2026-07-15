from __future__ import annotations

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

    # ------------------------------------------------------------
    # Graph: background worker (faithful to your threading approach)
    # ------------------------------------------------------------
    # def on_btn_draw_signal_clicked(self):
    #     LOG.debug("Click draw signal button")
    #     ctx = self.ctx_model.cur_ctx
    #     if not ctx:
    #         QMessageBox.warning(self, "No Log File", "Please load a logfile.")
    #         return False

    #     items = self.lb_filter_signal_.current_selected_items()
    #     if len(items) == 0:
    #         QMessageBox.warning(self, "Warning", "No signal selected, please select a signal")
    #         return False

    #     sig = _WorkerSignals()

    #     # when finished -> draw on UI thread
    #     sig.finished.connect(self._on_graph_data_ready)
    #     sig.error.connect(lambda msg: QMessageBox.warning(self, "Warning", msg))

    #     import threading
    #     try:
    #         threading.Thread(
    #             target=self._graph_worker,
    #             args=(items, sig),
    #             daemon=True
    #         ).start()
    #         return True
    #     except Exception:
    #         QMessageBox.warning(self, "Warning", "Signal graph is unavailable.")
    #         return False

    # def _graph_worker(self, items: List[SignalFilter], sig: _WorkerSignals):
    #     try:
    #         ok, timestamps, signals_data, static_data = self.on_signal_graph_collecting_data(items)
    #         if not ok:
    #             sig.error.emit("No signal found.")
    #             return
    #         sig.finished.emit(timestamps, signals_data, static_data)
    #     except Exception as e:
    #         sig.error.emit(str(e))

    # @Slot(dict, dict, list)
    # def _on_graph_data_ready(self, timestamps: dict, signals_data: dict, static_data: list):
    #     # exactly like your Tk: create drawer and plot
    #     def _draw():
    #         #drawer = Signal_Graph_Drawer()
    #         drawer.draw_axes(static_data)
    #         drawer.create_splines_data(timestamps, signals_data)
    #         drawer.start_plot()

    #     _draw()

    # ------------------------------------------------------------
    # Same core data-collection logic (ported line-by-line)
    # ------------------------------------------------------------
    # def on_signal_graph_collecting_data(self, log_sig_current_filters: List[SignalFilter]):
    #     sig_names: dict[int, list[str]] = defaultdict(list)
    #     for f in log_sig_current_filters:
    #         sig_names[f.can_id].append(f.sig_name)
    #         if len(sig_names) > 6:
    #             break

    #     ids = list(sig_names.keys())
    #     sig_n = [sig for sig_list in sig_names.values() for sig in sig_list]
    #     LOG.debug(sig_n)

    #     from can_sdk.measurement import get_timer

    #     get_timer().start("TIMESTAMP")
    #     ctx = self.ctx_model.cur_ctx
    #     if not ctx:
    #         return False, {}, {}, []

    #     timestamps = ctx.datalog.get_timestamps_of_signal_by_list_ids(
    #         ctx.file_path,
    #         sig_names,
    #     )
    #     if not timestamps:
    #         return False, {}, {}, []
    #     get_timer().elapsed("TIMESTAMP")

    #     get_timer().start("Y DATA")
    #     signals_data = ctx.datalog.get_signal_values_by_ids(ids, sig_n)
    #     get_timer().elapsed("Y DATA")

    #     static_data: list[dict[str, Any]] = []
    #     for can_id, wanted_names in sig_names.items():
    #         message_info = self.candb.candb.messages[can_id]
    #         if isinstance(message_info, list):
    #             message_info = message_info[0] if message_info else None
    #         if message_info is None:
    #             continue
    #         for signal in message_info.signals:
    #             if signal.name in wanted_names and signal.name in timestamps:
    #                 entry = {
    #                     "label": signal.name,
    #                     "color": "tab:blue",
    #                 }
    #                 if not signal.choices:
    #                     entry["y_max"] = float(signal.maximum)
    #                     entry["y_min"] = float(signal.minimum)
    #                     entry["y_label"] = None
    #                     entry["unit"] = signal.unit
    #                 else:
    #                     label_value = [v.name for v in signal.choices.values()]
    #                     entry["y_max"] = len(label_value) - 1
    #                     entry["y_min"] = 0
    #                     entry["y_label"] = label_value
    #                     entry["unit"] = None
    #                 static_data.append(entry)

    #     return True, timestamps, signals_data, static_data