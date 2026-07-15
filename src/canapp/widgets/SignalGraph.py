from dataclasses import dataclass
from typing import Dict, Iterable, Optional
import uuid
import random

import numpy as np
import pyqtgraph as pg
from PySide6 import QtCore, QtGui, QtWidgets


@dataclass
class SignalSpec:
	name: str
	message_name: str
	x: np.ndarray
	y: np.ndarray
	kind: str = "numeric"
	choice_labels: Optional[Dict[int, str]] = None
	y_min: Optional[float] = None
	y_max: Optional[float] = None
	color: Optional[str] = None
	x_axis_offset: int = 0
	unit: str = ""


@dataclass
class _SignalRuntime:
	spec: SignalSpec
	view: pg.ViewBox
	axis: pg.AxisItem
	curve: pg.PlotDataItem
	pen_color: str


class CtrlZoomViewBox(pg.ViewBox):
	"""
	Wheel behavior:
	- Wheel: scroll parent list
	- Ctrl + Wheel: zoom
	"""

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._is_panning = False

	def wheelEvent(self, ev, axis=None):
		modifiers = QtWidgets.QApplication.keyboardModifiers()
		if modifiers & QtCore.Qt.KeyboardModifier.ControlModifier:
			super().wheelEvent(ev, axis=axis)
			return

		delta_y = 0
		delta_attr = getattr(ev, "delta", None)
		if callable(delta_attr):
			try:
				delta_y = int(delta_attr())
			except Exception:
				delta_y = 0
		if delta_y == 0 and hasattr(ev, "angleDelta"):
			try:
				delta_y = int(ev.angleDelta().y())
			except Exception:
				delta_y = 0

		scroll_step = int((delta_y / 120.0) * 48) if delta_y else 0
		if scroll_step == 0:
			scroll_step = -48 if delta_y < 0 else 48

		scene = self.scene()
		if scene is not None:
			for view in scene.views():
				parent = view.parentWidget()
				while parent is not None and not isinstance(parent, QtWidgets.QScrollArea):
					parent = parent.parentWidget()
				if isinstance(parent, QtWidgets.QScrollArea):
					bar = parent.verticalScrollBar()
					bar.setValue(bar.value() - scroll_step)
					ev.accept()
					return

		ev.ignore()

	def updateMouseCursor(self):
		if self._is_panning:
			self.setCursor(QtCore.Qt.CursorShape.ClosedHandCursor)
		else:
			self.setCursor(QtCore.Qt.CursorShape.ArrowCursor)

	def mousePressEvent(self, ev):
		if ev.button() == QtCore.Qt.MouseButton.LeftButton:
			self._is_panning = True
			self.setCursor(QtCore.Qt.CursorShape.ClosedHandCursor)
		super().mousePressEvent(ev)

	def mouseReleaseEvent(self, ev):
		super().mouseReleaseEvent(ev)
		if ev.button() == QtCore.Qt.MouseButton.LeftButton:
			self._is_panning = False
			self.setCursor(QtCore.Qt.CursorShape.ArrowCursor)

	def mouseDragEvent(self, ev, axis=None):
		if hasattr(ev, "isStart") and ev.isStart():
			self._is_panning = True
			self.setCursor(QtCore.Qt.CursorShape.ClosedHandCursor)

		super().mouseDragEvent(ev, axis=axis)

		if hasattr(ev, "isFinish") and ev.isFinish():
			self._is_panning = False
			self.setCursor(QtCore.Qt.CursorShape.ArrowCursor)


