from typing import Optional
from ui_sdk.components.pyqt.basic_component.ComboboxSearch import ComboBoxSearch
from lw.logger_setup import LOG
from PySide6.QtWidgets import (
    QWidget, QGroupBox, QVBoxLayout, QLabel, QPushButton, QSizePolicy, QToolBox,
    QApplication, QStackedWidget, QFrame)
from PySide6 import QtCore, QtGui, QtWidgets
from typing import Any, Optional, Callable, Dict, List, Tuple
import re

class CanIdEditBox(QtWidgets.QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText(
            "CAN FD ID range: 0x000-0x7FF (STD), 0x00000000-0x1FFFFFFF (EXT)"
        )
        self._is_formatting = False
        self.textChanged.connect(self._on_text_changed)

    # ---------------------------
    # Public API
    # ---------------------------
    def current_value(self) -> Optional[int]:
        text = self.text().strip()
        if not text:
            return None

        can_id = self._parse_can_id(text)
        return can_id

    def _on_text_changed(self, text: str):
        if self._is_formatting:
            return

        normalized = self._normalize_display_text(text)
        if normalized == text:
            return

        self._is_formatting = True
        try:
            self.setText(normalized)
        finally:
            self._is_formatting = False

    def _commit(self):
        text = self.text().strip()
        if not text:
            return

        can_id = self._parse_can_id(text)
        if can_id is None:
            return

        if can_id < 0 or can_id > 0x1FFFFFFF:
            return

        self.setText(self._format_hex(can_id))

    def _normalize_display_text(self, text: str) -> str:
        t = text.strip()
        if not t:
            return ""

        can_id = self._parse_can_id(t)
        if can_id is None:
            return text
        if can_id < 0 or can_id > 0x1FFFFFFF:
            return text

        return self._format_hex(can_id)

    # ---------------------------
    # Internal
    # ---------------------------
    def _parse_can_id(self, text: str) -> Optional[int]:
        t = text.strip()
        if not t:
            return None

        bracketed = re.match(r"^\s*\[([^\]]+)\]\s*(.*)$", t)
        if bracketed:
            id_str = bracketed.group(1).strip()
        else:
            id_str = t.split(None, 1)[0].strip()

        if re.fullmatch(r"\d+", id_str):
            try:
                return int(id_str, 10)
            except Exception:
                return None

        if re.fullmatch(r"0[xX][0-9A-Fa-f]+", id_str):
            try:
                return int(id_str, 16)
            except Exception:
                return None

        if re.fullmatch(r"[0-9A-Fa-f]+", id_str) and re.search(r"[A-Fa-f]", id_str):
            try:
                return int(id_str, 16)
            except Exception:
                return None

        return None

    def _format_hex(self, can_id: int) -> str:
        if can_id <= 0x7FF:
            return f"0x{can_id:03X}"
        return f"0x{can_id:08X}"

class RawBytesEditBox(QtWidgets.QLineEdit):
    valueChanged = QtCore.Signal(object)  # Optional[bytes]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText('e.g. "FF AB 21 AA" or "FF12AB" or "FF,AB,21,AA"')
        allowed_input = QtCore.QRegularExpression(r"^[0-9A-Fa-f\s,;:\-xX]*$")
        self.setValidator(QtGui.QRegularExpressionValidator(allowed_input, self))
        self._parsed_value: Optional[bytes] = None
        self._bytes_num: Optional[int] = None
        self._is_formatting = False
        self.textChanged.connect(self._on_text_changed)
        self._on_text_changed(self.text())

    # ---------------------------
    # Public API
    # ---------------------------
    def current_value(self) -> Optional[bytes]:
        return self._parsed_value

    def has_valid_value(self) -> bool:
        return self._parsed_value is not None

    def set_bytes_num(self, bytes_num: Optional[int]):
        if bytes_num is None:
            self._bytes_num = None
        else:
            n = int(bytes_num)
            self._bytes_num = n if n > 0 else None

        self._on_text_changed(self.text())

    def bytes_num(self) -> Optional[int]:
        return self._bytes_num

    def _on_text_changed(self, text: str):
        if self._is_formatting:
            return

        normalized = self._normalize_display_text(text)
        if normalized != text:
            self._is_formatting = True
            try:
                self.setText(normalized)
            finally:
                self._is_formatting = False
            return

        self._parsed_value = self._parse_raw_bytes(text)
        self.valueChanged.emit(self._parsed_value)

    def _normalize_display_text(self, text: str) -> str:
        s = text.upper()
        s = re.sub(r"0X", "", s)
        s = re.sub(r"[^0-9A-F]", "", s)
        if not s:
            return ""

        if self._bytes_num is not None:
            s = s[: self._bytes_num * 2]

        groups = [s[i:i + 2] for i in range(0, len(s), 2)]
        return " ".join(groups)

    # ---------------------------
    # Internal
    # ---------------------------
    def _parse_raw_bytes(self, txt: str) -> Optional[bytes]:
        """
        Accept:
        - "FF AB 21 AA"
        - "FF,AB,21,AA"
        - "FF12AB" (no spaces)
        - mixed separators
        Returns raw bytes (length 1..64) or None.
        """
        s = txt.strip()
        # Remove common separators into spaces
        s = s.replace(",", " ").replace(";", " ").replace(":", " ").replace("-", " ")
        s = re.sub(r"\s+", " ", s).strip()

        # Case 1: spaced tokens
        tokens = s.split(" ")
        if len(tokens) > 1:
            out: List[int] = []
            for tok in tokens:
                tok = tok.strip()
                if tok == "":
                    continue
                if not re.fullmatch(r"[0-9a-fA-F]{1,2}", tok):
                    return None
                out.append(int(tok, 16))
            if not out:
                return None
            if self._bytes_num is not None and len(out) != self._bytes_num:
                return None
            if len(out) > 64:
                return None
            return bytes(out)

        # Case 2: no spaces (e.g. FF12AB)
        s2 = tokens[0] if tokens else ""
        s2 = s2.replace("0x", "").replace("0X", "")
        if not re.fullmatch(r"[0-9a-fA-F]+", s2):
            return None
        if len(s2) % 2 != 0:
            # odd length like "F12" invalid; you can decide to left-pad, but safer invalid
            return None
        out = bytes(int(s2[i:i+2], 16) for i in range(0, len(s2), 2))
        if self._bytes_num is not None and len(out) != self._bytes_num:
            return None
        if len(out) == 0 or len(out) > 64:
            return None
        return out


class TimeEditBox(QtWidgets.QLineEdit):
    """
    Duration editor with adaptive display:
    12ms → 12ms
    1000ms → 1.0s
    62.3s → 1m2.3s
    """

    _TIME_RE = re.compile(
        r"""
        ^
        (?:
            (?P<ms>\d+)ms
            |
            (?P<s>\d+(\.\d+)?)s
            |
            (?P<m>\d+)m(?P<ms2>\d+(\.\d+)?)s
            |
            (?P<h>\d+)h(?P<m2>\d+)m(?P<ms3>\d+(\.\d+)?)s
        )
        $
        """,
        re.VERBOSE
    )
    _MAX_SECONDS = 10.0
    valueChanged = QtCore.Signal(float)  # seconds

    def __init__(self, parent=None):
        super().__init__(parent)

        self._seconds = 0.0
        self.setAlignment(QtCore.Qt.AlignRight)
        self.setPlaceholderText("")

        self.editingFinished.connect(self._commit)

    # -------------------------
    # Public API
    # -------------------------
    def setSeconds(self, seconds: float):
        self._seconds = self._clamp_seconds(seconds)
        self.setText(self.format_timediff(self._seconds))

    def seconds(self) -> float:
        return self._seconds

    # -------------------------
    # Commit / validation
    # -------------------------
    def _commit(self):
        text = self.text()
        try:
            seconds = self.parse_timediff(text)
        except ValueError:
            # revert to last valid value
            self.setText(self.format_timediff(self._seconds))
            return
        self._seconds = self._clamp_seconds(seconds)
        self.setText(self.format_timediff(self._seconds))
        self.valueChanged.emit(self._seconds)

    def parse_timediff(self, text: str) -> float:
        stripped = text.strip()
        if re.fullmatch(r"\d+", stripped):
            return int(stripped) / 1000.0

        m = self._TIME_RE.match(stripped)
        if not m:
            raise ValueError("Invalid time format")

        if m.group("ms"):
            return int(m.group("ms")) / 1000.0

        if m.group("s"):
            return float(m.group("s"))

        if m.group("m"):
            return int(m.group("m")) * 60 + float(m.group("ms2"))

        if m.group("h"):
            return (
                int(m.group("h")) * 3600
                + int(m.group("m2")) * 60
                + float(m.group("ms3"))
            )

        raise ValueError("Invalid time format")

    def _clamp_seconds(self, seconds: float) -> float:
        return max(0.0, min(float(seconds), self._MAX_SECONDS))

    def format_timediff(self, seconds: float) -> str:
        seconds = self._clamp_seconds(seconds)
        if seconds < 1.0:
            ms = int(round(seconds * 1000.0))
            return f"{ms}ms"

        if seconds < 60.0:
            s_text = f"{seconds:.3f}".rstrip("0").rstrip(".")
            return f"{s_text}s"

        minutes = int(seconds // 60)
        rem = seconds - minutes * 60
        rem_text = f"{rem:.3f}".rstrip("0").rstrip(".")
        return f"{minutes}m{rem_text}s"


class FloatEditBox(QtWidgets.QLineEdit):
    """
    Floating-point editor with auto-complete behavior.
    Examples:
    .5   -> 0.5
    -.5  -> -0.5
    12.  -> 12.0
    1,25 -> 1.25
    """

    valueChanged = QtCore.Signal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._value: Optional[float] = None
        self.setAlignment(QtCore.Qt.AlignRight)
        self.setPlaceholderText("e.g. 12.34")
        float_re = QtCore.QRegularExpression(r"^[+-]?(?:\d+(?:[\.,]\d*)?|[\.,]\d+)?$")
        self.setValidator(QtGui.QRegularExpressionValidator(float_re, self))
        self.editingFinished.connect(self._commit)

    # -------------------------
    # Public API
    # -------------------------
    def current_value(self) -> Optional[float]:
        return self._parse_float(self.text())

    def set_value(self, value: Optional[float]):
        if value is None:
            self._value = None
            self.clear()
            return
        self._value = float(value)
        self.setText(self._format_value(self._value))

    # -------------------------
    # Commit / parsing
    # -------------------------
    def _commit(self):
        parsed = self._parse_float(self.text())
        if parsed is None:
            if self._value is None:
                self.clear()
            else:
                self.setText(self._format_value(self._value))
            return

        self._value = parsed
        self.setText(self._format_value(parsed))
        self.valueChanged.emit(parsed)

    def _normalize_text(self, text: str) -> str:
        t = text.strip().replace(",", ".")
        if t.startswith("-."):
            t = "-0" + t[1:]
        elif t.startswith("+."):
            t = "+0" + t[1:]
        elif t.startswith("."):
            t = "0" + t
        if t.endswith("."):
            t = t + "0"
        return t

    def _parse_float(self, text: str) -> Optional[float]:
        t = self._normalize_text(text)
        if not t or t in ("+", "-"):
            return None
        try:
            return float(t)
        except ValueError:
            return None

    def _format_value(self, value: float) -> str:
        text = f"{value:.12f}".rstrip("0")
        if text.endswith("."):
            text += "0"
        return text



if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton

    app = QApplication(sys.argv)

    win = QWidget()
    layout = QVBoxLayout(win)

    float_box = FloatEditBox(win)
    float_box.setText(".5")
    layout.addWidget(float_box)

    time_box = TimeEditBox(win)
    time_box.setText("1000")
    layout.addWidget(time_box)

    raw_box = RawBytesEditBox(win)
    raw_box.setText("FF AB 21 AA")
    layout.addWidget(raw_box)

    result_label = QLabel("", win)
    layout.addWidget(result_label)

    btn = QPushButton("Test TimeEditBox")
    def on_test():
        float_box.clearFocus()
        time_box._commit()
        raw_val = raw_box.current_value()
        float_val = float_box.current_value()
        float_text = float_box.text()
        if raw_val is None:
            raw_text = "INVALID"
        else:
            raw_text = " ".join(f"{b:02X}" for b in raw_val)
        result = (
            f"float={float_val}, shown='{float_text}' | "
            f"seconds={time_box.seconds():.3f}, shown='{time_box.text()}' | "
            f"raw={raw_text}"
        )
        print(result)
        result_label.setText(result)

    btn.clicked.connect(on_test)
    layout.addWidget(btn)

    win.resize(520, 180)
    win.show()

    sys.exit(app.exec())
