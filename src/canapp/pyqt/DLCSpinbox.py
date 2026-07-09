from PySide6.QtWidgets import (QSpinBox, QPushButton,)

class DLCSpinBox(QSpinBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRange(0, 15)

    # ---------------------------
    # Public API
    # ---------------------------
    """ Read """
    def current_len_value(self) -> int:
        return self._get_length_from_dlc(self.value())

    def current_dlc_value(self) -> int:
        return self.value()
    
    """ Write """
    def set_len_value(self, length: int):
        dlc = self._get_dlc_from_length(length)
        self.setValue(dlc)

    def set_dlc_value(self, dlc: int):
        self.setValue(dlc)

    # ---------------------------
    # Internal
    # ---------------------------
    def _get_length_from_dlc(self, dlc:int) -> int:
        dlc_to_len = [0, 1, 2, 3, 4, 5, 6, 7, 8, 12, 16, 20, 24, 32, 48, 64]
        return dlc_to_len[min(dlc, len(dlc_to_len) - 1)]

    def _get_dlc_from_length(self, length: int) -> int:
        """
        Convert data length (bytes) → DLC.
        Length is rounded UP to the nearest valid CAN-FD size.
        """
        if length <= 0:
            return 0
        elif length <= 8:
            return length
        elif length <= 12:
            return 9
        elif length <= 16:
            return 10
        elif length <= 20:
            return 11
        elif length <= 24:
            return 12
        elif length <= 32:
            return 13
        elif length <= 48:
            return 14
        else:
            return 15