class SignalGraphWidget(QtWidgets.QFrame):
	mergeDropped = QtCore.Signal(str, str)  # target_graph_id, source_graph_id
	closeRequested = QtCore.Signal(str)  # graph_id
	heightChanged = QtCore.Signal(str, int)  # graph_id, new_height

	MIME_TYPE = "application/x-signal-graph-id"
	_GLOBAL_MUTED_POOL: list[str] = []
	_RESIZE_GRIP_HEIGHT = 8  # pixels from bottom edge for resize detection
	_MIN_GRAPH_HEIGHT = 120
	_MAX_GRAPH_HEIGHT = 800
	_X_LEFT_MARGIN_RATIO = 0.05
	_X_RIGHT_MARGIN_RATIO = 0.05
	_INTERVAL_ENTER_RATIO = 0.18
	_INTERVAL_EXIT_RATIO = 0.24
	_INTERVAL_MAX_TICKS = 20

	def __init__(self, parent: Optional[QtWidgets.QWidget] = None, initial_height: int = 220) -> None:
		super().__init__(parent)
		self.graph_id = str(uuid.uuid4())
		self._drag_start_pos: Optional[QtCore.QPoint] = None
		self._signals: Dict[str, _SignalRuntime] = {}
		self._hovered_signal: Optional[str] = None
		self._active_signal_name: Optional[str] = None
		self._interval_mode = False

		# Resize state
		self._is_resizing = False
		self._resize_start_y: Optional[int] = None
		self._resize_start_height: Optional[int] = None
		self._current_height = initial_height

		self.setAcceptDrops(True)
		self.setMouseTracking(True)
		self.setObjectName("signalGraphWidgetFrame")
		self.setFrameShape(QtWidgets.QFrame.Shape.Box)
		self.setFrameShadow(QtWidgets.QFrame.Shadow.Plain)
		self.setLineWidth(1)
		self.setMinimumHeight(self._MIN_GRAPH_HEIGHT)
		self.setMaximumHeight(self._MAX_GRAPH_HEIGHT)
		self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Preferred)

		self.setStyleSheet(
			"QFrame#signalGraphWidgetFrame {"
			"  border: 1px solid #808080;"
			"  border-radius: 4px;"
			"  background: #101014;"
			"}"
		)

		self._layout = QtWidgets.QVBoxLayout(self)
		self._layout.setContentsMargins(6, 6, 6, 6)

		self._close_button = QtWidgets.QToolButton(self)
		self._close_button.setText("✕")
		self._close_button.setToolTip("Close graph")
		self._close_button.setAutoRaise(True)
		self._close_button.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
		self._close_button.setFixedSize(16, 16)
		self._close_button.clicked.connect(self._on_close_clicked)
		self._close_button.raise_()

		self.plot_widget = pg.PlotWidget(viewBox=CtrlZoomViewBox())
		self.plot_widget.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
		self.plot_widget.setLineWidth(0)
		self._layout.addWidget(self.plot_widget)

		self.plot_item = self.plot_widget.getPlotItem()
		self.main_view = self.plot_item.vb
		self.main_axis_bottom = self.plot_item.getAxis("bottom")
		self.main_axis_left = self.plot_item.getAxis("left")
		self.main_axis_bottom.setLabel("[s]")
		self.main_axis_left.setLabel("")
		self.main_axis_bottom.setStyle(stopAxisAtTick=(True, True))
		self.main_axis_left.setStyle(stopAxisAtTick=(True, True))

		self.plot_item.showGrid(x=True, y=True, alpha=0.2)
		self.main_view.sigResized.connect(self._sync_child_views)
		self.main_view.sigRangeChanged.connect(self._update_axis_arrows)
		self.main_view.sigRangeChanged.connect(self._update_relative_time_ticks)
		self.main_view.setMouseEnabled(x=True, y=False)
		self.main_view.enableAutoRange(axis=pg.ViewBox.YAxis, enable=False)

		self._x_axis_arrow = pg.ArrowItem(angle=0, headLen=11, tipAngle=25, baseAngle=18)
		self._y_axis_arrow = pg.ArrowItem(angle=90, headLen=11, tipAngle=25, baseAngle=18)
		self.plot_item.addItem(self._x_axis_arrow)
		self.plot_item.addItem(self._y_axis_arrow)

		unit_font = QtGui.QFont()
		unit_font.setPointSize(9)
		unit_color = pg.mkColor("#9fb4cc")

		self._y_unit_text = pg.TextItem("", anchor=(1, 1))
		self._x_unit_text = pg.TextItem("", anchor=(1, 0))
		self._y_exp_text = pg.TextItem("", anchor=(0, 1))
		for _ti in (self._y_unit_text, self._x_unit_text, self._y_exp_text):
			_ti.setColor(unit_color)
			_ti.setFont(unit_font)
			_ti.setZValue(1000)
		self.plot_item.addItem(self._y_unit_text)
		self.plot_item.addItem(self._x_unit_text)
		self.plot_item.addItem(self._y_exp_text)
		self._y_unit_text.hide()
		self._x_unit_text.hide()
		self._y_exp_text.hide()

		self._hover_marker = pg.ScatterPlotItem(size=8, brush=pg.mkBrush("#ffffff"), pen=pg.mkPen("#000000", width=1))
		self._hover_text = pg.TextItem(anchor=(0, 1))
		self._hover_marker.setZValue(2000)
		self._hover_text.setZValue(2001)
		self.plot_item.addItem(self._hover_marker)
		self.plot_item.addItem(self._hover_text)
		self._hover_marker.hide()
		self._hover_text.hide()

		self._mouse_proxy = pg.SignalProxy(
			self.plot_item.scene().sigMouseMoved,
			rateLimit=60,
			slot=self._on_scene_mouse_moved,
		)

		self._position_close_button()

	def add_signal(
		self,
		message_name: str,
		name: str,
		x_data: Iterable[float],
		y_data: Iterable[float],
		y_min: Optional[float] = None,
		y_max: Optional[float] = None,
		x_axis_offset: int = 0,
		unit: str = "",
	) -> None:
		if name in self._signals:
			raise ValueError(f"Signal '{name}' already exists in graph pane")

		x_np = np.asarray(x_data, dtype=float)
		y_np = np.asarray(y_data, dtype=float)
		if x_np.shape[0] != y_np.shape[0]:
			raise ValueError(f"x and y size mismatch for signal '{name}'")

		spec = SignalSpec(
			name=name,
			message_name=message_name,
			x=x_np,
			y=y_np,
			kind="numeric",
			y_min=y_min,
			y_max=y_max,
			color=self._next_color(),
			x_axis_offset=max(0, int(x_axis_offset)),
			unit=unit,
		)

		if not self._signals:
			self._add_as_primary(spec)
		else:
			self._add_as_secondary(spec)

		if self._active_signal_name is None:
			self._active_signal_name = spec.name

		self._apply_stable_y_range()
		self._sync_child_views()
		self._update_relative_time_ticks()
		self._update_y_axis_end_labels(spec)
		self.plot_widget.update()

	def add_choice_signal(
		self,
		message_name: str,
		name: str,
		x_data: Iterable[float],
		y_data: Dict[int, str],
		sample_values: Optional[Iterable[int]] = None,
		x_axis_offset: int = 0,
		unit: str = "",
	) -> None:
		if name in self._signals:
			raise ValueError(f"Signal '{name}' already exists in graph pane")

		if not y_data:
			raise ValueError("Choice signal requires non-empty y_data dict[int, str]")

		x_np = np.asarray(x_data, dtype=float)
		if sample_values is None:
			first_key = sorted(y_data.keys())[0]
			y_np = np.full(shape=x_np.shape, fill_value=first_key, dtype=float)
		else:
			y_np = np.asarray(sample_values, dtype=float)

		if x_np.shape[0] != y_np.shape[0]:
			raise ValueError(f"x and sample_values size mismatch for choice signal '{name}'")

		spec = SignalSpec(
			name=name,
			message_name=message_name,
			x=x_np,
			y=y_np,
			kind="choice",
			choice_labels={int(k): str(v) for k, v in y_data.items()},
			y_min=float(min(y_data.keys())),
			y_max=float(max(y_data.keys())),
			color=self._next_color(),
			x_axis_offset=max(0, int(x_axis_offset)),
			unit=unit,
		)

		if not self._signals:
			self._add_as_primary(spec)
		else:
			self._add_as_secondary(spec)

		if self._active_signal_name is None:
			self._active_signal_name = spec.name

		self._apply_stable_y_range()
		self._sync_child_views()
		self._update_relative_time_ticks()
		self._update_y_axis_end_labels(spec)
		self.plot_widget.update()

	def export_signals(self) -> list[SignalSpec]:
		specs: list[SignalSpec] = []
		for runtime in self._signals.values():
			src = runtime.spec
			specs.append(
				SignalSpec(
					name=src.name,
					message_name=src.message_name,
					x=np.array(src.x, copy=True),
					y=np.array(src.y, copy=True),
					kind=src.kind,
					choice_labels=dict(src.choice_labels) if src.choice_labels else None,
					y_min=src.y_min,
					y_max=src.y_max,
					color=src.color,
					x_axis_offset=src.x_axis_offset,
					unit=src.unit,
				)
			)
		return specs

	def merge_from(self, other: "SignalGraphWidget") -> None:
		existing_names = set(self._signals.keys())
		for spec in other.export_signals():
			unique_name = spec.name
			suffix = 2
			while unique_name in existing_names:
				unique_name = f"{spec.name}_{suffix}"
				suffix += 1
			spec.name = unique_name
			existing_names.add(unique_name)
			if spec.kind == "choice":
				self.add_choice_signal(
					message_name=spec.message_name,
					name=spec.name,
					x_data=spec.x,
					y_data=spec.choice_labels or {},
					sample_values=spec.y,
					x_axis_offset=spec.x_axis_offset,
					unit=spec.unit,
				)
			else:
				self.add_signal(
					message_name=spec.message_name,
					name=spec.name,
					x_data=spec.x,
					y_data=spec.y,
					y_min=spec.y_min,
					y_max=spec.y_max,
					x_axis_offset=spec.x_axis_offset,
					unit=spec.unit,
				)

	def _add_as_primary(self, spec: SignalSpec) -> None:
		line_color = spec.color or self._next_color()
		pen = pg.mkPen(line_color, width=1.8)
		curve = self.plot_item.plot(spec.x, spec.y, pen=pen, name=spec.name)
		self._set_title(spec.message_name, spec.name)
		self._set_main_y_axis_color()

		x_min = float(np.min(spec.x))
		x_max = float(np.max(spec.x))
		if x_max > x_min:
			x_left, x_right = self._x_bounds_with_margins(x_min, x_max)
			self.main_view.setXRange(x_left, x_right, padding=0.0)
			self.main_view.setLimits(xMin=x_left, xMax=x_right)

		runtime = _SignalRuntime(
			spec=spec,
			view=self.main_view,
			axis=self.main_axis_bottom,
			curve=curve,
			pen_color=line_color,
		)
		self._signals[spec.name] = runtime

	def _add_as_secondary(self, spec: SignalSpec):
		view = CtrlZoomViewBox()
		view.setMouseEnabled(x=True, y=False)
		view.enableAutoRange(axis=pg.ViewBox.YAxis, enable=False)
		view.setYLink(self.main_view)

		self.plot_item.scene().addItem(view)

		axis = pg.AxisItem(orientation="bottom")
		axis.linkToView(view)
		axis.setLabel("[s]")
		axis.setStyle(stopAxisAtTick=(True, True))
		axis.setStyle(tickTextOffset=2)

		current_rows = len(self._signals)
		row = 3 + current_rows
		self.plot_item.layout.addItem(axis, row, 1)
		axis.setHeight(30)

		line_color = spec.color or self._next_color()
		pen = pg.mkPen(line_color, width=1.6)
		curve = pg.PlotDataItem(spec.x, spec.y, pen=pen, name=spec.name)
		view.addItem(curve)

		runtime = _SignalRuntime(spec=spec, view=view, axis=axis, curve=curve, pen_color=line_color)
		self._signals[spec.name] = runtime

		x_min = float(np.min(spec.x))
		x_max = float(np.max(spec.x))
		if x_max > x_min:
			x_left, x_right = self._x_bounds_with_margins(x_min, x_max)
			view.setXRange(x_left, x_right, padding=0.0)
			view.setLimits(xMin=x_left, xMax=x_right)

		if len(self._signals) == 2:
			self._set_title(spec.message_name, spec.name)

	def _x_bounds_with_margins(self, x_min: float, x_max: float) -> tuple[float, float]:
		span = float(x_max - x_min)
		if span <= 0.0:
			return x_min, x_max
		left_margin = span * self._X_LEFT_MARGIN_RATIO
		right_margin = span * self._X_RIGHT_MARGIN_RATIO
		return x_min - left_margin, x_max + right_margin

	def _apply_stable_y_range(self) -> None:
		if not self._signals:
			return

		active = self._signals.get(self._active_signal_name) if self._active_signal_name else None
		if active and active.spec.kind == "choice" and active.spec.choice_labels:
			self.main_axis_left.setStyle(stopAxisAtTick=(False, False), hideOverlappingLabels=False)
			keys = sorted(active.spec.choice_labels.keys())
			lower = float(keys[0]) - 0.5
			upper = float(keys[-1]) + 0.5
			self.main_view.setLimits(yMin=lower, yMax=upper)
			self.main_view.setYRange(lower, upper, padding=0.0)
			self._set_choice_ticks(active.spec.choice_labels)
			return

		self.main_axis_left.setStyle(stopAxisAtTick=(True, True), hideOverlappingLabels=True)
		self.main_axis_left.setTicks(None)

		y_min = float("inf")
		y_max = float("-inf")
		for runtime in self._signals.values():
			y_arr = np.asarray(runtime.spec.y, dtype=float)
			if y_arr.size == 0:
				continue
			finite = y_arr[np.isfinite(y_arr)]
			if finite.size == 0:
				continue
			y_min = min(y_min, float(np.min(finite)))
			y_max = max(y_max, float(np.max(finite)))

		if not np.isfinite(y_min) or not np.isfinite(y_max):
			return

		for runtime in self._signals.values():
			if runtime.spec.y_min is not None:
				y_min = min(y_min, float(runtime.spec.y_min))
			if runtime.spec.y_max is not None:
				y_max = max(y_max, float(runtime.spec.y_max))

		span = y_max - y_min
		if span <= 0:
			span = max(abs(y_min), 1.0) * 0.1

		pad = span * 0.05
		lower = y_min - pad
		upper = y_max + pad

		self.main_view.setLimits(yMin=lower, yMax=upper)
		self.main_view.setYRange(lower, upper, padding=0.0)

	def _set_choice_ticks(self, labels: Dict[int, str]) -> None:
		ticks = []
		for key in sorted(labels.keys()):
			ticks.append((float(key), labels[key]))
		self.main_axis_left.setTicks([ticks])

	def _on_scene_mouse_moved(self, evt) -> None:
		if not evt:
			self._clear_hover()
			return

		scene_pos = evt[0]
		if not self.plot_item.sceneBoundingRect().contains(scene_pos):
			self._clear_hover()
			return

		best_name: Optional[str] = None
		best_x = 0.0
		best_y = 0.0
		best_dist = float("inf")

		for name, runtime in self._signals.items():
			x_arr = runtime.spec.x
			y_arr = runtime.spec.y
			if x_arr.size == 0:
				continue

			view_pos = runtime.view.mapSceneToView(scene_pos)
			x_guess = view_pos.x()
			idx = int(np.searchsorted(x_arr, x_guess))
			candidate_indices = {max(0, min(len(x_arr) - 1, idx + offset)) for offset in (-2, -1, 0, 1, 2)}

			for candidate in candidate_indices:
				x_val = float(x_arr[candidate])
				y_val = float(y_arr[candidate])
				pt_scene = runtime.view.mapViewToScene(QtCore.QPointF(x_val, y_val))
				dist = np.hypot(scene_pos.x() - pt_scene.x(), scene_pos.y() - pt_scene.y())
				if dist < best_dist:
					best_dist = dist
					best_name = name
					best_x = x_val
					best_y = y_val

		threshold_px = 12.0
		if best_name is None or best_dist > threshold_px:
			self._clear_hover()
			return

		runtime = self._signals[best_name]
		self._hovered_signal = best_name
		self._active_signal_name = best_name
		self._set_main_y_axis_color()
		self._set_title(runtime.spec.message_name, runtime.spec.name)
		self._update_y_axis_end_labels(runtime.spec)

		self._hover_marker.setData([best_x], [best_y])
		self._hover_marker.setPen(pg.mkPen(runtime.pen_color, width=2))
		self._hover_marker.setBrush(pg.mkBrush("#ffffff"))
		self._hover_marker.show()

		if runtime.spec.kind == "choice" and runtime.spec.choice_labels:
			raw_key = int(round(best_y))
			value_text = runtime.spec.choice_labels.get(raw_key, str(raw_key))
		else:
			value_text = f"{best_y:.6f}"

		self._hover_text.setText(f"{best_x:.6f}, {value_text}")
		self._hover_text.setPos(best_x, best_y)
		self._hover_text.show()

	def _clear_hover(self) -> None:
		self._hovered_signal = None
		self._hover_marker.hide()
		self._hover_text.hide()

	def _set_main_y_axis_color(self) -> None:
		return

	def _sync_child_views(self) -> None:
		rect = self.main_view.sceneBoundingRect()
		for runtime in self._signals.values():
			if runtime.view is self.main_view:
				continue
			horizontal_offset = max(0, int(runtime.spec.x_axis_offset))
			inset_width = max(10.0, rect.width() - horizontal_offset)
			inset_rect = QtCore.QRectF(rect.left() + horizontal_offset, rect.top(), inset_width, rect.height())
			runtime.view.setGeometry(inset_rect)
			runtime.view.linkedViewChanged(self.main_view, runtime.view.XAxis)
		self._update_axis_arrows()
		self._update_relative_time_ticks()

	def _update_axis_arrows(self, *args) -> None:
		x_range, y_range = self.main_view.viewRange()
		x_min, x_max = x_range
		y_min, y_max = y_range

		dx = max((x_max - x_min) * 0.02, 1e-9)
		dy = max((y_max - y_min) * 0.04, 1e-9)

		self._x_axis_arrow.setPos(x_max, y_min + 0.5 * dy)
		self._y_axis_arrow.setPos(x_min + dx, y_max)

		if self._active_signal_name and self._active_signal_name in self._signals:
			runtime = self._signals[self._active_signal_name]
			self._update_y_axis_end_labels(runtime.spec)

	def _update_y_axis_end_labels(self, spec: SignalSpec) -> None:
		x_range, y_range = self.main_view.viewRange()
		x_min, x_max = x_range
		y_min, y_max = y_range

		dx = max((x_max - x_min) * 0.025, 1e-9)
		dy = max((y_max - y_min) * 0.05, 1e-9)

		self.main_axis_left.setLabel(f"[{spec.unit}]" if spec.unit else "")
		self._y_unit_text.hide()
		self._x_unit_text.hide()

		if spec.kind == "choice":
			self.main_axis_left.setScale(1.0)
			self._y_exp_text.hide()
			return

		y_abs_max = max(abs(y_min), abs(y_max))
		if y_abs_max >= 1000:
			exp = int(np.floor(np.log10(y_abs_max)))
			if exp >= 3:
				scale = 10.0 ** (-exp)
				self.main_axis_left.setScale(scale)
				self._y_exp_text.setText(f"+1e{exp}")
				self._y_exp_text.setPos(x_min + dx, y_max - 1.35 * dy)
				self._y_exp_text.show()
				return

		self.main_axis_left.setScale(1.0)
		self._y_exp_text.hide()

	def _update_relative_time_ticks(self, *args) -> None:
		if not self._signals:
			self._interval_mode = False
			self.main_axis_bottom.setLabel("")
			self._x_unit_text.hide()
			return

		runtime = next((r for r in self._signals.values() if r.view is self.main_view), None)
		if runtime is None:
			active_name = self._active_signal_name or next(iter(self._signals.keys()))
			runtime = self._signals.get(active_name)
		if runtime is None:
			self.main_axis_bottom.setTicks(None)
			self._interval_mode = False
			self.main_axis_bottom.setLabel("")
			return

		x_arr = np.asarray(runtime.spec.x, dtype=float)
		if x_arr.size < 2:
			self.main_axis_bottom.setTicks(None)
			self._interval_mode = False
			self.main_axis_bottom.setLabel("[s]")
			self._x_unit_text.hide()
			return

		x_min, x_max = self.main_view.viewRange()[0]
		full_span = float(x_arr[-1] - x_arr[0]) if x_arr.size > 1 else 0.0
		view_span = float(x_max - x_min)

		if full_span <= 0:
			self.main_axis_bottom.setTicks(None)
			self._interval_mode = False
			self.main_axis_bottom.setLabel("[s]")
			self._x_unit_text.hide()
			return

		ratio = view_span / full_span
		enter_threshold = self._INTERVAL_ENTER_RATIO
		exit_threshold = self._INTERVAL_EXIT_RATIO
		if self._interval_mode:
			self._interval_mode = ratio <= exit_threshold
		else:
			self._interval_mode = ratio <= enter_threshold

		if not self._interval_mode:
			self.main_axis_bottom.setTicks(None)
			self.main_axis_bottom.setLabel("[s]")
			self._x_unit_text.hide()
			return

		visible = np.where((x_arr >= x_min) & (x_arr <= x_max))[0]
		if visible.size < 2:
			self.main_axis_bottom.setTicks(None)
			self.main_axis_bottom.setLabel("[ms]")
			self._x_unit_text.hide()
			return

		if visible.size > self._INTERVAL_MAX_TICKS:
			stride = int(np.ceil(visible.size / self._INTERVAL_MAX_TICKS))
			visible = visible[::max(1, stride)]

		ticks = []
		for idx in visible:
			if idx <= 0:
				continue
			dt_ms = (x_arr[idx] - x_arr[idx - 1]) * 1000.0
			label = f"{dt_ms:.0f}" if abs(dt_ms - round(dt_ms)) < 0.05 else f"{dt_ms:.2f}"
			ticks.append((float(x_arr[idx]), label))

		if ticks:
			self.main_axis_bottom.setTicks([ticks])
		else:
			self.main_axis_bottom.setTicks(None)
		self.main_axis_bottom.setLabel("[ms]")
		self._x_unit_text.hide()

	def _set_title(self, message_name: str, signal_name: str) -> None:
		title = f"{message_name} - {signal_name}" if message_name else signal_name
		self.plot_item.setTitle(title)

	def _next_color(self) -> str:
		if not SignalGraphWidget._GLOBAL_MUTED_POOL:
			SignalGraphWidget._GLOBAL_MUTED_POOL = self._build_muted_color_pool()
		return SignalGraphWidget._GLOBAL_MUTED_POOL.pop()

	def _position_close_button(self) -> None:
		margin = 6
		x = max(0, self.width() - self._close_button.width() - margin)
		self._close_button.move(x, margin)

	def _on_close_clicked(self) -> None:
		self.closeRequested.emit(self.graph_id)

	def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
		super().resizeEvent(event)
		self._position_close_button()

	@staticmethod
	def _build_muted_color_pool() -> list[str]:
		palette = [
			"#5c6b73",
			"#6d597a",
			"#7f5539",
			"#4a6fa5",
			"#6b705c",
			"#7b2d26",
			"#5e6472",
			"#525b76",
			"#6a7f7a",
			"#7a6c5d",
			"#5b5f97",
			"#4f6d7a",
		]
		random.shuffle(palette)
		return palette

	def _is_in_resize_zone(self, pos: QtCore.QPoint) -> bool:
		"""Check if cursor position is within the resize grip zone at bottom edge."""
		return self.height() - pos.y() <= self._RESIZE_GRIP_HEIGHT

	def setGraphHeight(self, height: int) -> None:
		"""Set the graph height (clamped to min/max)."""
		clamped = max(self._MIN_GRAPH_HEIGHT, min(self._MAX_GRAPH_HEIGHT, height))
		self._current_height = clamped
		self.setFixedHeight(clamped)
		self.heightChanged.emit(self.graph_id, clamped)

	def graphHeight(self) -> int:
		"""Return the current graph height."""
		return self._current_height

	def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
		if event.button() == QtCore.Qt.MouseButton.LeftButton:
			if self._is_in_resize_zone(event.pos()):
				# Start resizing
				self._is_resizing = True
				self._resize_start_y = event.globalPos().y()
				self._resize_start_height = self.height()
				event.accept()
				return
			else:
				self._drag_start_pos = event.pos()
		super().mousePressEvent(event)

	def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
		# Handle resize cursor appearance when not pressing
		if not (event.buttons() & QtCore.Qt.MouseButton.LeftButton):
			if self._is_in_resize_zone(event.pos()):
				self.setCursor(QtCore.Qt.CursorShape.SizeVerCursor)
			else:
				self.unsetCursor()
			super().mouseMoveEvent(event)
			return

		# Handle active resizing
		if self._is_resizing and self._resize_start_y is not None:
			delta = event.globalPos().y() - self._resize_start_y
			new_height = self._resize_start_height + delta
			self.setGraphHeight(new_height)
			event.accept()
			return

		if self._drag_start_pos is None:
			super().mouseMoveEvent(event)
			return

		if (event.pos() - self._drag_start_pos).manhattanLength() < QtWidgets.QApplication.startDragDistance():
			super().mouseMoveEvent(event)
			return

		mime = QtCore.QMimeData()
		mime.setData(self.MIME_TYPE, self.graph_id.encode("utf-8"))

		drag = QtGui.QDrag(self)
		drag.setMimeData(mime)
		drag.exec(QtCore.Qt.DropAction.MoveAction)

	def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:
		if event.button() == QtCore.Qt.MouseButton.LeftButton:
			if self._is_resizing:
				self._is_resizing = False
				self._resize_start_y = None
				self._resize_start_height = None
				self.unsetCursor()
				event.accept()
				return
			self._drag_start_pos = None
		super().mouseReleaseEvent(event)

	def leaveEvent(self, event: QtCore.QEvent) -> None:
		if not self._is_resizing:
			self.unsetCursor()
		super().leaveEvent(event)

	def dragEnterEvent(self, event: QtGui.QDragEnterEvent) -> None:
		if event.mimeData().hasFormat(self.MIME_TYPE):
			source_id = bytes(event.mimeData().data(self.MIME_TYPE)).decode("utf-8")
			if source_id != self.graph_id:
				event.acceptProposedAction()
				return
		event.ignore()

	def dragMoveEvent(self, event: QtGui.QDragMoveEvent) -> None:
		self.dragEnterEvent(event)

	def dropEvent(self, event: QtGui.QDropEvent) -> None:
		if not event.mimeData().hasFormat(self.MIME_TYPE):
			event.ignore()
			return

		source_id = bytes(event.mimeData().data(self.MIME_TYPE)).decode("utf-8")
		if source_id == self.graph_id:
			event.ignore()
			return

		self.mergeDropped.emit(self.graph_id, source_id)
		event.acceptProposedAction()

