from __future__ import annotations

from typing import Any

from PySide6.QtCore import Property, Signal, Slot

# from .base_view_model import BaseViewModel
from cansrv.file_service import get_file_service, DBCId
from cansrv.application_events import DBCLoadedEvent
from fs_test.mock_vm import ParseModel, DBCModel
from pathlib import Path
from dataclasses import dataclass

from PySide6.QtCore import (
    Qt,
    QModelIndex,
    QAbstractListModel,
)

""" NOTE: This is for cache the data, so that will not re-load the data from disk each evaluatation"""
@dataclass(slots=True)
class DbcItem:
    dbc_id: DBCId
    file_path: Path

    @property
    def file_name(self) -> str:
        return self.file_path.name
    
class DbcListModel(QAbstractListModel):
    DbcIdRole = Qt.UserRole + 1
    FileNameRole = Qt.UserRole + 2
    FilePathRole = Qt.UserRole + 3

    def __init__(self, parent=None):
        super().__init__(parent)
        self._items: list[DbcItem] = []

    # ------------------------
    # Required Qt overrides
    # ------------------------

    def rowCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0
        return len(self._items)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        item = self._items[index.row()]

        if role in (Qt.DisplayRole, self.FileNameRole):
            return item.file_name

        if role == self.FilePathRole:
            return str(item.file_path)

        if role == self.DbcIdRole:
            return item.dbc_id

        return None

    def roleNames(self):
        return {
            self.DbcIdRole: b"dbcId",
            self.FileNameRole: b"fileName",
            self.FilePathRole: b"filePath",
        }

    # ------------------------
    # Public API
    # ------------------------

    def add(self, item: DbcItem):
        row = len(self._items)

        self.beginInsertRows(QModelIndex(), row, row)
        self._items.append(item)
        self.endInsertRows()

    def clear(self):
        self.beginResetModel()
        self._items.clear()
        self.endResetModel()

    def remove(self, dbc_id: DBCId):
        for row, item in enumerate(self._items):
            if item.dbc_id == dbc_id:
                self.beginRemoveRows(QModelIndex(), row, row)
                del self._items[row]
                self.endRemoveRows()
                return

    def contains(self, dbc_id: DBCId) -> bool:
        return any(item.dbc_id == dbc_id for item in self._items)

    def get(self, row: int) -> DbcItem:
        return self._items[row]

    def dbc_id(self, row: int) -> DBCId:
        return self._items[row].dbc_id

    def index_of(self, dbc_id: DBCId) -> int:
        for row, item in enumerate(self._items):
            if item.dbc_id == dbc_id:
                return row
        return -1

    def __len__(self):
        return len(self._items)
    
class DbcViewModel(DBCModel):
    dbcChanged = Signal()

    def __init__(self):
        super().__init__()
        self._file_service = get_file_service()
        self._dbc_id: DBCId | None = None
        self.dbcs = DbcListModel()

    @property
    def dbc_id(self):
        return self._dbc_id

    @dbc_id.setter
    def dbc_id(self, value):
        if self._dbc_id == value:
            return
        self._dbc_id = value
        self.dbcChanged.emit()

    def on_dbc_loaded(self, event: DBCLoadedEvent):
        DBCModel.on_dbc_model_loaded(event)

        candb = self._file_service.get_candb_data(event.dbc_id)

        if not self.dbcs.contains(event.dbc_id):
            self.dbcs.add(
                DbcItem(
                    dbc_id=event.dbc_id,
                    file_path=candb.file_path,
                )
            ) 

        # NOTE: new dbc load does not means the screen must display it, just add to the list
        #self.dbc_id = event.dbc_id

    @Slot(str)
    def loadDBC(self, db_file_path: str) -> None:
        # TODO: Could implement cache here if the same file_path and track changed
        self._file_service.parse_dbc_file(db_file_path)

    """ ui binding 
    Store selected_dbc in ViewModel
    ComboBox

    ↓

    currentIndexChanged

    ↓

    vm.selected_dbc = ...

    ↓

    dbcChanged.emit()

    ↓

    Properties re-evaluate

    This is the classic MVVM approach.    
    """
    @property
    def dbc_num(self) -> int:
        return len(self.dbcs)
    
    @property
    def has_dbc(self) -> bool:
        return self._dbc_id is not None

    @property
    def dbc_messages_count(self) -> int:
        if self.dbc_id is None:
            return 0
        candb = get_file_service().get_candb_data(self.dbc_id)
        msg_defs = list(candb.messages)
        return len(msg_defs)

    @property
    def current_dbc_file(self) -> str:
        #TODO: Could use the DbcItem for cache instead
        candb = get_file_service().get_candb_data(self.dbc_id)
        return str(candb.file_path)

    @property
    def message_lists(self) -> list[str]:
        candb = self._candb_info
        if candb is None:
            return []

        messages: list[str] = []
        msg_defs = list(getattr(candb, "messages", []) or [])
        for msg in msg_defs:
            frame_id = getattr(msg, "frame_id", None)
            msg_name = str(getattr(msg, "name", "") or "")
            if frame_id is None:
                messages.append(msg_name)
            else:
                messages.append(f"[{int(frame_id):03X}] {msg_name}")

        # de-dup while preserving order for stable UI listbox rendering
        return list(dict.fromkeys(messages))

    @property
    def signal_lists(self) -> list[str]:
        candb = self._candb_info
        if candb is None:
            return []

        signals: list[str] = []
        msg_defs = list(getattr(candb, "messages", []) or [])
        for msg in msg_defs:
            msg_name = str(getattr(msg, "name", "") or "")
            for sig in list(getattr(msg, "signals", []) or []):
                sig_name = str(getattr(sig, "name", "") or "")
                if not sig_name:
                    continue
                if msg_name:
                    signals.append(f"{msg_name}.{sig_name}")
                else:
                    signals.append(sig_name)

        # de-dup while preserving order for stable UI listbox rendering
        return list(dict.fromkeys(signals))