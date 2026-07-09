from typing import Dict, Optional
from ui_sdk.components.pyqt.basic_component.ComboboxSearch import ComboBoxSearch

class SignalChoiceComboBox(ComboBoxSearch):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._raw_to_choice: Dict[int, str] = {}
        self._choice_to_raw: Dict[str, int] = {}

    # ---------------------------
    # Public API
    # ---------------------------
    def set_value(self, raw_to_choice: Dict[int, str]):
        self._raw_to_choice = {}
        self._choice_to_raw = {}

        if not raw_to_choice:
            self.set_completer_values([])
            self.clearEditText()
            return

        choices: list[str] = []
        for raw, choice_text in raw_to_choice.items():
            try:
                raw_int = int(raw)
            except (TypeError, ValueError):
                continue

            text = str(choice_text)
            self._raw_to_choice[raw_int] = text

            if text not in self._choice_to_raw:
                self._choice_to_raw[text] = raw_int
                choices.append(text)

        self.set_completer_values(choices)

        if choices:
            self.setEditText(choices[0])
        else:
            self.clearEditText()

    def current_value(self) -> Optional[int]:
        text = self.currentText().strip()
        if not text:
            return None
        return self._choice_to_raw.get(text)

    def set_raw_value(self, raw_value: int) -> bool:
        try:
            raw_int = int(raw_value)
        except (TypeError, ValueError):
            return False

        if raw_int not in self._raw_to_choice:
            return False

        target_text = self._raw_to_choice[raw_int]
        self.setEditText(target_text)
        return True


if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel

    app = QApplication(sys.argv)

    win = QWidget()
    win.setWindowTitle("SignalChoiceComboBox Test")
    layout = QVBoxLayout(win)

    cb = SignalChoiceComboBox()
    cb.set_value({
        0: "Off",
        1: "On",
        2: "Blink",
        3: "Fault",
    })
    layout.addWidget(cb)

    result_label = QLabel("")
    layout.addWidget(result_label)

    btn = QPushButton("Get current raw")

    def on_get_current():
        raw = cb.current_value()
        text = cb.currentText()
        out = f"text='{text}', raw={raw}"
        print(out)
        result_label.setText(out)

    btn.clicked.connect(on_get_current)
    layout.addWidget(btn)

    win.resize(360, 140)
    win.show()
    sys.exit(app.exec())