__all__ = ["SignalSpec", "SignalGraphWidget"]


if __name__ == "__main__":
	app = QtWidgets.QApplication([])

	window = QtWidgets.QMainWindow()
	window.setWindowTitle("SignalGraphWidget Demo")
	window.resize(1100, 520)

	graph = SignalGraphWidget()
	graph.setFixedHeight(420)

	# Demo data
	# time vector
	x = np.linspace(0.0, 10.0, 500)

	# numeric example (optional)
	# np.random.seed(11)
	# y = 8.0 + 0.3 * np.sin(2.1 * x) + 0.02 * np.random.randn(x.size)
	# graph.add_signal(
	# 	message_name="MSG_FV081",
	# 	name="FV081_FVTx",
	# 	x_data=x,
	# 	y_data=y,
	# 	x_axis_offset=0,
	# 	unit="km/h",
	# )

	# choice (categorical) demo
	choice_labels = {0: "OFF", 1: "IDLE", 2: "READY", 3: "RUN", 4: "FAULT"}
	choice_samples = np.random.choice([0, 1, 2, 3, 4], size=x.size)
	graph.add_choice_signal(
		message_name="MSG_MODE",
		name="DriveMode",
		x_data=x,
		y_data=choice_labels,
		sample_values=choice_samples,
		x_axis_offset=20,
		unit="state",
	)

	window.setCentralWidget(graph)
	window.show()
	app.exec()
