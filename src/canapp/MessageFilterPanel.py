from PySide6.QtWidgets import (
    QGroupBox, QPushButton, QTreeView,
    QVBoxLayout, QHBoxLayout, QMessageBox, QSizePolicy
)
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex, QTimer
from typing import Dict, List, Optional, Tuple
from can_sdk.logger_setup import LOG, setup_logger
from can_sdk.canlog_viewmodel import FilterMode, LogContextManager, State
from can_sdk.dbc_manager import CANDBManager
from typing import List, Dict, Optional, Tuple
from ultility import *
from ui_sdk.components.pyqt.MessageFilterTable import MessageFilterTable

class MessageFilterPanel(QGroupBox):
    def __init__(
        self,
        parent,
        model1,   # LogContextManager
        model2,   # CANDBManager
    ):
        super().__init__(parent)

        self.setTitle("")
        self.my_model1 = model1
        self.my_model2 = model2
        # self.lb_filter_message = MessageFilterViewModel(model2)

        self._last_mode = None

        self._build_ui()
        self._bind_events()

    # -------------------------------------------------
    # UI
    # -------------------------------------------------
    def _build_ui(self):
        # -------- shared widgets (created ONCE) --------
        self.btn_add = QPushButton("Add")
        self.btn_remove = QPushButton("Remove")
        self.btn_clear = QPushButton("Clear")

        self.btn_view_filtering = QPushButton("View Filtered Message")
        self.btn_view_filter_change = QPushButton("View Filter Changed Only")

        self.lb_filter_message = MessageFilterTable(parent=self, model2= self.my_model2)

        # limit horizontal stretch
        self._max_control_width = 360
        self._btn_max_width = self._max_control_width // 3
        for btn in (self.btn_add, self.btn_remove, self.btn_clear,
                self.btn_view_filtering, self.btn_view_filter_change):
            btn.setMaximumWidth(self._max_control_width)
            btn.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        # -------- root layout --------
        self._root_layout = QVBoxLayout(self)
        self._root_layout.setContentsMargins(0, 0, 0, 0)
        self._root_layout.setSpacing(6)
        # initial layout
        self._apply_layout("portrait")

    # -------------------------------------------------
    # Portrait layout (vertical)
    # -------------------------------------------------
    def _clear_layout(self, layout: QVBoxLayout | QHBoxLayout):
        while layout.count():
            item = layout.takeAt(0)
            if item.layout():
                self._clear_layout(item.layout())
            # widgets are kept; no deletion

    def _apply_layout(self, mode: str):
        self._clear_layout(self._root_layout)

        if mode == "landscape":
            self.btn_add.setText("Add Message")
            self.btn_remove.setText("Remove Message")
            self.btn_clear.setText("Clear Message")
        else:
            self.btn_add.setText("Add")
            self.btn_remove.setText("Remove")
            self.btn_clear.setText("Clear")

        if mode == "landscape":
            row = QHBoxLayout()
            row.setAlignment(Qt.AlignLeft | Qt.AlignTop)
            row.addWidget(self.lb_filter_message, 1)

            btn_col = QVBoxLayout()
            btn_col.setAlignment(Qt.AlignLeft | Qt.AlignTop)
            btn_col.addWidget(self.btn_add)
            btn_col.addWidget(self.btn_remove)
            btn_col.addWidget(self.btn_clear)
            btn_col.addWidget(self.btn_view_filtering)
            btn_col.addWidget(self.btn_view_filter_change)
            btn_col.addStretch(1)

            row.addLayout(btn_col)
            self._root_layout.addLayout(row, 1)
        else:
            btn_row = QHBoxLayout()
            btn_row.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            # portrait: total width of 3 buttons equals max control width
            for btn in (self.btn_add, self.btn_remove, self.btn_clear):
                btn.setMaximumWidth(self._btn_max_width)
                btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            btn_row.addWidget(self.btn_add)
            btn_row.addWidget(self.btn_remove)
            btn_row.addWidget(self.btn_clear)

            self._root_layout.addLayout(btn_row)
            self._root_layout.addWidget(self.lb_filter_message, 1)
            self._root_layout.addWidget(self.btn_view_filtering)
            self._root_layout.addWidget(self.btn_view_filter_change)

        self._last_mode = mode

    # -------------------------------------------------
    # Auto layout switching
    # -------------------------------------------------
    def resizeEvent(self, event):
        super().resizeEvent(event)

        w = self.width()
        h = self.height()

        # aspect-ratio based heuristic
        if w > h * 1.2:
            mode = "landscape"
        else:
            mode = "portrait"

        if mode != self._last_mode:
            self._apply_layout(mode)

    # -------------------------------------------------
    # Events
    # -------------------------------------------------
    def _bind_events(self):
        self.btn_add.clicked.connect(self.on_btn_add_filter_msg_clicked)
        self.btn_remove.clicked.connect(self.on_btn_remove_filter_msg_clicked)
        self.btn_clear.clicked.connect(self.on_btn_remove_all_filter_msg_clicked)
        self.btn_view_filtering.clicked.connect(self.on_btn_view_filtering_clicked)
        self.btn_view_filter_change.clicked.connect(self.on_btn_view_filter_change_clicked)

    # -------------------------------------------------
    # Button handlers
    # -------------------------------------------------
    def on_btn_add_filter_msg_clicked(self):
        LOG.debug("Add filter msg")
        if not self.my_model2.cur_sig:
            return
        self.lb_filter_message.add_filter(self.my_model2.cur_sig.can_id)

    def on_btn_remove_filter_msg_clicked(self):
        LOG.debug("Remove filter msg")
        self.lb_filter_message.remove_selected()

    def on_btn_remove_all_filter_msg_clicked(self):
        LOG.debug("Clear all filters")

        if not self.lb_filter_message.get_filter_count():
            return

        res = QMessageBox.question(
            self,
            "Confirm",
            "Are you sure to remove all filtered messages?",
            QMessageBox.Ok | QMessageBox.Cancel
        )

        if res == QMessageBox.Ok:
            self.lb_filter_message.clear_filters()


    def on_btn_view_filtering_clicked(self):
        LOG.debug("View filtering")

        ctx = self.my_model1.cur_ctx
        if ctx is None:
            return
        
        if ctx.state != State.DONE:
            return

        if ctx.filter_state == FilterMode.FILTERMSG:
            ctx.on_all_messages()
            return

        ids = self.lb_filter_message.get_selected_can_ids()
        if not ids:
            ids = list(self.lb_filter_message.get_filters())
        if not ids:
            return

        ctx.on_filter_messages_by_id(ids)

    def on_btn_view_filter_change_clicked(self):
        LOG.debug("View filter changed")

        ctx = self.my_model1.cur_ctx
        if ctx is None:
            return
        
        if ctx.state != State.DONE:
            return

        if ctx.filter_state == FilterMode.FILTERMSGCHANGED:
            ctx.on_all_messages()
            return

        ids = self.lb_filter_message.get_selected_can_ids()
        if not ids:
            ids = list(self.lb_filter_message.get_filters())
        if not ids:
            return

        ctx.on_filter_messages_changed_by_id(ids)