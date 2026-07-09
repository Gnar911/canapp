from abc import ABC, abstractmethod
from typing import List, Optional
from PySide6.QtCore import Qt, QModelIndex, QAbstractItemModel
from PySide6.QtCore import QModelIndex

from can_sdk.data_object import CANLogLine
from can_sdk.dbc_manager import CANDBManager

class SourceProvider(ABC):
    @abstractmethod
    def load_visible(self, first_row: int, window_size: int) -> List[CANLogLine]:
        pass

    def row_count(self) -> Optional[int]:
        """Return the actual number of valid rows for the current page, or None if unknown."""
        return None

class TreeLogDiskModel(QAbstractItemModel):
    """Lazy-load model that can fetch backing rows from a SourceProvider on demand."""
    def __init__(
        self,
        parent=None,
        **kwargs,
    ):
        super().__init__(parent)
        self._source_provider: Optional[SourceProvider] = None
        self._source_total_rows: Optional[int] = None
        self._source_exhausted = False

    def _total_rows(self) -> int:
        if self._source_provider is None:
            base_total = getattr(super(), "_total_rows", None)
            if callable(base_total):
                try:
                    return max(0, int(base_total()))
                except Exception:
                    return 0
            return 0

        if self._source_total_rows is not None:
            return max(0, int(self._source_total_rows))

        try:
            live_total = self._source_provider.row_count()
        except Exception:
            live_total = 0
        return max(0, int(live_total or 0))

    def set_source_provider(self, source_provider: Optional[SourceProvider]):
        self.beginResetModel()
        self._source_provider = source_provider
        self._source_exhausted = False
        self._source_total_rows = None
        if self._source_provider is not None:
            try:
                total = self._source_provider.row_count()
            except Exception:
                total = None
            self._source_total_rows = int(total) if total is not None else None
        self.endResetModel()

    def get_source_provider(self) -> SourceProvider:
        return self._source_provider