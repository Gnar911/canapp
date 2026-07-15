from __future__ import annotations

from typing import Optional
from PySide6.QtCore import QModelIndex, Qt
from ui_sdk.components.pyqt.DLCSpinbox import DLCSpinBox
from ui_sdk.components.pyqt.ParseableEditBox import RawBytesEditBox


class DlcRawBinder:
    def _length_from_dlc(self, dlc: int) -> int:
        dlc_to_len = [0, 1, 2, 3, 4, 5, 6, 7, 8, 12, 16, 20, 24, 32, 48, 64]
        if dlc < 0:
            return 0
        if dlc >= len(dlc_to_len):
            return dlc_to_len[-1]
        return dlc_to_len[dlc]

    def _dlc_from_length(self, length: int) -> int:
        if length <= 0:
            return 0
        if length <= 8:
            return length
        if length <= 12:
            return 9
        if length <= 16:
            return 10
        if length <= 20:
            return 11
        if length <= 24:
            return 12
        if length <= 32:
            return 13
        if length <= 48:
            return 14
        return 15

    def _format_bytes(self, data: bytes) -> str:
        return " ".join(f"{b:02X}" for b in data)

    def _adjust_raw_to_length(self, raw: bytes, target_len: int) -> bytes:
        if target_len <= 0:
            return b""
        if len(raw) >= target_len:
            return raw[:target_len]
        return raw + (b"\x00" * (target_len - len(raw)))

    def bind_dlc_editor(self, editor: DLCSpinBox, index: QModelIndex):
        editor.valueChanged.connect(lambda _v, e=editor, i=QModelIndex(index): self._on_dlc_changed(e, i))

    def bind_raw_editor(self, editor: RawBytesEditBox, index: QModelIndex):
        editor.set_bytes_num(None)
        editor.editingFinished.connect(lambda e=editor, i=QModelIndex(index): self._on_raw_edit_finished(e, i))

    def normalize_raw_editor_for_row(self, editor: RawBytesEditBox, dlc_value: int):
        target_len = self._length_from_dlc(int(dlc_value))
        parsed = editor.current_value() or b""
        adjusted = self._adjust_raw_to_length(parsed, target_len)
        adjusted_text = self._format_bytes(adjusted)
        if editor.text() != adjusted_text:
            editor.setText(adjusted_text)

    def _on_dlc_changed(self, editor: DLCSpinBox, index: QModelIndex):
        if not index.isValid():
            return

        model = index.model()
        target_len = editor.current_len_value()
        raw_index = model.index(index.row(), model.COL_RAW_DATA_BYTES, index.parent())
        if not raw_index.isValid():
            return

        raw_text = str(model.data(raw_index, Qt.DisplayRole) or "")
        parser = RawBytesEditBox()
        parser.setText(raw_text)
        parsed = parser.current_value() or b""
        adjusted = self._adjust_raw_to_length(parsed, target_len)
        model.setData(raw_index, self._format_bytes(adjusted), Qt.EditRole)

    def _on_raw_edit_finished(self, editor: RawBytesEditBox, index: QModelIndex):
        if not index.isValid():
            return

        parsed = editor.current_value()
        if parsed is None:
            return

        model = index.model()
        dlc = self._dlc_from_length(len(parsed))
        dlc_index = model.index(index.row(), model.COL_DATA_LEN, index.parent())
        if dlc_index.isValid():
            model.setData(dlc_index, dlc, Qt.EditRole)
