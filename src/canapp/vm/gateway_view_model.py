from __future__ import annotations

from typing import Any

from PySide6.QtCore import Property, Signal, Slot

from .base_view_model import BaseViewModel


class GatewayViewModel(BaseViewModel):
    routesChanged = Signal()
    lastErrorChanged = Signal()

    def __init__(self, can_service: Any, event_types: dict[str, type] | None = None):
        super().__init__(event_types=event_types)
        self._can_service = can_service
        self._routes: list[dict[str, Any]] = []
        self._last_error = ""

        self._subscribe_event(self._can_service, "GatewayRouteAddedEvent", self._on_route_added)
        self._subscribe_event(self._can_service, "GatewayRoutesClearedEvent", self._on_routes_cleared)

    @Property("QVariantList", notify=routesChanged)
    def routes(self) -> list[dict[str, Any]]:
        return self._routes

    @Property(str, notify=lastErrorChanged)
    def lastError(self) -> str:
        return self._last_error

    @Slot(str, str, int, int, result=bool)
    def addRoute(
        self,
        src_channel: str,
        dst_channel: str,
        src_can_id: int = -1,
        dst_can_id: int = -1,
    ) -> bool:
        src_id = None if src_can_id < 0 else src_can_id
        dst_id = None if dst_can_id < 0 else dst_can_id

        ok = bool(
            self._can_service.add_gateway_route(
                src_channel=src_channel,
                dst_channel_info=dst_channel,
                src_can_id=src_id,
                dst_can_id=dst_id,
            )
        )
        if not ok:
            self._set_if_changed(self, "_last_error", "Failed to add gateway route", self.lastErrorChanged)
        return ok

    @Slot()
    def clearRoutes(self) -> None:
        self._can_service.clear_gateway_routes()
        self._set_if_changed(self, "_routes", [], self.routesChanged)

    def _on_route_added(self, event: Any) -> None:
        route = getattr(event, "route", None)
        if route is None:
            route = {
                "src_channel": getattr(event, "src_channel", ""),
                "dst_channel": getattr(event, "dst_channel", ""),
                "src_can_id": getattr(event, "src_can_id", None),
                "dst_can_id": getattr(event, "dst_can_id", None),
            }
        updated = [*self._routes, route]
        self._set_if_changed(self, "_routes", updated, self.routesChanged)

    def _on_routes_cleared(self, _: Any) -> None:
        self._set_if_changed(self, "_routes", [], self.routesChanged)
