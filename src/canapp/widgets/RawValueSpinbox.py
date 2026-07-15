from PySide6.QtGui import QValidator
from PySide6.QtWidgets import QSpinBox

class RawValueSpinBox(QSpinBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRange(0, 255)
        self.setKeyboardTracking(False)
        self.setWrapping(False)

    # ---------------------------
    # Public API
    # ---------------------------
    """ Read """
    def current_value(self) -> int:
        return self.value()

    def get_value(self) -> int:
        return self.value()

    """ Write """
    def set_value(self, value: int):
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            parsed = self.minimum()
        self.setValue(max(self.minimum(), min(self.maximum(), parsed)))

    def set_value_range(self, min_value: int, max_value: int):
        min_v = max(0, int(min_value))
        max_v = max(0, int(max_value))
        if min_v > max_v:
            min_v, max_v = max_v, min_v
        self.setRange(min_v, max_v)
        self.set_value(self.value())

    def set_range(self, min_value: int, max_value: int):
        self.set_value_range(min_value, max_value)

    # ---------------------------
    # Validation
    # ---------------------------
    def validate(self, text: str, pos: int):
        text = text.strip()
        if text == "":
            return (QValidator.Intermediate, text, pos)

        if not text.isdigit():
            return (QValidator.Invalid, text, pos)

        try:
            value = int(text)
        except ValueError:
            return (QValidator.Invalid, text, pos)

        if self.minimum() <= value <= self.maximum():
            return (QValidator.Acceptable, text, pos)

        return (QValidator.Invalid, text, pos)

    def fixup(self, text: str) -> str:
        text = text.strip()
        if not text or not text.isdigit():
            return str(self.minimum())

        value = int(text)
        if value < self.minimum():
            return str(self.minimum())
        if value > self.maximum():
            return str(self.maximum())
        return text



    # ---------------------------
    # Internal
    # ---------------------------
