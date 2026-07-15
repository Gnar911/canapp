import sys
from decimal import Decimal, InvalidOperation
from typing import Callable
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QAbstractSlider
from qtrangeslider import QRangeSlider
from PySide6.QtWidgets import QStyle, QStyleOptionSlider
QRangeSlider.SliderChange = QAbstractSlider.SliderChange

class RangeSliderWithLabels(QWidget):
    valueChanged = Signal(tuple)  # emits external (lo, hi)
    indexValueChanged = Signal(tuple)  # emits (lo_idx, hi_idx) in real time
    handleIndexChanged = Signal(int, int)  # emits (handle_id, index), handle_id: 0=low, 1=high

    def __init__(self, parent=None):
        super().__init__(parent)

        self.slider = QRangeSlider(Qt.Horizontal)
        self._real_min = 0.0
        self._real_max = 100.0
        self._data_points = None
        self._sparse_total_count = None
        self._sparse_value_cache = {}
        self._sparse_resolver: Callable[[int], float | None] | None = None
        self._resolve_debounce_ms = 20
        self._resolve_timer = QTimer(self)
        self._resolve_timer.setSingleShot(True)
        self._resolve_timer.timeout.connect(self._resolve_visible_points)
        self._decimals = 0
        self._steps = 1000

        self.slider.setRange(0, self._steps)
        self.slider.setValue((0, self._steps))
        self.slider.setFixedHeight(28)

        self.label_min = QLabel(self)
        self.label_max = QLabel(self)

        for lb in (self.label_min, self.label_max):
            lb.setAlignment(Qt.AlignCenter)
            lb.setStyleSheet("""
                QLabel {
                    background: #555;
                    color: white;
                    padding: 4px 8px;
                    border-radius: 6px;
                    font-size: 11px;
                }
            """)
            lb.adjustSize()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 32, 16, 16)
        layout.addWidget(self.slider)

        self.slider.valueChanged.connect(self._on_slider_value_changed)

        self.set_range(1000, 2213)
        self._last_lo_idx, self._last_hi_idx = self.get_index_value()
        self._update_labels()

    def _default_value_thirds(self) -> tuple[float, float]:
        if self._data_points:
            max_idx = len(self._data_points) - 1
            lo_idx = int(round(max_idx / 3.0))
            hi_idx = int(round((2.0 * max_idx) / 3.0))
            return self._data_points[lo_idx], self._data_points[hi_idx]
        span = self._real_max - self._real_min
        lo = self._real_min + span / 3.0
        hi = self._real_min + (2.0 * span) / 3.0
        return lo, hi

    def _format_value(self, value: float) -> str:
        if self._decimals <= 0:
            return str(int(round(value)))
        return f"{value:.{self._decimals}f}"

    def _slider_to_real(self, slider_value: int) -> float:
        if self._data_points:
            idx = max(0, min(int(slider_value), len(self._data_points) - 1))
            return float(self._data_points[idx])

        if self._sparse_total_count is not None:
            idx = max(0, min(int(slider_value), int(self._sparse_total_count) - 1))
            cached = self._sparse_value_cache.get(idx)
            if cached is not None:
                return float(cached)
            if self._sparse_total_count <= 1:
                return self._real_min
            ratio = float(idx) / float(int(self._sparse_total_count) - 1)
            return self._real_min + ratio * (self._real_max - self._real_min)

        if self._steps <= 0:
            return self._real_min
        ratio = float(slider_value) / float(self._steps)
        return self._real_min + ratio * (self._real_max - self._real_min)

    def _real_to_slider(self, real_value: float) -> int:
        if self._data_points:
            target = float(real_value)
            nearest_idx = min(range(len(self._data_points)), key=lambda i: abs(self._data_points[i] - target))
            return int(nearest_idx)

        if self._sparse_total_count is not None:
            if self._real_max == self._real_min or int(self._sparse_total_count) <= 1:
                return 0
            clamped = max(self._real_min, min(float(real_value), self._real_max))
            ratio = (clamped - self._real_min) / (self._real_max - self._real_min)
            max_idx = int(self._sparse_total_count) - 1
            return int(round(ratio * max_idx))

        if self._real_max == self._real_min:
            return 0
        clamped = max(self._real_min, min(float(real_value), self._real_max))
        ratio = (clamped - self._real_min) / (self._real_max - self._real_min)
        return int(round(ratio * self._steps))

    def _on_slider_value_changed(self, slider_range):
        lo_idx, hi_idx = int(slider_range[0]), int(slider_range[1])

        # FPS-paced resolution for huge datasets: resolve by debounce timer,
        # not on every tiny move event.
        if self._sparse_total_count is not None and self._sparse_resolver is not None:
            self._resolve_timer.start(max(10, int(self._resolve_debounce_ms)))

        self._update_labels()
        self.valueChanged.emit(self.value())
        self.indexValueChanged.emit((lo_idx, hi_idx))

        moved_low = lo_idx != self._last_lo_idx
        moved_high = hi_idx != self._last_hi_idx

        if moved_low and not moved_high:
            self.handleIndexChanged.emit(0, lo_idx)
        elif moved_high and not moved_low:
            self.handleIndexChanged.emit(1, hi_idx)

        self._last_lo_idx, self._last_hi_idx = lo_idx, hi_idx

    def _detect_decimals_from_value(self, raw_value) -> int:
        try:
            value_dec = Decimal(str(raw_value))
        except (InvalidOperation, ValueError):
            return 0
        exponent = value_dec.as_tuple().exponent
        return max(0, -int(exponent))

    def _resolve_index_value(self, idx: int):
        if self._sparse_resolver is None:
            return
        if idx in self._sparse_value_cache:
            return
        try:
            resolved = self._sparse_resolver(int(idx))
        except Exception:
            return
        if resolved is None:
            return
        try:
            self._sparse_value_cache[int(idx)] = float(resolved)
        except Exception:
            return

    def _resolve_visible_points(self):
        if self._sparse_total_count is None or self._sparse_resolver is None:
            return

        lo_idx, hi_idx = self.get_index_value()
        mid_idx = (int(lo_idx) + int(hi_idx)) // 2

        self._resolve_index_value(lo_idx)
        self._resolve_index_value(mid_idx)
        self._resolve_index_value(hi_idx)

        self._update_labels()
        self.valueChanged.emit(self.value())


    def _value_to_slider_x(self, value: float) -> int:
        """
        Map a slider value -> x coordinate (in *parent* coordinates)
        Works reliably even for qtrangeslider.
        """
        style = self.slider.style()

        opt = QStyleOptionSlider()
        opt.initFrom(self.slider)
        opt.orientation = Qt.Horizontal
        opt.minimum = int(self.slider.minimum())
        opt.maximum = int(self.slider.maximum())

        groove = style.subControlRect(QStyle.CC_Slider, opt, QStyle.SC_SliderGroove, self.slider)

        # handle length (used to keep center correct)
        handle_len = style.pixelMetric(QStyle.PM_SliderLength, opt, self.slider)

        # available travel distance for the handle *center*
        span = max(1, groove.width() - handle_len)

        pos = style.sliderPositionFromValue(
            opt.minimum,
            opt.maximum,
            int(value),
            span,
            opt.upsideDown
        )

        # x in slider-local coords (center of handle)
        x_local = groove.left() + pos + handle_len // 2

        # convert to parent coords
        x_parent = self.slider.mapToParent(groove.topLeft()).x() + (x_local - groove.left())
        return x_parent


    # ------------------------------------------------------------
    # Handle → label positioning
    # ------------------------------------------------------------
    def _update_labels(self):
        lo_raw, hi_raw = self.slider.value()
        lo = self._slider_to_real(lo_raw)
        hi = self._slider_to_real(hi_raw)

        self.label_min.setText(self._format_value(lo))
        self.label_max.setText(self._format_value(hi))
        self.label_min.adjustSize()
        self.label_max.adjustSize()

        x1 = self._value_to_slider_x(lo_raw)
        x2 = self._value_to_slider_x(hi_raw)

        y = self.slider.y() - self.label_min.height() - 6

        self.label_min.move(x1 - self.label_min.width() // 2, y)
        self.label_max.move(x2 - self.label_max.width() // 2, y)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._update_labels()

    def _get_handle_positions(self):
        """Return QRect for both slider handles (min, max)"""

        style = self.slider.style()

        opt = QStyleOptionSlider()
        self.slider.initStyleOption(opt)

        lo, hi = self.slider.value()

        # ---- min handle ----
        opt.sliderPosition = lo
        opt.sliderValue = lo
        min_rect = style.subControlRect(
            QStyle.CC_Slider,
            opt,
            QStyle.SC_SliderHandle,
            self.slider,
        )

        # ---- max handle ----
        opt.sliderPosition = hi
        opt.sliderValue = hi
        max_rect = style.subControlRect(
            QStyle.CC_Slider,
            opt,
            QStyle.SC_SliderHandle,
            self.slider,
        )

        return min_rect, max_rect
    # ------------------------------------------------------------
    # Public API (for your backend)
    # ------------------------------------------------------------
    def set_range(self, minimum: float, maximum: float, decimals: int | None = None, steps: int = 1000):
        minimum = float(minimum)
        maximum = float(maximum)

        if maximum < minimum:
            minimum, maximum = maximum, minimum

        if decimals is None:
            decimals = 0 if minimum.is_integer() and maximum.is_integer() else 3

        self._real_min = minimum
        self._real_max = maximum
        self._data_points = None
        self._sparse_total_count = None
        self._sparse_value_cache = {}
        self._decimals = max(0, int(decimals))
        self._steps = max(10, int(steps))

        self.slider.blockSignals(True)
        self.slider.setRange(0, self._steps)
        lo, hi = self._default_value_thirds()
        self.slider.setValue((self._real_to_slider(lo), self._real_to_slider(hi)))
        self.slider.blockSignals(False)
        self._update_labels()

    def set_data(self, data_points, decimals: int | None = None, sort_values: bool = False, unique: bool = False):
        raw_values = list(data_points)
        if not raw_values:
            return

        first_raw = raw_values[0]
        values = [float(v) for v in raw_values]
        if not values:
            return

        if unique:
            values = list(dict.fromkeys(values))
        if sort_values:
            values = sorted(values)

        self._data_points = values
        self._sparse_total_count = None
        self._sparse_value_cache = {}
        self._real_min = min(values)
        self._real_max = max(values)

        if decimals is None:
            self._decimals = self._detect_decimals_from_value(first_raw)
        else:
            self._decimals = max(0, int(decimals))

        max_idx = max(0, len(values) - 1)
        self._steps = max_idx

        self.slider.blockSignals(True)
        self.slider.setRange(0, max_idx)
        lo, hi = self._default_value_thirds()
        self.slider.setValue((self._real_to_slider(lo), self._real_to_slider(hi)))
        self.slider.blockSignals(False)
        self._update_labels()

    def value(self):
        lo_raw, hi_raw = self.slider.value()
        lo = self._slider_to_real(lo_raw)
        hi = self._slider_to_real(hi_raw)
        return (round(lo, self._decimals), round(hi, self._decimals))

    def set_sparse_data(self, first_value: float, last_value: float, total_count: int, decimals: int | None = None):
        """
        Large dataset mode: do not preload all points.

        Args:
            first_value: value at index 0
            last_value: value at index total_count-1
            total_count: total number of data points (can be millions)
            decimals: display decimals; auto-detected when None
        """
        total_count = max(2, int(total_count))
        first_value = float(first_value)
        last_value = float(last_value)

        if decimals is None:
            decimals = max(
                self._detect_decimals_from_value(first_value),
                self._detect_decimals_from_value(last_value),
            )

        self._data_points = None
        self._sparse_total_count = total_count
        self._real_min = first_value
        self._real_max = last_value
        self._decimals = max(0, int(decimals))

        max_idx = total_count - 1
        self._steps = max_idx

        self._sparse_value_cache = {
            0: first_value,
            max_idx: last_value,
        }

        self.slider.blockSignals(True)
        self.slider.setRange(0, max_idx)
        lo, hi = self._default_value_thirds()
        self.slider.setValue((self._real_to_slider(lo), self._real_to_slider(hi)))
        self.slider.blockSignals(False)

        self._last_lo_idx, self._last_hi_idx = self.get_index_value()
        self._resolve_visible_points()
        self._update_labels()

    def set_value_resolver(self, resolver: Callable[[int], float | None] | None, debounce_ms: int = 20):
        """
        Assign callback to lazily resolve an index -> real value.

        Resolver is called with an integer index and should return a float value
        (or None if unavailable). Calls are debounced while dragging.
        """
        self._sparse_resolver = resolver
        self._resolve_debounce_ms = max(10, min(30, int(debounce_ms)))

    def get_value(self):
        return self.value()

    def get_index_value(self):
        lo_raw, hi_raw = self.slider.value()
        return int(lo_raw), int(hi_raw)

    def set_value(self, lo: float, hi: float):
        lo_raw = self._real_to_slider(lo)
        hi_raw = self._real_to_slider(hi)
        if lo_raw > hi_raw:
            lo_raw, hi_raw = hi_raw, lo_raw
        self.slider.setValue((lo_raw, hi_raw))

    def set_index_value(self, lo_index: int, hi_index: int):
        lo_raw = int(lo_index)
        hi_raw = int(hi_index)
        if lo_raw > hi_raw:
            lo_raw, hi_raw = hi_raw, lo_raw
        lo_raw = max(int(self.slider.minimum()), min(lo_raw, int(self.slider.maximum())))
        hi_raw = max(int(self.slider.minimum()), min(hi_raw, int(self.slider.maximum())))
        self.slider.setValue((lo_raw, hi_raw))

    # Backward-compatible aliases
    def setRange(self, minimum: float, maximum: float, decimals: int | None = None, steps: int = 1000):
        self.set_range(minimum, maximum, decimals=decimals, steps=steps)

    def setValue(self, lo: float, hi: float):
        self.set_value(lo, hi)

    def getValue(self):
        return self.get_value()

    def getIndexValue(self):
        return self.get_index_value()

    # Backward-compatible aliases for sparse mode
    def setSparseData(self, first_value: float, last_value: float, total_count: int, decimals: int | None = None):
        self.set_sparse_data(first_value, last_value, total_count, decimals=decimals)

    def setValueResolver(self, resolver: Callable[[int], float | None] | None, debounce_ms: int = 20):
        self.set_value_resolver(resolver, debounce_ms=debounce_ms)


# ------------------------------------------------------------
# Demo usage
# ------------------------------------------------------------
class Demo(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Range Slider with Labels")

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        self.range_slider = RangeSliderWithLabels()
        layout.addWidget(self.range_slider)

        # External API usage example with data points:
        self.range_slider.set_data([1.2, 2.3, 3.4, 4.8, 5.9, 6.7, 7.8, 8.9, 9.0, 10.1], decimals=1)
        self.range_slider.set_value(2.4, 5.7)  # nearest available values are used

        # Getter APIs:
        print("Current value:", self.range_slider.get_value())
        print("Current index:", self.range_slider.get_index_value())

        # Real-time value signal (external values)
        self.range_slider.valueChanged.connect(
            lambda v: print(f"Replay window: {v[0]} → {v[1]}")
        )

        # Real-time index tuple signal
        self.range_slider.indexValueChanged.connect(
            lambda idx: print(f"Index range: {idx[0]} → {idx[1]}")
        )

        # Real-time moving handle signal
        self.range_slider.handleIndexChanged.connect(self._on_handle_index_changed)

    def _on_handle_index_changed(self, handle_id: int, index: int):
        handle_name = "LOW" if handle_id == 0 else "HIGH"
        print(f"Moving handle: {handle_name}, index={index}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = Demo()
    w.resize(420, 160)
    w.show()
    sys.exit(app.exec())
