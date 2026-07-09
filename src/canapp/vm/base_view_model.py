from __future__ import annotations

from typing import Any, Callable, Type

from PySide6.QtCore import QObject, Slot


class BaseViewModel(QObject):
    """Shared utilities for Qt ViewModels.

    Responsibilities:
    - Optional event class lookup by name.
    - Best-effort subscription lifecycle cleanup on QObject destruction.
    - Small helper to update state only when values change.
    """

    def __init__(self, event_types: dict[str, Type[Any]] | None = None):
        super().__init__()
        self._event_types = event_types or {}
        self._subscriptions: list[Callable[[], None]] = []
        self.destroyed.connect(self._dispose_subscriptions)

    def _event_class(self, name: str) -> Type[Any] | None:
        return self._event_types.get(name)

    def _subscribe_event(
        self,
        service: Any,
        event_name: str,
        callback: Callable[[Any], None],
    ) -> None:
        event_type = self._event_class(event_name)
        if event_type is None:
            return
        if not hasattr(service, "subscribe"):
            return

        token = service.subscribe(event_type, callback)
        self._track_subscription(token)

    def _subscribe_any(self, service: Any, callback: Callable[[Any], None]) -> None:
        if not hasattr(service, "subscribe_any"):
            return
        token = service.subscribe_any(callback)
        self._track_subscription(token)

    def _track_subscription(self, token: Any) -> None:
        if token is None:
            return

        if callable(token):
            self._subscriptions.append(token)
            return

        for method_name in ("dispose", "unsubscribe", "close"):
            disposer = getattr(token, method_name, None)
            if callable(disposer):
                self._subscriptions.append(disposer)
                return

    @Slot()
    def _dispose_subscriptions(self, *_: Any) -> None:
        while self._subscriptions:
            disposer = self._subscriptions.pop()
            try:
                disposer()
            except Exception:
                pass

    # @staticmethod
    # def _set_if_changed(obj: Any, attr_name: str, value: Any, changed_signal: Any) -> bool:
    #     if getattr(obj, attr_name) == value:
    #         return False
    #     setattr(obj, attr_name, value)
    #     changed_signal.emit()
    #     return True
