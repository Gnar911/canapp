from typing import Optional, List

from PySide6.QtCore import Qt, QPoint, QModelIndex
from PySide6.QtWidgets import QFileDialog, QMenu, QApplication

from can_sdk.canlog_viewmodel import LogContextViewModel
from can_sdk.data_object import CANLogLine
from can_sdk.dbc_manager import CANDBManager

from ui_sdk.components.pyqt.TreeLogMessage import TreeLogTable, Type
from ui_sdk.components.pyqt.ultility import open_in_editor

TAG_FG = {
    # highlights (light backgrounds)
    "markselection11": (None, QColor("#FFCCCC")),
    "markselection22": (None, QColor("#C6EFCE")),
    "markselection33": (None, QColor("#FFCCFF")),
    "markselection44": (None, QColor("#CCCCFF")),
    "markselection55": (None, QColor("#E5CCFF")),
    "markselection66": (None, QColor("#CCF2FF")),
    "markselection77": (None, QColor("#FFD9B3")),
}

class TreeLogWithContext(TreeLogTable):
    def __init__(
        self,
        parent=None,
        model: CANDBManager = None,
        ctx_model: Optional[LogContextViewModel] = None,
    ):
        super().__init__(parent=parent, model=model)
        self.ctx_model: Optional[LogContextViewModel] = ctx_model
        self.view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.view.customContextMenuRequested.connect(self._show_context_menu)

    def set_context_model(self, ctx_model: Optional[LogContextViewModel]):
        self.ctx_model = ctx_model

    def copy_visible_items_to_clipboard(self):
        m = self.model_
        v = self.view
        lines: list[str] = []

        def recurse(parent_index: QModelIndex, indent: int = 0):
            rows = m.rowCount(parent_index)
            for r in range(rows):
                idx0 = m.index(r, 0, parent_index)
                idx1 = m.index(r, 1, parent_index)

                if v.isRowHidden(r, parent_index):
                    continue

                trend = str(m.data(idx0, Qt.DisplayRole) or "")
                text = str(m.data(idx1, Qt.DisplayRole) or "")
                line = ("    " * indent) + (trend + " " if trend else "") + text
                lines.append(line.rstrip())

                if v.isExpanded(idx0):
                    recurse(idx0, indent + 1)

        recurse(QModelIndex(), 0)

        out = "\n".join(lines)
        if out:
            QApplication.clipboard().setText(out)

    def _show_context_menu(self, pos: QPoint):
        if not getattr(self, "ctx_model", None):
            return

        index = self.view.indexAt(pos)
        menu = QMenu(self.view)
        menu.addAction("Copy Visible", self.copy_visible_items_to_clipboard)

        export_visible = menu.addMenu("Export Visible As")
        export_visible.addAction(".txt", lambda: self._handle_action("export_visible_txt"))
        export_visible.addAction(".csv", lambda: self._handle_action("export_visible_csv"))

        if not index.isValid():
            menu.exec(self.view.viewport().mapToGlobal(pos))
            return

        info = self.model_.selection_info(index)
        if not info:
            menu.exec(self.view.viewport().mapToGlobal(pos))
            return

        kind, msg, _sig = info
        if kind == Type.MESSAGE:
            menu.addSeparator()
            menu.addAction("Copy Selection Line", lambda: self._handle_action("copy_message_line"))

        menu.exec(self.view.viewport().mapToGlobal(pos))

    def _handle_action(self, action: str):
        index: QModelIndex = self.view.currentIndex()
        if not index.isValid():
            return

        info = self.model_.selection_info(index)
        if not info:
            return

        kind, msg, _sig = info
        clipboard = QApplication.clipboard()

        if kind == Type.MESSAGE and action == "copy_message_line":
            clipboard.setText(msg.format_line_log())
            return

        if action == "export_visible_txt":
            save_path, _ = QFileDialog.getSaveFileName(
                self.view,
                "Save filtered log as",
                "out.txt",
                "Text Files (*.txt);;All Files (*.*)",
            )
            if not save_path:
                return

            self.copy_visible_items_to_clipboard()
            open_in_editor(save_path)
            return

        if action == "export_visible_csv":
            save_path, _ = QFileDialog.getSaveFileName(
                self.view,
                "Save filtered log as",
                "out.csv",
                "CSV Files (*.csv);;All Files (*.*)",
            )
            if not save_path:
                return

            if not getattr(self, "ctx_model", None):
                return

            self.ctx_model.mCLM.write_log_csv(
                filepath=self.ctx_model.current_context_filepath,
                lines=self.ctx_model.cur_ctx.canlog_filter,
                save_filepath=save_path,
            )
            open_in_editor(save_path)

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
        