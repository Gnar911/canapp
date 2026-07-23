#from can_sdk.dbc_manager import CANDBManager
# from can_sdk.logfile_manager import LogContextManager, State, LogContext
# from can_sdk.parser import CANLogManager
# from lw.logger_setup import LOG, setup_logger
# import os
# from typing import Optional, List
from PySide6.QtWidgets import (
    QWidget, QGroupBox, QVBoxLayout, QHBoxLayout, QTreeView,
    QLineEdit, QComboBox, QMessageBox, QLabel, QProgressBar, QStackedLayout, QPushButton, QSizePolicy, QToolBox,
    QApplication, QStyle, QToolButton, QListView, QAbstractItemView
)
from PySide6.QtCore import Slot, Qt, Signal
from PySide6.QtWidgets import QFileDialog
# from can_sdk.parser import LogParser
from PySide6.QtGui import QFont
from canapp.vm.log_viewmodel import (
    CANLogLine,
    DecodedSignalLine,
    LogViewModel,
    LogViewModel_QtAdapter,
    QScrollBar,
    QHeaderView
)
# from canapp.widgets.TreeLogView import TreeLogView

"""
1. Display all load log files
2. Page
3. Loading bar while parsing
4. Radio button for visible Rx/Tx
5. Tool bar
"""
from PySide6.QtWidgets import (
    QGroupBox, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QComboBox
)
from PySide6.QtCore import Slot
import os

# class _OverlayWidget(QWidget):
#     sig_progress = Signal(object)
#     sig_context_changed = Signal(object)
#     sig_data_available = Signal(object)

#     def __init__(self, parent=None, model: LogContextManager = None):
#         super().__init__(parent)
#         self.my_model = model
#         self.sig_progress.connect(self.update_progress_status_bar)
#         self.sig_context_changed.connect(self.show_overlay_screen)
#         self.sig_data_available.connect(self.show_overlay_screen)

#         self.my_model.event_on_page_size_reached_periodically.subscribe(self.sig_progress.emit)
#         self.my_model.event_on_context_changed.subscribe(self.sig_context_changed.emit)
#         self.my_model.event_on_canlog_data_available.subscribe(self.sig_data_available.emit)
#         self._last_progress = -1

#         self.setAttribute(Qt.WA_StyledBackground, True)
#         self.setStyleSheet("background: rgba(0, 0, 0, 20);")

#         layout = QVBoxLayout(self)
#         layout.setAlignment(Qt.AlignCenter)

#         self.label = QLabel("Loading…")
#         self.label.setAlignment(Qt.AlignCenter)
#         self.label.setStyleSheet("""
#             QLabel {
#                 font-size: 18px;
#                 color: palette(text);
#             }
#         """)

#         self.progress = QProgressBar()
#         self.progress.setFixedWidth(240)

#         # Buttons layout
#         buttons_layout = QHBoxLayout()
#         buttons_layout.setSpacing(8)
        
#         self.cancel_btn = QPushButton("Cancel")
#         self.reload_btn = QPushButton("Reload")
#         self.cancel_btn.setFixedWidth(80)
#         self.reload_btn.setFixedWidth(80)
        
#         buttons_layout.addWidget(self.cancel_btn)
#         buttons_layout.addWidget(self.reload_btn)
#         buttons_layout.setAlignment(Qt.AlignCenter)

#         layout.addWidget(self.label)
#         layout.addSpacing(12)
#         layout.addWidget(self.progress)
#         layout.addSpacing(12)
#         layout.addLayout(buttons_layout)

#         # Empty screen label (hidden by default)
#         self._empty_label = QLabel()
#         self._empty_label.setAlignment(Qt.AlignCenter)
#         self._empty_label.setStyleSheet("QLabel { font-size: 14px; color: palette(text); }")
#         layout.addWidget(self._empty_label)
#         self._empty_label.setWordWrap(True)


#         self._empty_mode = False
#         self.cancel_btn.clicked.connect(self.on_cancel_clicked)
#         self.reload_btn.clicked.connect(self.on_reload_clicked)
#         self.show_overlay_screen(self.my_model.cur_ctx)
#         self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)


