from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
import numpy as np
from PySide6 import QtCore, QtWidgets
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QSplitter, QVBoxLayout, QWidget
from ui_sdk.components.pyqt.SignalGraphContainer import SignalGraphContainer
from ui_sdk.components.pyqt.SignalGraphCheckList import SignalGraphCheckList
from ui_sdk.components.pyqt.basic_component.CollapsibleSection import CollapsibleSection
from can_sdk.data_object import CANLogFile, SignalMetadata, SignalFilter

# TEST
from can_sdk.canlog_viewmodel import LogContext, LogContextViewModel, DecodeStatusChangedInfo
from can_sdk.logger_setup import LOG, setup_logger
from PySide6.QtWidgets import (
    QWidget, QGroupBox, QVBoxLayout, QHBoxLayout,
    QApplication, QStyle, QToolButton, QLabel)

@dataclass
class _ContextGraphState:
    ctx: Optional[LogContext]
    container: SignalGraphContainer
    signal_to_graph_id: Dict[str, str] = field(default_factory=dict)
    graph_id_to_signal: Dict[str, str] = field(default_factory=dict)
    checked_signals: Set[str] = field(default_factory=set)

class SignalGraphPanel(QWidget):
    LEFT_PANE_MIN_WIDTH = 80
    _contextChangedRequested = QtCore.Signal(object)
    _decodeStatusChangedRequested = QtCore.Signal(object)

    def __init__(self, 
                 parent = None,
                 model: Optional[LogContextViewModel] = None, ## For multi graphs of contexts
                 graph_height: int = 220):
        self.my_model = model
        super().__init__(parent)
        self._graph_height = graph_height
        self._available_signal_names: List[str] = []
        self._context_states: Dict[str, _ContextGraphState] = {}
        self._context_order: List[str] = []
        self._current_context_key: Optional[str] = None
        self._signal_payload_builder: Optional[
            Callable[[Optional[LogContext], str], Optional[Dict[str, Any]]]
        ] = None
        self._is_clamping_splitter = False
        self._left_collapsed = False

        self._build_ui(graph_height)
        self._connect_signals()

        self._contextChangedRequested.connect(self.on_event_context_changed, Qt.QueuedConnection)
        self._decodeStatusChangedRequested.connect(self._on_decode_status_changed, Qt.QueuedConnection)

        if self.my_model is not None:
            self.my_model.event_on_context_changed.subscribe(self._on_model_context_changed)
            self.my_model.event_on_decode_status_changed.subscribe(self._on_model_decode_status_changed)

            current_ctx = self.my_model.cur_ctx
            if current_ctx is not None:
                self.checklist._on_context_changed(current_ctx)
            self._update_status_label_from_model(current_ctx)
        else:
            self._update_status_label_from_model(None)

        self._render_graph_area()

    def on_event_context_changed(self, ctx: Optional[LogContext]):
        new_key = self._context_key(ctx)

        self.checklist._on_context_changed(ctx)

        if new_key is not None:
            self._ensure_context_state(new_key, ctx)

        self._current_context_key = new_key
        self._sync_checklist_with_current_context()
        self._render_graph_area()
        self._update_status_label_from_model(ctx)

    def _on_model_context_changed(self, ctx: Optional[LogContext]):
        self._contextChangedRequested.emit(ctx)

    def _on_model_decode_status_changed(self, info: DecodeStatusChangedInfo):
        self._decodeStatusChangedRequested.emit(info)

    def _on_decode_status_changed(self, info: DecodeStatusChangedInfo):
        if info is None:
            return
        current_ctx = self.my_model.cur_ctx if self.my_model is not None else None
        if current_ctx is None:
            self._update_status_label_from_model(None)
            return
        if getattr(info, "context", None) is not current_ctx:
            return
        self._update_status_label_from_model(current_ctx)

    def _update_status_label_from_model(self, ctx: Optional[LogContext]):
        if ctx is None:
            self.status_label.setText("context: none | decoded signals: 0")
            return
        file_name = str(getattr(ctx, "file_name", "") or "unknown")
        decoded_pairs = getattr(getattr(ctx, "dd_filelog", None), "decode_signal_list", []) or []
        self.status_label.setText(f"context: {file_name} | decoded signals: {len(decoded_pairs)}")

    def _build_ui(self, graph_height: int):
        drawer_content = QWidget(self)
        drawer_content.setMinimumWidth(0)
        drawer_layout = QVBoxLayout(drawer_content)
        drawer_layout.setContentsMargins(0, 0, 0, 0)
        drawer_layout.setSpacing(8)

        self.checklist = SignalGraphCheckList(parent=self, ctx_model=self.my_model)
        drawer_layout.addWidget(self.checklist)

        self.graph_host = QWidget(self)
        self.graph_host_layout = QVBoxLayout(self.graph_host)
        self.graph_host_layout.setContentsMargins(0, 0, 0, 0)
        self.graph_host_layout.setSpacing(6)

        self.splitter = QSplitter(Qt.Horizontal, self)
        self.splitter.addWidget(drawer_content)
        self.splitter.addWidget(self.graph_host)
        self.splitter.setChildrenCollapsible(True)
        self.splitter.setCollapsible(0, True)
        self.splitter.setCollapsible(1, False)
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setSizes([180, 600])

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        root_layout.addWidget(self.splitter, 1)

        self.status_label = QLabel(self)
        self.status_label.setStyleSheet("color: palette(shadow); font-style: italic;")
        status_row = QHBoxLayout()
        status_row.setContentsMargins(0, 0, 0, 0)
        status_row.setSpacing(6)
        status_row.addStretch(1)
        status_row.addWidget(self.status_label, 0)
        root_layout.addLayout(status_row)

    def _connect_signals(self):
        self.checklist.list.itemChanged.connect(self._on_check_item_changed)
        self.checklist.valueSignalDataReady.connect(self._on_value_signal_data_ready)
        self.checklist.choiceSignalDataReady.connect(self._on_choice_signal_data_ready)
        self.splitter.splitterMoved.connect(self._on_splitter_moved)

    def _on_splitter_moved(self, _pos: int, _index: int):
        if self._is_clamping_splitter:
            return

        sizes = self.splitter.sizes()
        if len(sizes) < 2:
            return

        left = sizes[0]
        if left == 0:
            self._left_collapsed = True
            return
        if left >= self.LEFT_PANE_MIN_WIDTH:
            self._left_collapsed = False
            return

        total = sum(sizes)
        if total <= self.LEFT_PANE_MIN_WIDTH:
            return

        target_left = self.LEFT_PANE_MIN_WIDTH if self._left_collapsed else 0
        self._is_clamping_splitter = True
        try:
            self.splitter.setSizes([target_left, total - target_left])
            self._left_collapsed = (target_left == 0)
        finally:
            self._is_clamping_splitter = False

    def set_signal_payload_builder(
        self,
        builder: Callable[[Optional[LogContext], str], Optional[Dict[str, Any]]],
    ):
        self._signal_payload_builder = builder

    def set_available_signals(self, signal_names: List[str]):
        self._available_signal_names = list(signal_names)
        self._sync_checklist_with_current_context()

    def _on_check_item_changed(self, item):
        state = self._get_current_state()
        if state is None:
            return

        signal_name = self._get_signal_name_from_item(item)
        if not signal_name:
            return
        checked = item.checkState() == Qt.Checked
        if checked:
            state.checked_signals.add(signal_name)
        else:
            state.checked_signals.discard(signal_name)
            self._remove_signal_graph(signal_name)

    def _on_value_signal_data_ready(self, signal_filter: SignalFilter, x_data: List[float], y_data: List[float]):
        state = self._get_current_state()
        if state is None:
            return

        signal_name = str(getattr(signal_filter, "sig_name", "") or "")
        if not signal_name:
            return

        sig_info = getattr(signal_filter, "signal_info", None)
        x_arr = np.array(list(x_data), dtype=float)
        y_arr = np.array(list(y_data), dtype=float)
        x_arr, y_arr = self._normalize_xy_samples(signal_name, x_arr, y_arr)
        if x_arr.size == 0 or y_arr.size == 0:
            return

        payload = {
            "kind": "numeric",
            "message_name": str(getattr(signal_filter, "message_name", "") or ""),
            "x_data": x_arr,
            "y_data": y_arr,
            "y_min": float(sig_info.minimum) if sig_info is not None and sig_info.minimum is not None else None,
            "y_max": float(sig_info.maximum) if sig_info is not None and sig_info.maximum is not None else None,
            "unit": str(getattr(sig_info, "unit", "") or ""),
            "x_axis_offset": 0,
        }
        self._add_signal_graph_from_payload(signal_name, payload)

    def _on_choice_signal_data_ready(self, signal_filter: SignalFilter, x_data: List[float], sample_values: List[int]):
        state = self._get_current_state()
        if state is None:
            return

        signal_name = str(getattr(signal_filter, "sig_name", "") or "")
        if not signal_name:
            return

        sig_info = getattr(signal_filter, "signal_info", None)
        choices = getattr(sig_info, "choices", None) if sig_info is not None else None
        x_arr = np.array(list(x_data), dtype=float)
        sample_arr = np.array(list(sample_values), dtype=int)
        x_arr, sample_arr = self._normalize_xy_samples(signal_name, x_arr, sample_arr)
        if x_arr.size == 0 or sample_arr.size == 0:
            return

        payload = {
            "kind": "choice",
            "message_name": str(getattr(signal_filter, "message_name", "") or ""),
            "x_data": x_arr,
            "y_data": {int(k): str(v) for k, v in (choices or {}).items()},
            "sample_values": sample_arr,
            "unit": str(getattr(sig_info, "unit", "") or ""),
            "x_axis_offset": 0,
        }
        self._add_signal_graph_from_payload(signal_name, payload)

    def _normalize_xy_samples(self, signal_name: str, x_data: np.ndarray, y_data: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        x_size = int(x_data.size)
        y_size = int(y_data.size)
        if x_size == y_size:
            return x_data, y_data

        target_size = min(x_size, y_size)
        LOG.warning(
            "Signal '%s' has x/y size mismatch (x=%d, y=%d). Trimming to %d samples.",
            signal_name,
            x_size,
            y_size,
            target_size,
        )
        if target_size <= 0:
            return np.array([], dtype=x_data.dtype), np.array([], dtype=y_data.dtype)
        return x_data[:target_size], y_data[:target_size]

    def _add_signal_graph(self, signal_name: str):
        state = self._get_current_state()
        if state is None:
            return

        if signal_name in state.signal_to_graph_id:
            return

        payload = self.prepare_signal_payload(state.ctx, signal_name)
        self._add_signal_graph_from_payload(signal_name, payload)

    def _add_signal_graph_from_payload(self, signal_name: str, payload: Optional[Dict[str, Any]]):
        state = self._get_current_state()
        if state is None:
            return

        if signal_name in state.signal_to_graph_id:
            return

        if not payload:
            self._set_check_state(signal_name, False)
            state.checked_signals.discard(signal_name)
            return

        message_name = payload.get("message_name", "")
        x_data = payload.get("x_data")
        x_axis_offset = int(payload.get("x_axis_offset", 0))
        unit = payload.get("unit", "")
        if x_data is None:
            self._set_check_state(signal_name, False)
            state.checked_signals.discard(signal_name)
            return

        kind = payload.get("kind", "numeric")
        if kind == "choice":
            graph = state.container.add_choice_signal_graph(
                message_name=message_name,
                signal_name=signal_name,
                x_data=x_data,
                y_data=payload.get("y_data", {}),
                sample_values=payload.get("sample_values"),
                x_axis_offset=x_axis_offset,
                unit=unit,
            )
        else:
            y_data = payload.get("y_data")
            if y_data is None:
                self._set_check_state(signal_name, False)
                state.checked_signals.discard(signal_name)
                return
            graph = state.container.add_signal_graph(
                message_name=message_name,
                signal_name=signal_name,
                x_data=x_data,
                y_data=y_data,
                y_min=payload.get("y_min"),
                y_max=payload.get("y_max"),
                x_axis_offset=x_axis_offset,
                unit=unit,
            )

        state.signal_to_graph_id[signal_name] = graph.graph_id
        state.graph_id_to_signal[graph.graph_id] = signal_name
        self._render_graph_area()

    def _remove_signal_graph(self, signal_name: str):
        state = self._get_current_state()
        if state is None:
            return

        graph_id = state.signal_to_graph_id.pop(signal_name, None)
        if not graph_id:
            return
        state.graph_id_to_signal.pop(graph_id, None)
        state.container.remove_graph_by_id(graph_id)
        self._render_graph_area()

    def _on_graph_removed(self, context_key: str, graph_id: str):
        state = self._context_states.get(context_key)
        if state is None:
            return

        signal_name = state.graph_id_to_signal.pop(graph_id, None)
        if not signal_name:
            return

        state.signal_to_graph_id.pop(signal_name, None)
        state.checked_signals.discard(signal_name)

        if context_key == self._current_context_key:
            self._set_check_state(signal_name, False)

        self._render_graph_area()

    def _set_check_state(self, signal_name: str, checked: bool):
        target_state = Qt.Checked if checked else Qt.Unchecked
        for i in range(self.checklist.list.count()):
            item = self.checklist.list.item(i)
            if self._get_signal_name_from_item(item) != signal_name:
                continue
            if item.checkState() == target_state:
                return
            blocker = QtCore.QSignalBlocker(self.checklist.list)
            item.setCheckState(target_state)
            del blocker
            return

    def _get_signal_name_from_item(self, item) -> str:
        if item is None:
            return ""
        payload = item.data(Qt.UserRole)
        if isinstance(payload, tuple) and len(payload) >= 3:
            return str(payload[2])
        text = item.text()
        return str(text) if text else ""

    def prepare_signal_payload(
        self,
        ctx: Optional[LogContext],
        signal_name: str,
    ) -> Optional[Dict[str, Any]]:
        # If custom builder is set, use it
        if self._signal_payload_builder is not None:
            return self._signal_payload_builder(ctx, signal_name)
        # Otherwise, try to build from signal_metadata
        return self._build_signal_payload_from_metadata(ctx, signal_name)

    def _find_signal_in_metadata(
        self,
        datalog: CANLogFile,
        signal_name: str,
    ) -> Tuple[Optional[int], Optional[List[SignalMetadata]]]:
        """Find signal in signal_metadata by name, returns (can_id, metadata_list)."""
        for can_id, signals_dict in datalog.signal_metadata.items():
            if signal_name in signals_dict:
                metadata_list = datalog.get_signal_metadata(can_id, signal_name)
                return can_id, metadata_list
        return None, None

    def _build_signal_payload_from_metadata(
        self,
        ctx: Optional[LogContext],
        signal_name: str,
    ) -> Optional[Dict[str, Any]]:
        """Build signal payload from CANLogFile.signal_metadata and DBC info."""
        if ctx is None:
            return None
        datalog = ctx.r_filelog
        # Find signal in metadata
        can_id, metadata_list = self._find_signal_in_metadata(datalog, signal_name)
        if can_id is None or not metadata_list:
            LOG.warning(f"Signal '{signal_name}' not found in signal_metadata")
            return None

        # Get message/signal info from SignalList current rows
        msg_info = self.checklist.get_current_checked_message()
        sig_info = msg_info.get_signal_by_name(signal_name)
        message_name = msg_info.name

        # Extract x_data (timestamps) and y_data (values) from metadata
        x_data = np.array([m.timestamp for m in metadata_list], dtype=float)
        
        # Determine kind and prepare y_data
        is_choice = sig_info is not None and sig_info.choices is not None and len(sig_info.choices) > 0
        
        if is_choice:
            # For choice signals: y_data is the choice dict, sample_values is raw values
            sample_values = np.array([m.raw_value if m.raw_value is not None else 0 for m in metadata_list], dtype=int)
            y_data_choices = {int(k): str(v) for k, v in sig_info.choices.items()}
            unit = sig_info.unit if sig_info and sig_info.unit else ""
            
            return {
                "kind": "choice",
                "message_name": message_name,
                "x_data": x_data,
                "y_data": y_data_choices,
                "sample_values": sample_values,
                "unit": unit,
                "x_axis_offset": 0,
            }
        else:
            # For numeric signals: use physical value if available, otherwise raw_value
            y_data = np.array(
                [m.value if m.value is not None else (m.raw_value if m.raw_value is not None else 0.0)
                 for m in metadata_list],
                dtype=float
            )
            
            # Get y_min and y_max from signal info
            y_min = None
            y_max = None
            unit = ""
            
            if sig_info is not None:
                unit = sig_info.unit if sig_info.unit else ""
                # Use DBC min/max if available
                if sig_info.minimum is not None:
                    y_min = float(sig_info.minimum)
                if sig_info.maximum is not None:
                    y_max = float(sig_info.maximum)
            
            return {
                "kind": "numeric",
                "message_name": message_name,
                "x_data": x_data,
                "y_data": y_data,
                "y_min": y_min,
                "y_max": y_max,
                "unit": unit,
                "x_axis_offset": 0,
            }

    def _context_key(self, ctx: Optional[LogContext]) -> Optional[str]:
        if ctx is None:
            return None
        file_path = getattr(ctx, "file_path", None)
        if file_path:
            return str(file_path)
        datalog = getattr(ctx, "r_filelog", None)
        if datalog is not None and getattr(datalog, "file_path", None):
            return str(datalog.file_path)
        return None

    def _ensure_context_state(self, key: str, ctx: Optional[LogContext]) -> _ContextGraphState:
        state = self._context_states.get(key)
        if state is not None:
            state.ctx = ctx
            return state

        container = SignalGraphContainer(self.graph_host, graph_height=self._graph_height)
        container.graphRemoved.connect(lambda graph_id, ctx_key=key: self._on_graph_removed(ctx_key, graph_id))
        state = _ContextGraphState(ctx=ctx, container=container)
        self._context_states[key] = state
        self._context_order.append(key)
        return state

    def _get_current_state(self) -> Optional[_ContextGraphState]:
        if self._current_context_key is None:
            return None
        return self._context_states.get(self._current_context_key)

    def _sync_checklist_with_current_context(self):
        if not self._available_signal_names:
            return
        state = self._get_current_state()
        checked = state.checked_signals if state is not None else set()
        blocker = QtCore.QSignalBlocker(self.checklist.list)
        try:
            self.checklist.set_items(self._available_signal_names)
            for i in range(self.checklist.list.count()):
                item = self.checklist.list.item(i)
                name = item.text()
                item.setCheckState(Qt.Checked if name in checked else Qt.Unchecked)
        finally:
            del blocker

    def _clear_layout(self, layout: QVBoxLayout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                if not isinstance(widget, SignalGraphContainer):
                    widget.deleteLater()

    def _render_graph_area(self):
        self._clear_layout(self.graph_host_layout)

        state = self._get_current_state()
        if state is None:
            return

        if len(self._context_order) <= 1:
            self.graph_host_layout.addWidget(state.container)
            return

        for key in self._context_order:
            section_state = self._context_states.get(key)
            if section_state is None:
                continue

            section = CollapsibleSection(
                title=key,
                parent=self.graph_host,
                expanded=(key == self._current_context_key),
                animated=False,
            )
            section_layout = QVBoxLayout()
            section_layout.setContentsMargins(0, 0, 0, 0)
            section_layout.setSpacing(0)
            section_layout.addWidget(section_state.container)
            section.setContentLayout(section_layout)
            self.graph_host_layout.addWidget(section)

        self.graph_host_layout.addStretch(1)

if __name__ == "__main__":
    import numpy as np
    from can_sdk.test_ultility import TEST_set_up_1_context
    # APP
    setup_logger(env="DEV", backup_count=30)
    app = QApplication()
    win = QWidget()
    win.setWindowTitle("TreeLogTable Test")
    layout = QVBoxLayout(win)

    ############################### SET UP ##############################
    ctx_model = TEST_set_up_1_context()

    panel = SignalGraphPanel(model=ctx_model)
    panel.resize(1200, 760)
    panel.setWindowTitle("SignalGraphPanel Test")
    ############################### LV1. TEST DUMMY ##############################
    # x = np.linspace(100.5, 110.5, 700)
    # sample_payloads = {
    #     "FV081_FVTx": {
    #         "kind": "numeric",
    #         "message_name": "MSG_FV081",
    #         "x_data": x,
    #         "y_data": 8.0 + 0.25 * np.sin(1.7 * x),
    #         "y_min": 7.4,
    #         "y_max": 8.6,
    #         "unit": "km/h",
    #         "x_axis_offset": 0,
    #     },
    #     "KZK081_MACTx": {
    #         "kind": "numeric",
    #         "message_name": "MSG_KZK081",
    #         "x_data": x,
    #         "y_data": 2.0e8 + 1.5e7 * np.cos(0.95 * x),
    #         "unit": "kN",
    #         "x_axis_offset": 8,
    #     },
    #     "DriveMode": {
    #         "kind": "choice",
    #         "message_name": "MSG_MODE",
    #         "x_data": x,
    #         "y_data": {0: "OFF", 1: "IDLE", 2: "READY", 3: "RUN", 4: "FAULT"},
    #         "sample_values": np.random.choice([0, 1, 2, 3, 4], size=len(x)),
    #         "unit": "state",
    #         "x_axis_offset": 20,
    #     },
    # }

    # panel.set_available_signals(list(sample_payloads.keys()))
    # panel.set_signal_payload_builder(lambda _ctx, signal_name: sample_payloads.get(signal_name))


    ############################### LV2. TEST DUMMY ##############################


    panel.show()
    app.exec()
