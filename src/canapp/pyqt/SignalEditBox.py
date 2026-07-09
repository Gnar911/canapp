from typing import Dict, Optional
from PySide6 import QtCore, QtWidgets
from can_sdk.data_object import Signal
from ui_sdk.components.pyqt.ParseableEditBox import FloatEditBox
from ui_sdk.components.pyqt.RawValueSpinbox import RawValueSpinBox
from ui_sdk.components.pyqt.SignalChoiceCombobox import SignalChoiceComboBox

class SignalEditBox(QtWidgets.QWidget):
	"""
	Composite signal editor:
	- left widget is dynamic:
		- SignalChoiceComboBox when signal is choice
		- FloatEditBox when signal is numeric
	- right widget is RawValueSpinBox
	"""

	valueChanged = QtCore.Signal(int)

	def __init__(self, parent=None, signal: Optional[Signal] = None):
		super().__init__(parent)
		self._signal: Optional[Signal] = None
		self._is_syncing = False
		self._active_editor = "first"  # "first" | "raw"
		self._raw_to_choice: Dict[int, str] = {}
		self._first_widget_max_width = 320

		self._build_ui()
		self._install_handlers()
		self._apply_active_state()

		if signal is not None:
			self.set_signal(signal)

	# ---------------------------
	# Public API
	# ---------------------------
	def set_signal(self, signal: Optional[Signal]):
		self._signal = signal
		self.refresh_from_model()

	def set_widget_height(self, height: int):
		if height <= 0:
			return
		self._choice.setFixedHeight(height)
		self._float.setFixedHeight(height)
		self._raw.setFixedHeight(height + 2)

	def widget_height(self) -> int:
		return self._choice.height()

	def set_first_widget_max_width(self, width: int):
		if width <= 0:
			return
		self._first_widget_max_width = int(width)
		self._stack.setMaximumWidth(self._first_widget_max_width)

	def signal(self) -> Optional[Signal]:
		return self._signal

	# Backward-compatible aliases
	def set_signal_filter(self, signal: Optional[Signal]):
		self.set_signal(signal)

	def signal_filter(self) -> Optional[Signal]:
		return self.signal()

	def refresh_from_model(self):
		sig = self._signal
		if sig is None:
			self._raw.set_range(0, 0)
			self._raw.set_value(0)
			self._float.set_value(None)
			self._choice.set_value({})
			self._stack.setCurrentWidget(self._float)
			return

		self._is_syncing = True
		try:
			min_raw, max_raw = sig.min_max
			self._raw.set_range(min_raw, max_raw)
			self._raw.set_value(0 if sig.rawvalue is None else sig.rawvalue)

			if bool(sig.is_choice_value):
				self._stack.setCurrentWidget(self._choice)
				self._raw_to_choice = self._build_raw_choice_map(sig)
				self._choice.set_value(self._raw_to_choice)
				if sig.rawvalue is not None:
					self._choice.set_raw_value(sig.rawvalue)
			else:
				self._stack.setCurrentWidget(self._float)
				self._float.set_value(None if sig.rawvalue is None else float(sig.value))
		finally:
			self._is_syncing = False

		self._apply_active_state()

	# ---------------------------
	# UI
	# ---------------------------
	def _build_ui(self):
		lay = QtWidgets.QHBoxLayout(self)
		lay.setContentsMargins(0, 0, 0, 0)
		lay.setSpacing(0)

		self._stack = QtWidgets.QStackedWidget(self)

		self._choice = SignalChoiceComboBox(self._stack)
		self._float = FloatEditBox(self._stack)
		self._float.setPlaceholderText("Enter signal value")
		self._raw = RawValueSpinBox(self)

		h = max(self._choice.sizeHint().height(), self._float.sizeHint().height(), self._raw.sizeHint().height())
		self.set_widget_height(h)

		self._stack.addWidget(self._choice)
		self._stack.addWidget(self._float)

		self._stack.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
		self._stack.setMaximumWidth(self._first_widget_max_width)
		self._raw.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
		self._raw.setFixedWidth(60)

		lay.addWidget(self._stack, 0)
		lay.addWidget(self._raw, 0)
		lay.addStretch(1)

	def _install_handlers(self):
		self._choice.installEventFilter(self)
		self._float.installEventFilter(self)
		self._raw.installEventFilter(self)

		self._choice.lineEdit().editingFinished.connect(self._on_choice_edited)
		self._float.editingFinished.connect(self._on_float_edited)
		self._raw.editingFinished.connect(self._on_raw_edited)
		self._raw.valueChanged.connect(self._on_raw_spin_changed)

	# ---------------------------
	# Interaction model
	# ---------------------------
	def eventFilter(self, obj, event):
		if event.type() == QtCore.QEvent.MouseButtonPress:
			if obj in (self._choice, self._float):
				if self._active_editor != "first":
					self._active_editor = "first"
					self._apply_active_state()
			elif obj is self._raw:
				if self._active_editor != "raw":
					self._active_editor = "raw"
					self._apply_active_state()
		return super().eventFilter(obj, event)

	def _apply_active_state(self):
		first_active = self._active_editor == "first"

		if self._stack.currentWidget() is self._float:
			self._float.setReadOnly(not first_active)
		else:
			self._choice.lineEdit().setReadOnly(not first_active)

		self._raw.setReadOnly(first_active)

		self._apply_styles(first_active)

	def _apply_styles(self, first_active: bool):
		first_bg = "palette(base)" if first_active else "palette(window)"
		raw_bg = "palette(base)" if not first_active else "palette(window)"

		common_border = "1px solid palette(mid)"

	# ---------------------------
	# Sync handlers
	# ---------------------------
	def _on_choice_edited(self):
		if self._is_syncing or self._active_editor != "first":
			return
		sig = self._signal
		if sig is None:
			return

		selected_raw = self._choice.current_value()
		if selected_raw is None:
			self.refresh_from_model()
			return

		sig.set_raw_value(selected_raw)
		self._sync_controls_from_model()

	def _on_float_edited(self):
		if self._is_syncing or self._active_editor != "first":
			return
		sig = self._signal
		if sig is None:
			return

		value = self._float.current_value()
		if value is None:
			self.refresh_from_model()
			return

		sig.value = value
		self._sync_controls_from_model()

	def _on_raw_spin_changed(self, _value: int):
		if self._is_syncing or self._active_editor != "raw":
			return
		self._commit_raw_change()

	def _on_raw_edited(self):
		if self._is_syncing or self._active_editor != "raw":
			return
		self._commit_raw_change()

	def _commit_raw_change(self):
		sig = self._signal
		if sig is None:
			return
		sig.set_raw_value(self._raw.current_value())
		self._sync_controls_from_model()

	def _sync_controls_from_model(self):
		sig = self._signal
		if sig is None:
			return

		self._is_syncing = True
		try:
			self._raw.set_value(0 if sig.rawvalue is None else sig.rawvalue)
			if bool(sig.is_choice_value):
				if sig.rawvalue is not None:
					self._choice.set_raw_value(sig.rawvalue)
			else:
				self._float.set_value(None if sig.rawvalue is None else float(sig.value))
		finally:
			self._is_syncing = False

		if sig.rawvalue is not None:
			self.valueChanged.emit(int(sig.rawvalue))

	def _build_raw_choice_map(self, sig: Signal) -> Dict[int, str]:
		choices = sig.get_choice_strings()
		if not choices:
			return {}

		raw_keys = list(sig.value_choices.keys()) if sig.value_choices else []
		if len(raw_keys) == len(choices):
			return {int(raw): str(text) for raw, text in zip(raw_keys, choices)}

		return {idx: text for idx, text in enumerate(choices)}


