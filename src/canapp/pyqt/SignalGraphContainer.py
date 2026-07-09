from typing import Dict, Iterable, Optional
import numpy as np
from PySide6 import QtCore, QtGui, QtWidgets
from ui_sdk.components.pyqt.SignalGraph import SignalGraphWidget

class SignalGraphContainer(QtWidgets.QWidget):
    graphRemoved = QtCore.Signal(str)

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None, graph_height: int = 220) -> None:
        super().__init__(parent)
        self._graph_height = graph_height
        self._graphs: Dict[str, SignalGraphWidget] = {}
        self._drag_source_graph: Optional[SignalGraphWidget] = None
        self._drag_start_global_pos: Optional[QtCore.QPoint] = None
        self._drag_hotspot_in_graph: Optional[QtCore.QPoint] = None
        self._is_dragging_graph = False
        self._swap_anim_group: Optional[QtCore.QParallelAnimationGroup] = None
        self._swap_anim_duration_ms = 260
        self._reorder_anim_duration_ms = 210
        self._drag_placeholder: Optional[QtWidgets.QWidget] = None
        self._drag_origin_parent: Optional[QtWidgets.QWidget] = None
        self._drag_fixed_x: int = 0
        self._drag_last_pointer_y: Optional[int] = None
        self._swap_hysteresis_px = 10

        root_layout = QtWidgets.QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)

        self.scroll = QtWidgets.QScrollArea(self)
        self.scroll.setWidgetResizable(True)
        root_layout.addWidget(self.scroll)

        self._content = QtWidgets.QWidget(self.scroll)
        self._stack_layout = QtWidgets.QVBoxLayout(self._content)
        self._stack_layout.setContentsMargins(12, 12, 12, 12)
        self._stack_layout.setSpacing(10)
        self._stack_layout.addStretch(1)

        self.scroll.setWidget(self._content)

    def eventFilter(self, watched: QtCore.QObject, event: QtCore.QEvent) -> bool:
        graph = self._resolve_graph_widget(watched)
        if graph is None:
            return super().eventFilter(watched, event)

        event_type = event.type()
        if event_type == QtCore.QEvent.Type.MouseButtonPress and isinstance(event, QtGui.QMouseEvent):
            if self._handle_mouse_press(graph, watched, event):
                return True
        elif event_type == QtCore.QEvent.Type.MouseMove and isinstance(event, QtGui.QMouseEvent):
            if self._handle_mouse_move(graph, watched, event):
                return True
        elif event_type == QtCore.QEvent.Type.MouseButtonRelease and isinstance(event, QtGui.QMouseEvent):
            if self._handle_mouse_release(graph, watched, event):
                return True
        elif event_type in (QtCore.QEvent.Type.Leave, QtCore.QEvent.Type.HoverLeave):
            if graph is not self._drag_source_graph:
                self._clear_drag_cursor(graph)

        return super().eventFilter(watched, event)

    def add_signal_graph(
        self,
        message_name: str,
        signal_name: str,
        x_data: Iterable[float],
        y_data: Iterable[float],
        y_min: Optional[float] = None,
        y_max: Optional[float] = None,
        x_axis_offset: int = 0,
        unit: str = "",
    ) -> SignalGraphWidget:
        graph = SignalGraphWidget(self._content, initial_height=self._graph_height)
        graph.setGraphHeight(self._graph_height)
        graph.mergeDropped.connect(self._on_merge_dropped)
        graph.closeRequested.connect(self._on_graph_close_requested)
        graph.add_signal(
            message_name=message_name,
            name=signal_name,
            x_data=x_data,
            y_data=y_data,
            y_min=y_min,
            y_max=y_max,
            x_axis_offset=x_axis_offset,
            unit=unit,
        )
        self._append_graph_widget(graph)
        return graph

    def add_choice_signal_graph(
        self,
        message_name: str,
        signal_name: str,
        x_data: Iterable[float],
        y_data: Dict[int, str],
        sample_values: Optional[Iterable[int]] = None,
        x_axis_offset: int = 0,
        unit: str = "",
    ) -> SignalGraphWidget:
        graph = SignalGraphWidget(self._content, initial_height=self._graph_height)
        graph.setGraphHeight(self._graph_height)
        graph.mergeDropped.connect(self._on_merge_dropped)
        graph.closeRequested.connect(self._on_graph_close_requested)
        graph.add_choice_signal(
            message_name=message_name,
            name=signal_name,
            x_data=x_data,
            y_data=y_data,
            sample_values=sample_values,
            x_axis_offset=x_axis_offset,
            unit=unit,
        )
        self._append_graph_widget(graph)
        return graph

    def add_graph_widget(self, graph: SignalGraphWidget) -> None:
        graph.setParent(self._content)
        graph.setGraphHeight(self._graph_height)
        graph.mergeDropped.connect(self._on_merge_dropped)
        graph.closeRequested.connect(self._on_graph_close_requested)
        self._append_graph_widget(graph)

    def clear(self) -> None:
        for graph in list(self._graphs.values()):
            self._remove_graph_widget(graph)
        self._graphs.clear()

    def remove_graph_by_id(self, graph_id: str) -> bool:
        graph = self._graphs.pop(graph_id, None)
        if graph is None:
            return False
        self._remove_graph_widget(graph)
        self.graphRemoved.emit(graph_id)
        return True

    def graph_count(self) -> int:
        return len(self._graphs)

    def _append_graph_widget(self, graph: SignalGraphWidget) -> None:
        self._graphs[graph.graph_id] = graph
        self._install_drag_event_filters(graph)
        self._insert_widget_before_stretch(graph, self._stack_layout.count())

    def _remove_graph_widget(self, graph: SignalGraphWidget) -> None:
        try:
            graph.closeRequested.disconnect(self._on_graph_close_requested)
        except (TypeError, RuntimeError):
            pass
        self._remove_drag_event_filters(graph)
        if self._drag_source_graph is graph:
            self._reset_drag_state(graph)
        self._stack_layout.removeWidget(graph)
        graph.setParent(None)
        graph.deleteLater()

    def _on_graph_close_requested(self, graph_id: str) -> None:
        self.remove_graph_by_id(graph_id)

    def _on_merge_dropped(self, target_graph_id: str, source_graph_id: str) -> None:
        if target_graph_id == source_graph_id:
            return

        target = self._graphs.get(target_graph_id)
        source = self._graphs.get(source_graph_id)
        if target is None or source is None:
            return

        target.merge_from(source)
        self.remove_graph_by_id(source_graph_id)

    def _install_drag_event_filters(self, graph: SignalGraphWidget) -> None:
        watched_widgets = [graph, graph.plot_widget, graph.plot_widget.viewport()]
        for widget in watched_widgets:
            widget.installEventFilter(self)
            widget.setMouseTracking(True)

    def _remove_drag_event_filters(self, graph: SignalGraphWidget) -> None:
        watched_widgets = [graph, graph.plot_widget, graph.plot_widget.viewport()]
        for widget in watched_widgets:
            widget.removeEventFilter(self)

    def _resolve_graph_widget(self, watched: QtCore.QObject) -> Optional[SignalGraphWidget]:
        if not isinstance(watched, QtWidgets.QWidget):
            return None

        cursor = watched
        while cursor is not None and cursor is not self._content:
            if isinstance(cursor, SignalGraphWidget):
                return cursor
            cursor = cursor.parentWidget()
        return None

    def _ordered_graph_widgets(self) -> list[SignalGraphWidget]:
        graphs: list[SignalGraphWidget] = []
        for index in range(self._stack_layout.count()):
            item = self._stack_layout.itemAt(index)
            widget = item.widget() if item is not None else None
            if isinstance(widget, SignalGraphWidget):
                graphs.append(widget)
        return graphs

    def _index_of_widget_in_stack(self, widget: QtWidgets.QWidget) -> int:
        for index in range(self._stack_layout.count()):
            item = self._stack_layout.itemAt(index)
            if item is not None and item.widget() is widget:
                return index
        return -1

    def _last_insertable_index(self) -> int:
        return max(0, self._stack_layout.count() - 1)

    def _insert_widget_before_stretch(self, widget: QtWidgets.QWidget, index_hint: int) -> None:
        insert_index = max(0, min(index_hint, self._last_insertable_index()))
        self._stack_layout.insertWidget(insert_index, widget)

    def _mouse_pos_in_graph(
        self,
        graph: SignalGraphWidget,
        watched: QtCore.QObject,
        event: QtGui.QMouseEvent,
    ) -> QtCore.QPoint:
        local_pos = event.position().toPoint()
        if watched is graph:
            return local_pos
        if isinstance(watched, QtWidgets.QWidget):
            global_pos = watched.mapToGlobal(local_pos)
            return graph.mapFromGlobal(global_pos)
        return local_pos

    def _mouse_global_pos(self, watched: QtCore.QObject, event: QtGui.QMouseEvent) -> QtCore.QPoint:
        if hasattr(event, "globalPosition"):
            return event.globalPosition().toPoint()
        if isinstance(watched, QtWidgets.QWidget):
            return watched.mapToGlobal(event.pos())
        return QtGui.QCursor.pos()

    def _is_plot_drag_region(self, graph: SignalGraphWidget, pos_in_graph: QtCore.QPoint) -> bool:
        scene_rect = graph.main_view.sceneBoundingRect()
        if scene_rect.isNull() or not scene_rect.isValid():
            return False

        pointer_global = graph.mapToGlobal(pos_in_graph)
        pointer_in_viewport = graph.plot_widget.viewport().mapFromGlobal(pointer_global)
        pointer_in_scene = graph.plot_widget.mapToScene(pointer_in_viewport)
        return scene_rect.contains(pointer_in_scene)

    def _can_start_widget_drag(self, graph: SignalGraphWidget, pos_in_graph: QtCore.QPoint) -> bool:
        return not self._is_plot_drag_region(graph, pos_in_graph)

    def _set_drag_cursor(self, graph: SignalGraphWidget, shape: QtCore.Qt.CursorShape) -> None:
        cursor = QtGui.QCursor(shape)
        graph.setCursor(cursor)
        graph.plot_widget.setCursor(cursor)
        graph.plot_widget.viewport().setCursor(cursor)

    def _clear_drag_cursor(self, graph: SignalGraphWidget) -> None:
        graph.unsetCursor()
        graph.plot_widget.unsetCursor()
        graph.plot_widget.viewport().unsetCursor()

    def _handle_mouse_press(
        self,
        graph: SignalGraphWidget,
        watched: QtCore.QObject,
        event: QtGui.QMouseEvent,
    ) -> bool:
        if event.button() != QtCore.Qt.MouseButton.LeftButton:
            return False

        pos_in_graph = self._mouse_pos_in_graph(graph, watched, event)
        if not self._can_start_widget_drag(graph, pos_in_graph):
            return False

        self._drag_source_graph = graph
        self._drag_start_global_pos = self._mouse_global_pos(watched, event)
        self._drag_hotspot_in_graph = pos_in_graph
        self._is_dragging_graph = False
        event.accept()
        return True

    def _handle_mouse_move(
        self,
        graph: SignalGraphWidget,
        watched: QtCore.QObject,
        event: QtGui.QMouseEvent,
    ) -> bool:
        pos_in_graph = self._mouse_pos_in_graph(graph, watched, event)

        if self._drag_source_graph is graph and (event.buttons() & QtCore.Qt.MouseButton.LeftButton):
            global_pos = self._mouse_global_pos(watched, event)
            if not self._is_dragging_graph:
                if self._drag_start_global_pos is None:
                    return True
                delta = (global_pos - self._drag_start_global_pos).manhattanLength()
                if delta < QtWidgets.QApplication.startDragDistance():
                    return True
                self._is_dragging_graph = True
                self._begin_live_drag(graph)

            self._set_drag_cursor(graph, QtCore.Qt.CursorShape.ClosedHandCursor)
            self._move_dragged_widget(graph, global_pos)
            self._maybe_reposition_placeholder(global_pos)
            event.accept()
            return True

        if self._drag_source_graph is graph and not (event.buttons() & QtCore.Qt.MouseButton.LeftButton):
            self._reset_drag_state(graph)

        if self._is_plot_drag_region(graph, pos_in_graph):
            return False

        self._clear_drag_cursor(graph)
        return False

    def _handle_mouse_release(
        self,
        graph: SignalGraphWidget,
        watched: QtCore.QObject,
        event: QtGui.QMouseEvent,
    ) -> bool:
        if event.button() != QtCore.Qt.MouseButton.LeftButton:
            return False

        if self._drag_source_graph is not graph:
            return False

        pos_in_graph = self._mouse_pos_in_graph(graph, watched, event)
        was_dragging = self._is_dragging_graph
        self._reset_drag_state(graph)

        if not self._can_start_widget_drag(graph, pos_in_graph):
            return was_dragging

        if was_dragging:
            event.accept()
        return was_dragging

    def _reset_drag_state(self, graph: Optional[SignalGraphWidget] = None) -> None:
        if graph is not None and self._is_dragging_graph:
            self._finish_live_drag(graph)
        self._drag_source_graph = None
        self._drag_start_global_pos = None
        self._drag_hotspot_in_graph = None
        self._is_dragging_graph = False
        if graph is not None:
            self._clear_drag_cursor(graph)

    def _begin_live_drag(self, graph: SignalGraphWidget) -> None:
        index = self._index_of_widget_in_stack(graph)
        if index < 0:
            return

        self._drag_origin_parent = graph.parentWidget()

        placeholder = QtWidgets.QWidget(self._content)
        placeholder.setFixedHeight(graph.height())
        placeholder.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
        self._stack_layout.insertWidget(index, placeholder)
        self._drag_placeholder = placeholder

        graph_top_left_global = graph.mapToGlobal(QtCore.QPoint(0, 0))
        self._stack_layout.removeWidget(graph)
        graph.setParent(self.scroll.viewport())
        graph.show()
        graph.raise_()

        top_left_in_viewport = self.scroll.viewport().mapFromGlobal(graph_top_left_global)
        self._drag_fixed_x = top_left_in_viewport.x()
        graph.move(self._drag_fixed_x, top_left_in_viewport.y())
        self._drag_last_pointer_y = None

    def _move_dragged_widget(self, graph: SignalGraphWidget, pointer_global_pos: QtCore.QPoint) -> None:
        if graph.parentWidget() is not self.scroll.viewport():
            return
        hotspot = self._drag_hotspot_in_graph or QtCore.QPoint(graph.width() // 2, 18)
        top_left_global = pointer_global_pos - hotspot
        top_left_in_viewport = self.scroll.viewport().mapFromGlobal(top_left_global)
        graph.move(self._drag_fixed_x, top_left_in_viewport.y())

    def _maybe_reposition_placeholder(self, pointer_global_pos: QtCore.QPoint) -> None:
        placeholder = self._drag_placeholder
        if placeholder is None:
            return

        pointer_in_content = self._content.mapFromGlobal(pointer_global_pos)
        pointer_y = pointer_in_content.y()
        last_pointer_y = self._drag_last_pointer_y
        self._drag_last_pointer_y = pointer_y

        if last_pointer_y is None:
            return

        moving_down = pointer_y > last_pointer_y
        moving_up = pointer_y < last_pointer_y
        if not moving_down and not moving_up:
            return

        current_index = self._index_of_widget_in_stack(placeholder)
        if current_index < 0:
            return

        if moving_down:
            next_widget, next_index = self._adjacent_signal_widget(current_index, direction=1)
            if next_widget is None or next_index is None:
                return
            threshold = next_widget.geometry().center().y() + self._swap_hysteresis_px
            if pointer_y > threshold:
                old_geometries = self._capture_content_signal_geometries()
                self._insert_widget_before_stretch(placeholder, next_index + 1)
                self._stack_layout.activate()
                self._animate_signal_geometries(old_geometries, duration_ms=self._reorder_anim_duration_ms)
            return

        prev_widget, prev_index = self._adjacent_signal_widget(current_index, direction=-1)
        if prev_widget is None or prev_index is None:
            return
        threshold = prev_widget.geometry().center().y() - self._swap_hysteresis_px
        if pointer_y < threshold:
            old_geometries = self._capture_content_signal_geometries()
            self._insert_widget_before_stretch(placeholder, prev_index)
            self._stack_layout.activate()
            self._animate_signal_geometries(old_geometries, duration_ms=self._reorder_anim_duration_ms)

    def _adjacent_signal_widget(
        self,
        from_index: int,
        direction: int,
    ) -> tuple[Optional[SignalGraphWidget], Optional[int]]:
        index = from_index + direction
        while 0 <= index < self._stack_layout.count():
            item = self._stack_layout.itemAt(index)
            candidate = item.widget() if item is not None else None
            if isinstance(candidate, SignalGraphWidget):
                return candidate, index
            index += direction
        return None, None

    def _finish_live_drag(self, graph: SignalGraphWidget) -> None:
        old_geometries = self._capture_content_signal_geometries()
        drag_top_left_global = graph.mapToGlobal(QtCore.QPoint(0, 0))
        drag_top_left_in_content = self._content.mapFromGlobal(drag_top_left_global)
        drag_start_rect = QtCore.QRect(drag_top_left_in_content, graph.size())

        placeholder = self._drag_placeholder
        target_index = self._index_of_widget_in_stack(placeholder) if placeholder is not None else -1

        if placeholder is not None:
            self._stack_layout.removeWidget(placeholder)
            placeholder.setParent(None)
            placeholder.deleteLater()
            self._drag_placeholder = None

        graph.setParent(self._content)
        if target_index < 0:
            target_index = self._last_insertable_index()
        self._insert_widget_before_stretch(graph, target_index)
        self._stack_layout.activate()
        graph.show()
        self._animate_signal_geometries(
            old_geometries,
            extra_start_rects={graph: drag_start_rect},
            duration_ms=self._swap_anim_duration_ms,
        )

        self._drag_origin_parent = None
        self._drag_last_pointer_y = None

    def _capture_content_signal_geometries(self) -> dict[SignalGraphWidget, QtCore.QRect]:
        geometries: dict[SignalGraphWidget, QtCore.QRect] = {}
        for widget in self._ordered_graph_widgets():
            if widget.parentWidget() is self._content:
                geometries[widget] = QtCore.QRect(widget.geometry())
        return geometries

    def _animate_signal_geometries(
        self,
        old_geometries: dict[SignalGraphWidget, QtCore.QRect],
        extra_start_rects: Optional[dict[SignalGraphWidget, QtCore.QRect]] = None,
        duration_ms: Optional[int] = None,
    ) -> None:
        extra_start_rects = extra_start_rects or {}
        new_geometries = self._capture_content_signal_geometries()

        if self._swap_anim_group is not None:
            self._swap_anim_group.stop()

        self._swap_anim_group = QtCore.QParallelAnimationGroup(self)
        easing = QtCore.QEasingCurve(QtCore.QEasingCurve.Type.InOutCubic)
        duration = self._swap_anim_duration_ms if duration_ms is None else duration_ms

        for widget, new_rect in new_geometries.items():
            start_rect = extra_start_rects.get(widget) or old_geometries.get(widget)
            if start_rect is None or start_rect == new_rect:
                continue

            widget.setGeometry(start_rect)
            anim = QtCore.QPropertyAnimation(widget, b"geometry", self)
            anim.setDuration(duration)
            anim.setEasingCurve(easing)
            anim.setStartValue(start_rect)
            anim.setEndValue(new_rect)
            self._swap_anim_group.addAnimation(anim)

        if self._swap_anim_group.animationCount() > 0:
            self._swap_anim_group.start(QtCore.QAbstractAnimation.DeletionPolicy.KeepWhenStopped)

    def _maybe_swap_with_hovered_widget(self, source: SignalGraphWidget, pointer_global_pos: QtCore.QPoint) -> None:
        ordered = self._ordered_graph_widgets()
        if len(ordered) < 2 or source not in ordered:
            return

        pointer_in_content = self._content.mapFromGlobal(pointer_global_pos)
        source_index = ordered.index(source)

        for target in ordered:
            if target is source:
                continue

            target_rect = target.geometry()
            if not target_rect.contains(pointer_in_content):
                continue

            target_index = ordered.index(target)
            target_center_y = target_rect.center().y()
            moving_down = source_index < target_index and pointer_in_content.y() > target_center_y
            moving_up = source_index > target_index and pointer_in_content.y() < target_center_y

            if moving_down or moving_up:
                self._swap_widgets_with_animation(source, target)
            return

    def _swap_widgets_with_animation(self, source: SignalGraphWidget, target: SignalGraphWidget) -> None:
        ordered = self._ordered_graph_widgets()
        if source not in ordered or target not in ordered:
            return

        source_index = ordered.index(source)
        target_index = ordered.index(target)
        if source_index == target_index:
            return

        old_geometries = {widget: QtCore.QRect(widget.geometry()) for widget in ordered}

        self._stack_layout.insertWidget(target_index, source)
        self._stack_layout.activate()

        new_ordered = self._ordered_graph_widgets()
        new_geometries = {widget: QtCore.QRect(widget.geometry()) for widget in new_ordered}

        if self._swap_anim_group is not None:
            self._swap_anim_group.stop()

        self._swap_anim_group = QtCore.QParallelAnimationGroup(self)
        easing = QtCore.QEasingCurve(QtCore.QEasingCurve.Type.InOutCubic)

        for widget in new_ordered:
            old_rect = old_geometries.get(widget)
            new_rect = new_geometries.get(widget)
            if old_rect is None or new_rect is None or old_rect == new_rect:
                continue

            widget.setGeometry(old_rect)
            anim = QtCore.QPropertyAnimation(widget, b"geometry", self)
            anim.setDuration(self._swap_anim_duration_ms)
            anim.setEasingCurve(easing)
            anim.setStartValue(old_rect)
            anim.setEndValue(new_rect)
            self._swap_anim_group.addAnimation(anim)

        if self._swap_anim_group.animationCount() > 0:
            self._swap_anim_group.start(QtCore.QAbstractAnimation.DeletionPolicy.KeepWhenStopped)


__all__ = ["SignalGraphPanel"]


if __name__ == "__main__":
    app = QtWidgets.QApplication([])

    window = QtWidgets.QMainWindow()
    window.setWindowTitle("SignalGraphPanel Demo")
    window.resize(1200, 760)

    panel = SignalGraphContainer(graph_height=230)
    window.setCentralWidget(panel)

    np.random.seed(7)
    x = np.linspace(100.5, 110.5, 800)

    panel.add_signal_graph(
        message_name="MSG_FV081",
        signal_name="FV081_FVTx",
        x_data=x,
        y_data=8.0 + 0.25 * np.sin(1.8 * x),
        y_min=7.6,
        y_max=8.4,
        x_axis_offset=1,
        unit="km/h",
    )

    choice_labels = {
        0: "OFF",
        1: "IDLE",
        2: "READY",
        3: "RUN",
        4: "FAULT",
    }
    choice_values = np.random.choice(list(choice_labels.keys()), size=len(x))
    panel.add_choice_signal_graph(
        message_name="MSG_MODE",
        signal_name="DriveMode",
        x_data=x,
        y_data=choice_labels,
        sample_values=choice_values,
        x_axis_offset=50,
        unit="state",
    )
    # panel.add_signal_graph(
    #     message_name="MSG_KZK081",
    #     signal_name="KZK081_MACTx",
    #     x_data=x,
    #     y_data=2.0e8 + 1.5e7 * np.cos(0.95 * x),
    #     x_axis_offset=8,
    #     unit="kN",
    # )
    # panel.add_signal_graph(
    #     message_name="MSG_THIRD",
    #     signal_name="ThirdSig",
    #     x_data=x,
    #     y_data=0.4 + 0.45 * np.sin(0.55 * x + 0.3),
    #     x_axis_offset=16,
    #     unit="ratio",
    # )
    # panel.add_signal_graph(
    #     message_name="MSG_NOISE",
    #     signal_name="NoiseSig",
    #     x_data=x,
    #     y_data=np.cumsum(np.random.normal(0.0, 0.01, size=x.shape[0])) + 1.0,
    #     x_axis_offset=24,
    #     unit="raw",
    # )

    window.show()
    app.exec()