#     def show_empty_log_screen(self):
#         LOG.debug("show_empty_log_screen")
#         self.hide_overlay()
#         text = (
#             "Open or drag a file log:   Double click\n"
#             "Open folder:  Ctrl + Double click"
#         )
#         self.label.hide()
#         self.progress.hide()
#         self.progress.setRange(0, 100)
#         self.progress.setValue(0)
#         self.cancel_btn.hide()
#         self.reload_btn.hide()
#         self._empty_label.setText(text)
#         self._empty_label.show()
#         self._empty_mode = True
#         self.show()
#         self.raise_()

#     def show_overlay_screen(self, ctx: Optional[LogContext]):
#         LOG.debug("show_loading_screen")
#         if not ctx:
#             self.show_empty_log_screen()
#             return

#         if ctx.state == State.LOADING or ctx.state == State.IDLE:
#             self.show_loading()
#         else:
#             self.hide_overlay()

#     def update_progress_status_bar(self, ctx: Optional[LogContext]):
#         LOG.debug("update_progress_status_bar")
#         if not ctx:
#             return
#         percent = ctx.percent
#         # ---- Unknown progress → infinite animation ----
#         if percent is None or percent < 0:
#             self.progress.setRange(0, 0)   # busy indicator
#             self.label.setText("Loading…")
#             self.show()
#             return

#         # ---- Known progress ----
#         self.progress.setRange(0, 100)
#         self.progress.setValue(percent)
#         self.label.setText(f"Loading… {percent}%")
#         self.show()

#         # ---- Done ----
#         if percent >= 100:
#             self.hide()

#     def show_loading(self, text="Loading log…"):
#         self.hide_overlay()
#         self._empty_label.hide()
#         self.label.show()
#         self.label.setText(text)
#         self.progress.show()
#         self.progress.show()
#         self.cancel_btn.show()
#         self.reload_btn.show()
#         self.show()
#         self.raise_()

#     def hide_overlay(self):
#         LOG.debug("hide_overlay")
#         self._empty_mode = False
#         self._empty_label.hide()
#         self.hide()

#     def mouseDoubleClickEvent(self, event):
#         if not self._empty_mode:
#             return super().mouseDoubleClickEvent(event)

#         modifiers = event.modifiers()
#         # Ctrl + double click -> open folder
#         if modifiers & Qt.ControlModifier:
#             folder = QFileDialog.getExistingDirectory(self, "Select Log Folder")
#             if not folder:
#                 return
#             SUPPORTED_EXT = {".asc", ".log", ".txt", ".csv", ".blf", ".xls", ".xlsx"}
#             from pathlib import Path
#             files = [str(p) for p in Path(folder).iterdir() if p.suffix.lower() in SUPPORTED_EXT]
#             if not files:
#                 return
#             for f in files:
#                 self.my_model.mCLM.start_log_verification(file_path=f)
#             return

#         # Double click -> open single file
#         file_path, _ = QFileDialog.getOpenFileName(self, "Open CAN Log", "", "Logs (*.asc *.log *.txt *.csv *.blf *.xls *.xlsx)")
#         if not file_path:
#             return
#         self.my_model.mCLM.start_log_verification(file_path=file_path)
        
#     @Slot()
#     def on_cancel_clicked(self):
#         # Implement cancel logic (e.g., stop log parsing)
#         self.my_model.request_stop_loading_log()
#         self.hide()

#     @Slot()
#     def on_reload_clicked(self):
#         # Implement reload logic (e.g., restart parsing)
#         self.my_model.restart_loading_log()


# class TreeLogPane(QWidget):
#     """
#     Tree view + centered overlay (Loading / Empty / Error)
#     """
#     def __init__(self, 
#                  parent=None, 
#                     model1 :  CANDBManager = None,
#                  model2: LogContextManager = None):
#         super().__init__(parent)
#         self.my_model = model2
#         self.my_model1 = model1
#         self._supported_ext = {".asc", ".log", ".txt", ".csv", ".blf", ".xls", ".xlsx"}
#         self.setAcceptDrops(True)