if __name__ == "__main__":
	import sys
	from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel

	class _MockSignalInfo:
		def __init__(self, *, name: str, scale: float, offset: float, length: int, is_signed: bool,
					 choices: Optional[Dict[int, str]] = None, minimum: Optional[float] = None,
					 maximum: Optional[float] = None, unit: str = ""):
			self.name = name
			self.scale = scale
			self.offset = offset
			self.length = length
			self.is_signed = is_signed
			self.choices = choices
			self.minimum = minimum
			self.maximum = maximum
			self.unit = unit
			self.initial = 0

	def _build_numeric_signal() -> Signal:
		sig = Signal(raw_value=120)
		sig.sig_info = _MockSignalInfo(
			name="VehicleSpeed",
			scale=0.05,
			offset=0.0,
			length=16,
			is_signed=False,
			minimum=0.0,
			maximum=250.0,
			unit="km/h",
		)
		return sig

	def _build_choice_signal() -> Signal:
		sig = Signal(raw_value=1)
		sig.sig_info = _MockSignalInfo(
			name="LampState",
			scale=1.0,
			offset=0.0,
			length=2,
			is_signed=False,
			choices={0: "Off", 1: "On", 2: "Blink", 3: "Fault"},
			unit="",
		)
		return sig

	app = QApplication(sys.argv)

	win = QWidget()
	win.setWindowTitle("SignalEditBox Test")
	lay = QVBoxLayout(win)

	numeric_sig = _build_numeric_signal()
	choice_sig = _build_choice_signal()

	editor = SignalEditBox(signal=numeric_sig)
	lay.addWidget(editor)

	result = QLabel("")
	lay.addWidget(result)

	btn_numeric = QPushButton("Use Numeric Signal")
	btn_choice = QPushButton("Use Choice Signal")
	btn_print = QPushButton("Print Current")

	def _use_numeric():
		editor.set_signal(numeric_sig)
		result.setText("Mode: Numeric")

	def _use_choice():
		editor.set_signal(choice_sig)
		result.setText("Mode: Choice")

	def _print_current():
		sig = editor.signal()
		if sig is None:
			text = "No SignalFilter"
		else:
			text = f"sig={sig.signal_name}, raw={sig.rawvalue}, value={sig.value}, choice={bool(sig.is_choice_value)}"
		print(text)
		result.setText(text)

	btn_numeric.clicked.connect(_use_numeric)
	btn_choice.clicked.connect(_use_choice)
	btn_print.clicked.connect(_print_current)

	lay.addWidget(btn_numeric)
	lay.addWidget(btn_choice)
	lay.addWidget(btn_print)

	win.resize(520, 180)
	win.show()
	sys.exit(app.exec())
