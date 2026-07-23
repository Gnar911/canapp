import sys
from PySide6.QtCore import Qt, Signal, QEvent, QRectF
from PySide6 import QtGui
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QStyle, QStyleOptionSlider, QLabel
from canapp.widgets.basic_component.RangeSlider import RangeSliderWithLabels
# from canapp.replay_viewmodel import CANLogPlayer, ReplayStatus
# from canapp.canlog_viewmodel import LogContextViewModel, BasicFileLogContext, NoFilter, MsgFilter, SigFilter

class _ReplayProgressOverlay(QWidget):
    def __init__(self, owner, slider):
        super().__init__(slider)
        self._owner = owner
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

    def paintEvent(self, event):
        self._owner._paint_progress_overlay(event)

class ReplayTimescopeSlider(RangeSliderWithLabels):
    progressIndexChanged = Signal(int)

    def __init__(self, parent=None, player: CANLogPlayer | None = None, ctx_model: LogContextViewModel | None = None):
        self._progress_overlay = None
        self.label_progress = None
        super().__init__(parent)
        self._player: CANLogPlayer | None = None
        self._subscribed_player_ids: set[int] = set()
        self._ctx_model: LogContextViewModel | None = None
        self._subscribed_ctx_model_ids: set[int] = set()
        self._ctx: BasicFileLogContext | None = None
        self._subscribed_ctx_ids: set[int] = set()
        self._progress_index = self.get_index_value()[0]
        self._progress_visible = False
        self._progress_color = QtGui.QColor(56, 130, 89, 190)
        self._progress_border_color = QtGui.QColor(40, 95, 65, 230)

        self._progress_overlay = _ReplayProgressOverlay(self, self.slider)
        self._sync_progress_overlay_geometry()
        self._progress_overlay.setCursor(Qt.PointingHandCursor)
        self._progress_overlay.show()
        self._progress_overlay.raise_()

        self.label_progress = QLabel(self)
        self.label_progress.setAlignment(Qt.AlignCenter)
        self.label_progress.setStyleSheet("""
            QLabel {
                background: #356b4b;
                color: white;
                padding: 4px 8px;
                border-radius: 6px;
                font-size: 11px;
            }
        """)
        self.label_progress.hide()

        self.slider.installEventFilter(self)
        self.slider.setCursor(Qt.PointingHandCursor)
        self.slider.valueChanged.connect(lambda _: self._update_progress_visuals())
        self._update_progress_visuals()
        self.set_player(player)
        self.set_viewmodel(ctx_model)

    @staticmethod
    def _normalize_can_ids(can_ids) -> list[int]:
        result: list[int] = []
        seen: set[int] = set()
        if not can_ids:
            return result
        for raw_can_id in can_ids:
            try:
                can_id = int(raw_can_id)
            except Exception:
                continue
            if can_id in seen:
                continue
            seen.add(can_id)
            result.append(can_id)
        return result

    @staticmethod
    def _extract_sig_filter_can_ids(signals) -> list[int]:
        can_ids: list[int] = []
        seen: set[int] = set()
        if not signals:
            return can_ids
        for signal_filter in signals:
            can_id = getattr(signal_filter, "can_id", None)
            if can_id is None:
                continue
            try:
                cid = int(can_id)
            except Exception:
                continue
            if cid in seen:
                continue
            seen.add(cid)
            can_ids.append(cid)
        return can_ids

    def _set_full_scope_by_count(self, total_count: int):
        try:
            count = int(total_count)
        except Exception:
            return
        if count <= 1:
            return
        self.set_index_value(0, count - 1)

    def _bind_sparse_from_context(self):
        ctx = self._ctx
        if ctx is None:
            return

        d_filelog = getattr(ctx, "d_filelog", None)
        if d_filelog is None:
            return

        fs = getattr(ctx, "filter_state", NoFilter())

        def _bind_global():
            first_ts, last_ts = d_filelog.get_first_last_timestamp()
            if first_ts is None or last_ts is None:
                return
            total_count = int(getattr(d_filelog, "total_lines", 0) or 0)
            if total_count <= 0:
                return
            self.set_sparse_data(float(first_ts), float(last_ts), int(total_count), decimals=6)
            self.set_value_resolver(lambda idx: d_filelog.get_timestamp_by_row(int(idx)), debounce_ms=20)
            self._set_full_scope_by_count(total_count)

        if isinstance(fs, NoFilter):
            _bind_global()
            return

        if isinstance(fs, MsgFilter):
            can_ids = self._normalize_can_ids(fs.can_ids)
            if not can_ids:
                return

            is_changed = (fs.mode == MsgFilter.Type.FILTER_MSG_CHANGED)

            if len(can_ids) == 1:
                first_ts, last_ts = d_filelog.get_first_last_timestamp_by_can_id(can_ids[0])
                if is_changed:
                    total_count = int(d_filelog.get_changed_count_by_can_id(can_ids[0]))
                else:
                    total_count = int(d_filelog.get_total_count_by_can_id(can_ids[0]))
                if first_ts is None or last_ts is None or total_count <= 0:
                    return
                self.set_sparse_data(float(first_ts), float(last_ts), int(total_count), decimals=6)
                self.set_value_resolver(
                    lambda idx, cid=can_ids[0], changed=is_changed: d_filelog.get_timestamp_by_can_id_row(
                        cid,
                        int(idx),
                        changed=changed,
                    ),
                    debounce_ms=20,
                )
                self._set_full_scope_by_count(total_count)
                return

            first_ts, last_ts = d_filelog.get_first_last_timestamp_by_can_ids(can_ids)
            if is_changed:
                total_count = int(d_filelog.get_changed_count_by_can_ids(can_ids))
            else:
                total_count = int(d_filelog.get_total_count_by_can_ids(can_ids))
            if first_ts is None or last_ts is None or total_count <= 0:
                return
            self.set_sparse_data(float(first_ts), float(last_ts), int(total_count), decimals=6)
            self.set_value_resolver(
                lambda idx, cids=tuple(can_ids), changed=is_changed: d_filelog.get_timestamp_by_can_ids_row(
                    list(cids),
                    int(idx),
                    changed=changed,
                ),
                debounce_ms=20,
            )
            self._set_full_scope_by_count(total_count)
            return

        if isinstance(fs, SigFilter):
            can_ids = self._extract_sig_filter_can_ids(fs.signals)
            if not can_ids:
                _bind_global()
                return

            is_changed = (fs.mode == SigFilter.Type.FILTER_SIG_CHANGED)

            if len(can_ids) == 1:
                first_ts, last_ts = d_filelog.get_first_last_timestamp_by_can_id(can_ids[0])
                if is_changed:
                    total_count = int(d_filelog.get_changed_count_by_can_id(can_ids[0]))
                else:
                    total_count = int(d_filelog.get_total_count_by_can_id(can_ids[0]))
                if first_ts is None or last_ts is None or total_count <= 0:
                    return
                self.set_sparse_data(float(first_ts), float(last_ts), int(total_count), decimals=6)
                self.set_value_resolver(
                    lambda idx, cid=can_ids[0], changed=is_changed: d_filelog.get_timestamp_by_can_id_row(
                        cid,
                        int(idx),
                        changed=changed,
                    ),
                    debounce_ms=20,
                )
                self._set_full_scope_by_count(total_count)
                return

            first_ts, last_ts = d_filelog.get_first_last_timestamp_by_can_ids(can_ids)
            if is_changed:
                total_count = int(d_filelog.get_changed_count_by_can_ids(can_ids))
            else:
                total_count = int(d_filelog.get_total_count_by_can_ids(can_ids))
            if first_ts is None or last_ts is None or total_count <= 0:
                return
            self.set_sparse_data(float(first_ts), float(last_ts), int(total_count), decimals=6)
            self.set_value_resolver(
                lambda idx, cids=tuple(can_ids), changed=is_changed: d_filelog.get_timestamp_by_can_ids_row(
                    list(cids),
                    int(idx),
                    changed=changed,
                ),
                debounce_ms=20,
            )
            self._set_full_scope_by_count(total_count)
            return

        _bind_global()

    def _on_context_filter_state_changed(self, *_):
        self._bind_sparse_from_context()

    def set_context(self, ctx: BasicFileLogContext | None):
        self._ctx = ctx
        if ctx is None:
            return

        ctx_id = id(ctx)
        if ctx_id not in self._subscribed_ctx_ids:
            try:
                ctx.event_on_filter_state_changed.subscribe(self._on_context_filter_state_changed)
                self._subscribed_ctx_ids.add(ctx_id)
            except Exception:
                pass

        self._bind_sparse_from_context()

    def _on_context_changed(self, ctx: BasicFileLogContext | None):
        self.set_context(ctx)

    def set_viewmodel(self, ctx_model: LogContextViewModel | None):
        self._ctx_model = ctx_model
        if ctx_model is None:
            return

        model_id = id(ctx_model)
        if model_id not in self._subscribed_ctx_model_ids:
            try:
                ctx_model.event_on_context_changed.subscribe(self._on_context_changed)
                self._subscribed_ctx_model_ids.add(model_id)
            except Exception:
                pass

        self.set_context(getattr(ctx_model, "cur_ctx", None))

    def set_player(self, player: CANLogPlayer | None):
        self._player = player
        if player is None:
            return
        player_id = id(player)
        if player_id in self._subscribed_player_ids:
            return
        player.event_on_replay_status_changed.subscribe(self._on_replay_status_changed)
        self._subscribed_player_ids.add(player_id)

    def _on_replay_status_changed(self, status: ReplayStatus):
        if status is None:
            return
        st = getattr(status, "status", "")
        payload = getattr(status, "payload", {}) or {}

        if st == "STARTED":
            self._progress_visible = True
            start_ts = payload.get("replay_scope_start_ts", None)
            end_ts = payload.get("replay_scope_end_ts", None)
            if start_ts is not None and end_ts is not None:
                try:
                    self.set_value(float(start_ts), float(end_ts))
                except Exception:
                    pass

            progress_idx = payload.get("progress_index", payload.get("current_index", None))
            if progress_idx is not None:
                try:
                    self.set_progress_index(int(progress_idx))
                except Exception:
                    pass
            else:
                self.set_progress_index(self.get_index_value()[0])
            return

        if st == "PROGRESS":
            self._progress_visible = True
            progress_idx = payload.get("progress_index", payload.get("current_index", None))
            if progress_idx is None:
                return
            try:
                self.set_progress_index(int(progress_idx))
            except Exception:
                pass
            return

        if st in ("STOPPED", "FINISHED", "TIME_SCOPE_FINISHED", "IDLE", "EXIT"):
            self._progress_visible = False
            self._progress_index = self.get_index_value()[0]
            self._update_progress_visuals()

    def eventFilter(self, obj, event):
        if obj is self.slider and event.type() in (QEvent.Resize, QEvent.Move, QEvent.Show):
            self._sync_progress_overlay_geometry()
        return super().eventFilter(obj, event)

    def _sync_progress_overlay_geometry(self):
        if self._progress_overlay is not None:
            self._progress_overlay.setGeometry(self.slider.rect())

    def _effective_progress_index(self) -> int:
        lo_idx, hi_idx = self.get_index_value()
        return max(lo_idx, min(int(self._progress_index), hi_idx))

    def _update_progress_overlay(self):
        if self._progress_overlay is not None:
            self._progress_overlay.update()

    def _update_progress_label(self):
        if self._progress_index is None or self.label_progress is None:
            return
        if not self._progress_visible:
            self.label_progress.hide()
            return

        idx = self._effective_progress_index()
        value = self._slider_to_real(idx)
        self.label_progress.setText(self._format_value(value))
        self.label_progress.adjustSize()
        self.label_progress.show()

        x = self._value_to_slider_x(idx)
        y = self.slider.y() - self.label_progress.height() - 6
        self.label_progress.move(x - self.label_progress.width() // 2, y)

    def _update_progress_visuals(self):
        self._update_progress_overlay()
        self._update_progress_label()

    def _slider_value_to_local_x(self, value: int) -> int:
        style = self.slider.style()
        opt = QStyleOptionSlider()
        opt.initFrom(self.slider)
        opt.orientation = Qt.Horizontal
        opt.minimum = int(self.slider.minimum())
        opt.maximum = int(self.slider.maximum())

        groove = style.subControlRect(QStyle.CC_Slider, opt, QStyle.SC_SliderGroove, self.slider)
        handle_len = style.pixelMetric(QStyle.PM_SliderLength, opt, self.slider)
        span = max(1, groove.width() - handle_len)

        pos = style.sliderPositionFromValue(
            opt.minimum,
            opt.maximum,
            int(value),
            span,
            opt.upsideDown
        )
        return groove.left() + pos + handle_len // 2

    def _paint_progress_overlay(self, _event):
        if self._progress_index is None or not self._progress_visible:
            return

        lo_idx, hi_idx = self.get_index_value()
        cur_idx = max(lo_idx, min(int(self._progress_index), hi_idx))

        x1 = self._slider_value_to_local_x(lo_idx)
        x2 = self._slider_value_to_local_x(cur_idx)
        left = min(x1, x2)
        width = max(2, abs(x2 - x1))

        style = self.slider.style()
        opt = QStyleOptionSlider()
        opt.initFrom(self.slider)
        opt.orientation = Qt.Horizontal
        opt.minimum = int(self.slider.minimum())
        opt.maximum = int(self.slider.maximum())
        groove = style.subControlRect(QStyle.CC_Slider, opt, QStyle.SC_SliderGroove, self.slider)

        bar_h = max(4, groove.height() // 2)
        y = groove.center().y() - bar_h / 2
        rect = QRectF(left, y, width, bar_h)

        p = QtGui.QPainter(self._progress_overlay)
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        p.setPen(QtGui.QPen(self._progress_border_color, 1.0))
        p.setBrush(self._progress_color)

        progress_path = QtGui.QPainterPath()
        progress_path.addRoundedRect(rect, bar_h / 2, bar_h / 2)

        min_handle_rect, max_handle_rect = self._get_handle_positions()
        for handle_rect in (min_handle_rect, max_handle_rect):
            cut_rect = QRectF(handle_rect.adjusted(-2, -2, 2, 2))
            cut_path = QtGui.QPainterPath()
            cut_path.addRoundedRect(cut_rect, 4, 4)
            progress_path = progress_path.subtracted(cut_path)

        p.drawPath(progress_path)

    def set_progress_index(self, index: int):
        min_idx = int(self.slider.minimum())
        max_idx = int(self.slider.maximum())
        clamped = max(min_idx, min(int(index), max_idx))
        if clamped != self._progress_index:
            self._progress_index = clamped
            self.progressIndexChanged.emit(self._progress_index)
        if self._sparse_total_count is not None and self._sparse_resolver is not None:
            self._resolve_timer.start(max(10, int(self._resolve_debounce_ms)))
        self._update_progress_visuals()

    def _resolve_visible_points(self):
        super()._resolve_visible_points()
        if not self._progress_visible:
            return
        if self._sparse_total_count is None or self._sparse_resolver is None:
            return
        idx = self._effective_progress_index()
        self._resolve_index_value(idx)
        self._update_progress_label()

    def get_progress_index(self) -> int:
        return int(self._progress_index)

    def set_progress_value(self, value: float):
        self.set_progress_index(self._real_to_slider(value))

    # Backward-compatible aliases
    def setProgressIndex(self, index: int):
        self.set_progress_index(index)

    def getProgressIndex(self) -> int:
        return self.get_progress_index()

    def setProgressValue(self, value: float):
        self.set_progress_value(value)

    def set_range(self, minimum: float, maximum: float, decimals: int | None = None, steps: int = 1000):
        super().set_range(minimum, maximum, decimals=decimals, steps=steps)
        self._progress_index = self.get_index_value()[0]
        self._update_progress_visuals()

    def set_data(self, data_points, decimals: int | None = None, sort_values: bool = False, unique: bool = False):
        super().set_data(data_points, decimals=decimals, sort_values=sort_values, unique=unique)
        self._progress_index = self.get_index_value()[0]
        self._update_progress_visuals()

    def set_sparse_data(self, first_value: float, last_value: float, total_count: int, decimals: int | None = None):
        super().set_sparse_data(first_value, last_value, total_count, decimals=decimals)
        self._progress_index = self.get_index_value()[0]
        self._update_progress_visuals()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_progress_label()

# ------------------------------------------------------------
# Demo usage
# ------------------------------------------------------------
class Demo(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Replay Timescope Slider")

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        self.range_slider = ReplayTimescopeSlider()
        layout.addWidget(self.range_slider)

        # External API usage example with data points:
        self.range_slider.set_data([1.2, 2.3, 3.4, 4.8, 5.9, 6.7, 7.8, 8.9, 9.0, 10.1], decimals=1)
        self.range_slider.set_value(2.4, 5.7)  # nearest available values are used
        self.range_slider.set_progress_index(self.range_slider.get_index_value()[0])

        # Getter APIs:
        print("Current value:", self.range_slider.get_value())
        print("Current index:", self.range_slider.get_index_value())
        print("Current progress index:", self.range_slider.get_progress_index())

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

        # Progress signals
        self.range_slider.progressIndexChanged.connect(
            lambda idx: print(f"Progress index: {idx}")
        )

        # Manual API usage example (no auto-run):
        self.range_slider.set_progress_index(self.range_slider.get_index_value()[0] + 1)

    def _on_handle_index_changed(self, handle_id: int, index: int):
        handle_name = "LOW" if handle_id == 0 else "HIGH"
        print(f"Moving handle: {handle_name}, index={index}")

if __name__ == "__main__":
    import os
    from can_sdk.dbc_manager import CANDBManager
    from can_sdk.parser_manager import CANLogManager

    app = QApplication(sys.argv)

    host = QWidget()
    host.setWindowTitle("ReplayTimescopeSlider - Context Resolver Test")
    host_layout = QVBoxLayout(host)
    host_layout.setAlignment(Qt.AlignCenter)

    log_ctx_mgr = LogContextViewModel(DBM=CANDBManager(), CLM=CANLogManager())
    slider = ReplayTimescopeSlider(parent=host, player=None, ctx_model=log_ctx_mgr)
    host_layout.addWidget(slider)

    slider.valueChanged.connect(lambda v: print(f"scope={v[0]} -> {v[1]}"))
    slider.indexValueChanged.connect(lambda i: print(f"index={i[0]} -> {i[1]}"))

    def _on_context_changed(ctx: BasicFileLogContext | None):
        if ctx is None:
            print("context: None")
            return
        print(f"context: {getattr(ctx, 'file_name', '-')}")
        # Force immediate rebind for current filter state.
        slider.set_context(ctx)

    log_ctx_mgr.event_on_context_changed.subscribe(_on_context_changed)

    filelog = os.environ.get(
        "REPLAY_TEST_LOG",
        "/home/gnar911/Desktop/2025-02-11_11-14-53_仕様情報切替 1_x10.asc",
    )
    if os.path.isfile(filelog):
        ok = log_ctx_mgr.request_verify_file(filelog)
        print(f"request_verify_file: {ok} -> {filelog}")
    else:
        print("REPLAY_TEST_LOG not found. Set env var to an existing .asc/.blf/.csv/.log file.")

    host.resize(900, 180)
    host.show()
    sys.exit(app.exec())
