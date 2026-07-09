from __future__ import annotations

from typing import Any

from PySide6.QtCore import Property, Signal, Slot

from .base_view_model import BaseViewModel


class DbcViewModel(BaseViewModel):
    currentDbcChanged = Signal()
    loadingChanged = Signal()
    lastErrorChanged = Signal()

    def __init__(self, file_service: Any, event_types: dict[str, type] | None = None):
        super().__init__(event_types=event_types)
        self._file_service = file_service
        self._loading = False
        self._current_dbc = ""
        self._last_error = ""

        self._subscribe_event(self._file_service, "DBCLoadedEvent", self._on_dbc_loaded)
        self._subscribe_event(self._file_service, "DBCParseFailedEvent", self._on_dbc_failed)

    @Property(bool, notify=loadingChanged)
    def loading(self) -> bool:
        return self._loading

    @Property(str, notify=currentDbcChanged)
    def currentDbc(self) -> str:
        return self._current_dbc

    @Property(str, notify=lastErrorChanged)
    def lastError(self) -> str:
        return self._last_error

    @Slot(str, result=bool)
    def loadDbc(self, path: str) -> bool:
        self._set_if_changed(self, "_loading", True, self.loadingChanged)
        self._set_if_changed(self, "_last_error", "", self.lastErrorChanged)
        ok = bool(self._file_service.parse_dbc(path))
        if not ok:
            self._set_if_changed(self, "_loading", False, self.loadingChanged)
            self._set_if_changed(self, "_last_error", f"Failed to parse DBC: {path}", self.lastErrorChanged)
        return ok

    @Slot()
    def clearDbc(self) -> None:
        self._set_if_changed(self, "_current_dbc", "", self.currentDbcChanged)

    def _on_dbc_loaded(self, event: Any) -> None:
        db_file_path = getattr(event, "db_file_path", None)
        if db_file_path is None:
            db_file_path = getattr(event, "dbc_file_path", None)
        if db_file_path is None:
            db_file_path = getattr(event, "file_path", "")

        self._set_if_changed(self, "_loading", False, self.loadingChanged)
        self._set_if_changed(self, "_current_dbc", str(db_file_path), self.currentDbcChanged)
        self._set_if_changed(self, "_last_error", "", self.lastErrorChanged)

    def _on_dbc_failed(self, event: Any) -> None:
        self._set_if_changed(self, "_loading", False, self.loadingChanged)
        message = getattr(event, "message", "Failed to parse DBC")
        self._set_if_changed(self, "_last_error", str(message), self.lastErrorChanged)