#         self.tree = TreeLogPageTable(parent = self, model = model1)
#         self.overlay = _OverlayWidget(self, model=model2)
#         self.drop_hover = QWidget(self)
#         self.drop_hover.setAttribute(Qt.WA_TransparentForMouseEvents, True)
#         self.drop_hover.setStyleSheet("background: rgba(80, 120, 255, 35);")
#         self.drop_hover.hide()

#         layout = QStackedLayout(self)
#         layout.setStackingMode(QStackedLayout.StackAll)
#         layout.setContentsMargins(0, 0, 0, 0)
#         layout.setSpacing(0)

#         layout.addWidget(self.tree)
#         layout.addWidget(self.overlay)
#         layout.addWidget(self.drop_hover)

#         self._stack = layout
#         self.overlay.raise_()
#         self.overlay.show()

#     def resizeEvent(self, event):
#         super().resizeEvent(event)
#         self.overlay.raise_()
#         if self.drop_hover.isVisible():
#             self.drop_hover.raise_()

#     def dragEnterEvent(self, event):
#         if event.mimeData().hasUrls():
#             self.drop_hover.show()
#             self.drop_hover.raise_()
#             event.acceptProposedAction()
#             return
#         super().dragEnterEvent(event)

#     def dragMoveEvent(self, event):
#         if event.mimeData().hasUrls():
#             if not self.drop_hover.isVisible():
#                 self.drop_hover.show()
#             self.drop_hover.raise_()
#             event.acceptProposedAction()
#             return
#         super().dragMoveEvent(event)

#     def dragLeaveEvent(self, event):
#         self.drop_hover.hide()
#         super().dragLeaveEvent(event)

#     def dropEvent(self, event):
#         if not self.my_model or not event.mimeData().hasUrls():
#             self.drop_hover.hide()
#             super().dropEvent(event)
#             return

#         dropped_paths = [url.toLocalFile() for url in event.mimeData().urls() if url.isLocalFile()]
#         verify_files: list[str] = []

#         for path in dropped_paths:
#             if not path:
#                 continue
#             if os.path.isdir(path):
#                 for name in os.listdir(path):
#                     full_path = os.path.join(path, name)
#                     if not os.path.isfile(full_path):
#                         continue
#                     if os.path.splitext(full_path)[1].lower() in self._supported_ext:
#                         verify_files.append(full_path)
#             elif os.path.isfile(path):
#                 if os.path.splitext(path)[1].lower() in self._supported_ext:
#                     verify_files.append(path)

#         for file_path in verify_files:
#             self.my_model.mCLM.start_log_verification(file_path=file_path)

#         self.drop_hover.hide()
#         event.acceptProposedAction()

class FileLogViewPanel(QGroupBox):
    def __init__(
        self,
        parent: QWidget,
        vm: LogViewModel
    ):
        super().__init__("", parent)
        self.vm = vm
        self._build_ui()
        self._connect_signals()
    # -------------------------------------------------
    # UI
    # -------------------------------------------------
    def _build_ui(self):
        main = QVBoxLayout(self)
        main.setContentsMargins(6, 2, 6, 6)
        main.setSpacing(2)

        # ---- HEADER ROW ----
        header_row = QWidget(self)
        header_layout = QHBoxLayout(header_row)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(4)

        self.header_label = QLabel("View page 0 / Total 0 pages")
        self.header_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.btn_toggle_toolbox = QToolButton(self)
        self.btn_toggle_toolbox.setCheckable(True)
        self.btn_toggle_toolbox.setChecked(True)
        self.btn_toggle_toolbox.setArrowType(Qt.DownArrow)
        self.btn_toggle_toolbox.setToolTip("Show / hide tools")

        header_layout.addWidget(self.header_label)
        header_layout.addStretch(1)
        header_layout.addWidget(self.btn_toggle_toolbox)

        main.addWidget(header_row)

        # ---- TOOLBOX ROW ----
        self.toolbox_container = QWidget(self)
        self.toolbox_container.setContentsMargins(0, 0, 0, 0)
        toolbox_layout = QHBoxLayout(self.toolbox_container)
        toolbox_layout.setContentsMargins(0, 0, 0, 0)
        toolbox_layout.setSpacing(4)

        """ QT built-in set"""
        style = QApplication.instance().style() if QApplication.instance() else QApplication.style()
        icon_open_file = style.standardIcon(QStyle.SP_FileIcon)
        icon_folder = style.standardIcon(QStyle.SP_FileDialogNewFolder)
        icon_refresh = style.standardIcon(QStyle.SP_BrowserReload)
        icon_play = style.standardIcon(QStyle.SP_MediaPlay)
        icon_pause = style.standardIcon(QStyle.SP_MediaPause)
        icon_edit = style.standardIcon(QStyle.SP_FileDialogDetailedView)
        icon_delete = style.standardIcon(QStyle.SP_TrashIcon)

        self.btn_open_log = QPushButton(icon_open_file, "File")
        self.btn_open_folder = QPushButton(icon_folder, "Folder")
        self.btn_refresh = QPushButton(icon_refresh, "Reset")
        self.btn_play = QPushButton(icon_play, "Play")
        self.btn_pause = QPushButton(icon_pause, "Pause")
        self.btn_edit = QPushButton(icon_edit, "Edit")
        self.btn_delete = QPushButton(icon_delete, "Close")

        self._is_playing = False
        self._sync_play_pause_buttons()
        
        toolbox_layout.addWidget(self.btn_open_log)
        toolbox_layout.addWidget(self.btn_open_folder)
        toolbox_layout.addWidget(self.btn_refresh)
        toolbox_layout.addWidget(self.btn_play)
        toolbox_layout.addWidget(self.btn_pause)
        toolbox_layout.addWidget(self.btn_edit)
        toolbox_layout.addWidget(self.btn_delete)
        toolbox_layout.addStretch(1)
        main.addWidget(self.toolbox_container)

        # store icons for toggling
        self._icon_play = icon_play
        self._icon_pause = icon_pause

        # ---- HEADER LABEL (replaces QGroupBox title) ----
        # self.header_label = QLabel("View page 0 / Total 0 pages")
        # self.header_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        # self.header_label.setStyleSheet(
        #     "font-weight: 400; padding: 2px 0;"
        # )
        # main.addWidget(self.header_label)

        # ---- top controls ----
        top = QHBoxLayout()
        self.log_selector = QComboBox()
        self.log_selector.setEditable(False)
        self.log_selector.setFont(QFont("Sans Serif", 10))

        self.page_selector = QComboBox()
        self.page_selector.setFixedWidth(100)
        self.page_selector.setMaxVisibleItems(5)

        popup_view = QListView(self.page_selector)
        popup_view.setVerticalScrollMode(QAbstractItemView.ScrollPerItem)
        popup_view.setUniformItemSizes(True)
        popup_view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        popup_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.page_selector.setView(popup_view)
        self.page_selector.setStyleSheet("QComboBox { combobox-popup: 0; }")

        self._enforce_page_selector_popup_limit()

        # top.addWidget(self.canid_filter)
        top.addWidget(self.log_selector, 1)
        top.addWidget(self.page_selector)

        main.addLayout(top)

        # ---- log pane ----
        # self.log_pane = TreeLogView(
        #     view_model = self.vm,
        #     parent = self
        # )

        self.view = QTreeView(self)

        ## NOTE page load tree
        self.view.setModel(
            self.vm.tree_model_
        )

        # self.view.setSelectionModel(
        #     self.select_model
        # )

        mono = QFont(
            "Consolas",
            10,
        )

        mono.setStyleHint(
            QFont.StyleHint.Monospace
        )

        self.view.setFont(mono)

        header = self.view.header()

        header.setStretchLastSection(
            False
        )

        header.setSectionResizeMode(
            QHeaderView.ResizeMode.Interactive
        )

        header.setFixedHeight(20)

        self.view.setColumnWidth(
            LogViewModel_QtAdapter.COL_TREND,
            80,
        )

        self.view.setColumnWidth(
            LogViewModel_QtAdapter.COL_LOG_MESSAGES,
            1600,
        )

        self.view.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection
        )

        self.view.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )

        self.view.setUniformRowHeights(
            True
        )

        self.view.setAnimated(
            False
        )

        self.view.setAutoScroll(
            True
        )

        self.view.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        self.view.setStyleSheet(
            self._HOVER_STYLESHEET
        )

        layout = QHBoxLayout(self)

        layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        layout.setSpacing(0)

        layout.addWidget(
            self.view
        )

        self.scrollbar = QScrollBar(
            Qt.Orientation.Vertical,
            self,
        )

        layout.addWidget(
            self.scrollbar
        )

        main.addWidget(self.log_pane, 1)

        #self._update_toolbox_auto_visibility(self.vm.cur_ctx)


    # -------------------------------------------------
    # Wiring
    # -------------------------------------------------
    def _connect_signals(self):
        # UI → logic
        self.log_selector.currentIndexChanged.connect(self.on_log_selected)
        self.page_selector.currentIndexChanged.connect(self.on_page_changed)
        self.btn_toggle_toolbox.toggled.connect(self._toggle_toolbox)
        self.btn_open_log.clicked.connect(self._on_open_log_clicked)
        self.btn_open_folder.clicked.connect(self._on_open_folder_clicked)
        self.btn_refresh.clicked.connect(self.btn_refresh.clicked.connect(
            lambda: setattr(self.vm, "undoFilter", True)
        ))
        self.btn_play.clicked.connect(self._on_play_pause_clicked)
        self.btn_pause.clicked.connect(self._on_play_pause_clicked)
        self.btn_edit.clicked.connect(self._on_edit_clicked)
        self.btn_delete.clicked.connect(lambda: self.vm.closeLog())
        self.vm.commonStateChanged.connect(self._reevaluate)
        self._reevaluate()    

    def _reevaluate(self):
        pass

    def _enforce_page_selector_popup_limit(self):
        view = self.page_selector.view()
        row_h = view.sizeHintForRow(0)
        if row_h <= 0:
            row_h = self.page_selector.fontMetrics().height() + 8
        frame = view.frameWidth() * 2
        popup_h = row_h * 5 + frame
        view.setMinimumHeight(min(row_h + frame, popup_h))
        view.setMaximumHeight(popup_h)

    def _toggle_toolbox(self, checked: bool):
        self.toolbox_container.setVisible(checked)
        self.btn_toggle_toolbox.setArrowType(
            Qt.DownArrow if checked else Qt.RightArrow
        )

    # def _update_toolbox_auto_visibility(self, ctx: Optional[LogContext]):
    #     has_loaded_log = bool(ctx and getattr(ctx, "file_path", None))

    #     self.btn_toggle_toolbox.setVisible(has_loaded_log)
    #     self.btn_toggle_toolbox.setEnabled(has_loaded_log)

    #     if not has_loaded_log:
    #         self.toolbox_container.setVisible(False)
    #         return

    #     self.btn_toggle_toolbox.setChecked(True)
    #     self.btn_toggle_toolbox.setArrowType(Qt.DownArrow)
    #     self.toolbox_container.setVisible(True)

    @Slot()
    def _on_open_log_clicked(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open CAN Log",
            "",
            "Logs (*.asc *.log *.txt *.csv *.blf *.xls *.xlsx)"
        )
        if not file_path:
            return
        self.vm.startParsing(file_path=file_path)

    @Slot()
    def _on_open_folder_clicked(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Log Folder")
        if not folder:
            return
        SUPPORTED_EXT = {".asc", ".log", ".txt", ".csv", ".blf", ".xls", ".xlsx"}
        from pathlib import Path
        files = [str(p) for p in Path(folder).iterdir() if p.suffix.lower() in SUPPORTED_EXT]
        if not files:
            return
        
        """ 20260721 TODO: Feature not Implemented"""
        # for f in files:
        #     self.vm.mCLM.start_log_verification(file_path=f)

    # @Slot()
    # def _on_refresh_clicked(self):
    #     self.vm.undoFilter = True

    @Slot()
    def _on_play_pause_clicked(self):
        self._is_playing = not self._is_playing
        self._sync_play_pause_buttons()
        # TODO: implement play/pause logic
        pass

    def _sync_play_pause_buttons(self):
        self.btn_play.setVisible(not self._is_playing)
        self.btn_pause.setVisible(self._is_playing)

    @Slot()
    def _on_edit_clicked(self):
        """ 20260721 TODO: Feature not Implemented"""

    # @Slot()
    # def _on_delete_clicked(self):
    #     self.vm.closeLog()

    # def update_combobox_file_path(self):
    #     LOG.debug("update_combobox_file_path")
    #     self.log_selector.clear()
    #     base_names = [
    #         os.path.basename(p)
    #         for p in self.vm.get_all_context_filepath
    #     ]
    #     self.log_selector.addItems(base_names)

    # @Slot(int)
    # def on_log_selected(self, idx: int):
    #     """
    #     User selected a different log file.
    #     """
    #     paths = self.vm.get_all_context_filepath
    #     if not (0 <= idx < len(paths)):
    #         return

    #     selected_path = paths[idx]
    #     if selected_path == self.vm.cur_ctx.file_path:
    #         return

    #     self.vm.switch_context(selected_path)

    # def focus_message_line_number(self, num: int) -> bool:
    #     """
    #     Focus a message by absolute row index in current filtered dataset.
    #     It computes page + relative row, updates page content, then forwards
    #     to TreeLogTable.focus_message_row(relative_row).
    #     """
    #     ctx = self.vm.cur_ctx
    #     if not ctx:
    #         return False

    #     if num < 0:
    #         return False

    #     total_rows = len(ctx.canlog_filter)
    #     if num >= total_rows:
    #         return False

    #     target_page = (num // FileLogViewPanel.PAGE_SIZE) + 1
    #     relative_row = num % FileLogViewPanel.PAGE_SIZE

    #     if ctx.cur_page != target_page:
    #         ctx.cur_page = target_page

    #     self.change_page_information(ctx)
    #     #self.update_ui_tree_log_view(ctx)

    #     return self.log_view.focus_message_row(relative_row)

# if __name__ == "__main__":
#     import sys
#     from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton
#     from PySide6.QtCore import Qt
#     setup_logger(env="DEV", backup_count=30)
#     app = QApplication(sys.argv)
#     win = QWidget()
#     win.setWindowTitle("TreeLogTable Test")
#     layout = QVBoxLayout(win)
#     candb = CANDBManager()
#     candb.load_database("/home/gnar911/Desktop/20260122 APP WEBSITE - CAN ANALYZER 3.0 CBCM TOOL APP ARC/CAN_Analyzer_MVVM/Database/EEA10_CANFD_R00c_withADAS_Main.dbc")
#     FILELOG = "/home/gnar911/Desktop/2025-02-11_11-14-53_仕様情報切替 1_x1000.asc"
#     ctx = LogContextManager()
#     tree = FileLogViewPanel(parent=win, candb =candb, vm= ctx)
#     layout.addWidget(tree)

#     """ Test case 1: After done verify file log -> create a context for it, start parsing log async """
#     #clm.start_log_verification(FILELOG_BIG)

#     focus_btn = QPushButton("Focus next row")
#     focus_btn.setToolTip("10 -> 100 -> 1000 -> ... -> 10000 -> 21000 -> 31000 -> ...")
#     layout.addWidget(focus_btn)

#     click_state = {"count": 0}

#     def _next_target_row() -> int:
#         click_state["count"] += 1
#         step = click_state["count"]
#         if step == 1:
#             return 10
#         if step == 2:
#             return 100
#         if step <= 12:
#             return (step - 2) * 1000
#         return 21000 + (step - 13) * 10000

#     def _on_focus_btn_clicked():
#         target_row = _next_target_row()
#         ok = tree.focus_message_line_number(target_row)
#         LOG.info(f"focus row requested={target_row}, success={ok}")

#     focus_btn.clicked.connect(_on_focus_btn_clicked)

#     win.resize(800, 500)
#     win.show()

#     sys.exit(app.exec())