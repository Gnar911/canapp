""" NOTE: This is not actually a problematic circular object dependency. 
        It's a normal bidirectional object relationship."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Callable, Any, Tuple, Set
from cansrv.module.fs_core import ParsedEntry
from collections import defaultdict
from enum import Enum
from pathlib import Path
import mmap as _mmap
import struct
import heapq
import cantools
from cantools.database import Database
from lw.logger_setup import LOG
# region Class: Data (Signal/Message/CanInfo/BirateFDInfo...)
SignalName = str
RawValue = int
value = str

@dataclass
class DecodedSignalLine:
    name: str
    value: str
    unit: str

    changed: bool = False

    parent: CANLogLine | None = field(
        default=None,
        repr=False,
        compare=False,
    )

    @property
    def signal_line(self) -> str:
        text = f"{self.name}: {self.value}"

        if self.unit:
            text += f" {self.unit}"

        return text

    # def get_format_signal_show(self, max_len_name: int = 30):
    #     name = self.signal_name.ljust(max_len_name)
    #     if not self.is_choice_value:
    #         show_value = f"{self.value} {self.value_unit}"
    #     else:
    #         show_value = self.value_choice_str
    #     return f"{name} = {show_value}"
    
Signal = DecodedSignalLine

# """ TODO: With the data no cost performce to calculate like message_name... 
#         -> No need to store cache/state for it, use runtime calculate by @property"""
# @dataclass
# class Message:
#     # can_id: int
#     """TODO: Bind this to can_id"""
#     #_msg_info: cantools.database.can.Message
#     is_fd: bool
#     periodic: float
#     direction: str  # 'Rx' or 'Tx'
#     data_len: int
#     data: List[int]
#     changed: bool
#     curr_timestamp: float = field(default=0.0)
#     last_timestamp: float = field(default=0.0)
#     is_need_update_signal: bool = field(default=False)
#     _cached_signals: Dict[str, Signal] = field(default_factory=dict)
#     signame_max_len: int = field(default=0)
#     last_data: List[int] = field(default_factory=list)
#     _runtime_can_id: int = field(default=0)
#     _runtime_message_name: str = field(default="")

#     @property
#     def timediff(self) -> float:
#         if self.curr_timestamp > self.last_timestamp:
#             return self.curr_timestamp - self.last_timestamp
#         else:
#             return 0.0
    
#     @property
#     def checkum(self) -> int:
#         return 0

#     # @property
#     # def decode_data(self) -> bytes:
#     #     return bytes(self.data)

#     # def encode(
#     #     self,
#     #     scaling: bool = False,
#     #     padding: bool = False,
#     #     strict: bool = True,
#     # ) -> bytes:
#     #     """
#     #     Encode payload bytes using only current `_cached_signals` raw values.

#     #     - Updates `self.data` and `self.data_len` from encoded payload.
#     #     Returns encoded payload bytes.
#     #     """
#     #     if not self.msg_info:
#     #         raise ValueError("Message info is not available for encoding")

#     #     if self.can_id != self.msg_info.frame_id:
#     #         raise ValueError("CAN ID does not match bound message definition")

#     #     if not self._cached_signals:
#     #         raise ValueError("No cached signals available to encode payload")

#     #     signal_values: Dict[str, Any] = {}
#     #     for sig_name, sig in self._cached_signals.items():
#     #         if sig is None or sig.raw_value is None:
#     #             raise ValueError(f"Cached signal '{sig_name}' has invalid raw value")
#     #         signal_values[sig_name] = int(sig.raw_value)

#     #     try:
#     #         payload = self.msg_info.encode(
#     #             signal_values,
#     #             scaling=scaling,
#     #             padding=padding,
#     #             strict=strict,
#     #         )
#     #     except Exception as exc:
#     #         LOG.critical(f"Encode payload failed for CANID[{self.can_id:X}]: {exc}")
#     #         raise

#     #     self.last_data = list(self.data)
#     #     self.data = list(payload)
#     #     self.data_len = len(self.data)
#     #     self.changed = self.last_data != self.data
#     #     return payload
    
#     def update_current_timestamp(self, curr: float):
#         # shift last curr to last timestamp
#         self.last_timestamp = self.curr_timestamp
#         # replace last curr to new curr
#         self.curr_timestamp = curr
        
#     @property
#     def dlc(self):
#         # Failsafe if len larger than 64
#         dlc = 15
#         if not self.is_fd or self.data_len <= 8:
#             # CAN Standard
#             dlc = 8
#         elif self.data_len <= 12:
#             dlc = 9
#         elif self.data_len <= 16:
#             dlc = 10
#         elif self.data_len <= 20:
#             dlc = 11
#         elif self.data_len <= 24:
#             dlc = 12
#         elif self.data_len <= 32:
#             dlc = 13
#         elif self.data_len <= 48:
#             dlc = 14
#         elif self.data_len <= 64:
#             dlc = 15
#         return dlc

#     @property
#     def signals(self) -> Dict[str, Signal]:
#         return self._cached_signals

#     # def cal_signal_value(self) -> Dict[str, Signal]:
#     #     if not self.msg_info:
#     #         return {}
        
#     #     if self.can_id != self.msg_info.frame_id:
#     #         return {}
#     #     # Chuẩn hóa data, nếu data len không đúng so với database
#     #     # thì có khả năng decode bị fail, nên cần lấp đầy hoặc cắt bớt data trước khi decode
#     #     # tuy nhiên cần báo lỗi data đấy vào log
#     #     if self.msg_info.length != len(self.data):
#     #         LOG.critical(f"CANID[{self.can_id:X}] Data size not valid with database: valid len[{self.msg_info.length}], real len[{len(self.data)}]")
#     #         self.data = (self.data + [0] * self.msg_info.length)[:self.msg_info.length]
#     #         self.data_len = self.msg_info.length
#     #     try:
#     #         sigs = self.msg_info.decode(self.decode_data, decode_choices=False, scaling=False, allow_truncated=True)
#     #         last_sigs = sigs.copy()            
#     #         if self.changed:
#     #             last_sigs = self.msg_info.decode(bytes(self.last_data), decode_choices=False, scaling=False, allow_truncated=True)
#     #     except Exception as e:
#     #         LOG.critical(f"Process Signal has unknown exception: {e}")
#     #         return {}
        
#     #     signals = {}
#     #     for sig in sigs.items():
#     #         sig_name = sig[0]
#     #         sig_info = self.msg_info.get_signal_by_name(sig_name)
#     #         sig_raw_value = int(sig[1])
#     #         sigchange = False

#     #         if self.changed:
#     #             if sig_name not in last_sigs:
#     #                 sigchange = True
#     #             else:
#     #                 if last_sigs[sig_name] != sig_raw_value:
#     #                     sigchange = True
#     #         signal = Signal(
#     #             _sig_info = sig_info,
#     #             raw_value=sig_raw_value,
#     #             is_cnt=False,
#     #             is_chk=False,
#     #             changed=sigchange,
#     #         )
#     #         signals[sig_name] = signal
#     #         if len(sig_name) > self.signame_max_len:
#     #             self.signame_max_len = len(sig_name)
        
#     #     self._cached_signals = signals
#     #     return signals


#     def get_signals_value_show(self) -> Dict[str,str]:
#         if not self.signals or len(self.signals) == 0:
#             return {}
#         ret = {}
#         for signame, siginfo in self.signals.items():
#             ret[signame] = siginfo.get_format_signal_show(self.signame_max_len)
#         return ret

#     def get_signal_raw_value_by_name(self, signal_name):
#         for sig_n in self.signals:
#             if sig_n ==  signal_name:
#                 return self.signals[sig_n].raw_value

#     def get_signals_name_list(self) -> List[str]:
#         if len(self.signals.keys()) > 0:
#             return [key for key in self.signals.keys()]

#     def get_format_timediff(self) -> str:
#         seconds = self.timediff
#         if seconds < 1:
#             return f"{int(seconds * 1000)}ms"
#         elif seconds < 60:
#             return f"{round(seconds, 1)}s"
#         elif seconds < 3600:
#             minutes = int(seconds // 60)
#             remaining_seconds = round(seconds % 60, 1)
#             return f"{minutes}m{remaining_seconds}s"
#         else:
#             hours = int(seconds // 3600)
#             minutes = int((seconds % 3600) // 60)
#             remaining_seconds = round(seconds % 60, 1)
#         return f"{hours}h{minutes}m{remaining_seconds}s"

@dataclass
class SignalMetadata:
    timestamp: float
    raw_value: Optional[int] = None
    value: Optional[float] = None


# """ NOTE: For presentation data"""
# @dataclass(frozen=True)
# class ColumnInfo:
#     title: str


# class ColumnProperty(property):
#     def __init__(
#         self,
#         getter: Callable,
#         title: str,
#     ):
#         super().__init__(getter)
#         self.column_info = ColumnInfo(title)


# def column(title: str):
#     def decorator(getter):
#         return ColumnProperty(
#             getter,
#             title,
#         )

#     return decorator

""" NOTE Linking primarary key

                 LogRowId(42)
                     │
          ┌──────────┴──────────┐
          ▼                     ▼
    ParsedEntry             CANLogLine
    row_id = 42             row_id = 42

"""
@dataclass(frozen=True)
class LogRowId:
    value: int

""" 20260723 NOTE: A UI View data need Presentation + Data to 2 ways UI -> Model, Model -> UI
            For example the QStandardItem have text, data
    # row_index: LogRowId
    # channel: str
    # can_id: int
    # direction: str  # 'Rx' or 'Tx'
    # data_len: int
    # data: list[int]
    # changed: bool = False  # True if raw_data changed from previous of same CAN ID
    # timestamp: float = 0.0
    # last_timestamp: float = 0.0
"""
@dataclass
class CANLogLine:
    data_model: ParsedEntry

    #line_number: int = 0
    _timediff: float = 0.0
    _user_message_name: str = field(default="")
    #message_obj: Optional[Message] = field(default=None)
    """ NOTE: Qt Index Model will handle the look up index mapping for us, so do not need to store dict here."""
    signals: list[DecodedSignalLine] = field(default_factory=list)
    last_data: list[int] = field(default=list)
    _color_id: str = ""

    @property
    def channel(self) -> str:
        return str(self.data_model.channel)

    @channel.setter
    def channel(self, value: str) -> None:
        self.data_model.channel = str(value)

    @property
    def can_id(self) -> int:
        return int(self.data_model.can_id)

    @can_id.setter
    def can_id(self, value: int) -> None:
        self.data_model.can_id = int(value)

    @property
    def direction(self) -> str:
        return str(self.data_model.direction)

    @direction.setter
    def direction(self, value: str) -> None:
        self.data_model.direction = value

    @property
    def data_len(self) -> int:
        return int(self.data_model.data_len)

    @data_len.setter
    def data_len(self, value: int) -> None:
        self.data_model.data_len = int(value)

    @property
    def data(self):
        return self.data_model.data

    # @data.setter
    # def data(self, value: list[int]) -> None:
    #     clipped = [
    #         int(v) & 0xFF
    #         for v in value
    #     ]
    #     self.data_model.data = bytes(clipped)
    #     self.data_model.data_len = len(clipped)

    @property
    def changed(self) -> bool:
        return bool(self.data_model.changed)

    @changed.setter
    def changed(self, value: bool) -> None:
        self.data_model.changed = int(bool(value))

    @property
    def timestamp(self) -> float:
        return float(self.data_model.timestamp)

    @timestamp.setter
    def timestamp(self, value: float) -> None:
        self.data_model.timestamp = float(value)

    @property
    def last_timestamp(self) -> float:
        return float(self.data_model.last_timestamp)

    @last_timestamp.setter
    def last_timestamp(self, value: float) -> None:
        self.data_model.last_timestamp = float(value)

    @property
    def line_number(self) -> int:
        return int(self.data_model.line_number)

    @line_number.setter
    def line_number(self, value: int) -> None:
        # line_number/row_id may be read-only from pybind depending on build.
        try:
            self.data_model.line_number = int(value)
        except Exception:
            pass

    """ NOTE: 
    CANLogLine.from_parsed_entry(row) is an alternative way to construct a CANLogLine
    """
    @classmethod
    def from_parsed_entry(
        cls,
        entry: ParsedEntry,
    ) -> "CANLogLine":
        return cls(data_model=entry)

    def to_parsed_entry(
        self,
    ) -> ParsedEntry:
        return self.data_model
    
    @property
    def message_line(self) -> str:
        return self.format_line_log()

    @property
    def str_timestamp(self) -> str:
        return f"{self.timestamp:.6f}"

    @property
    def str_diff(self) -> str:
        return self.get_format_timediff()

    @property
    def direction_display(self) -> str:
        return self.direction

    @property
    def can_id_str(self) -> str:
        return f"{self.can_id:X}"

    @property
    def data_len_display(self) -> int:
        return self.data_len

    @property
    def raw_data_bytes(self) -> str:
        return self.raw_data
    
    @property 
    def raw_data(self) -> str:
        # Hex string like "00 1A FF"
        return " ".join(f"{int(b) & 0xFF:02X}" for b in self.data)

    @property 
    def last_raw_data(self) -> str:
        return " ".join(f"{int(b) & 0xFF:02X}" for b in self.last_data)

    @property
    def channel_idx(self) -> int:
        raw = str(self.channel or "")
        digits = ""
        for ch in reversed(raw):
            if ch.isdigit():
                digits = ch + digits
            elif digits:
                break

        if digits:
            try:
                return int(digits)
            except Exception:
                return 0

        return 0
    
    @property
    def color_id(self) -> str:
        return self._color_id

    def set_color(self, value: str):
        self._color_id = value

    @property
    def timediff(self) -> float:
        if self._timediff > 0.0:
            return self._timediff
        
        if self.timestamp > self.last_timestamp:
            return self.timestamp - self.last_timestamp
        else:
            return 0.0
        
    @timediff.setter
    def timediff(self, value: float):
        self._timediff = float(value)

    def get_format_timediff(self) -> str:
        seconds = self.timediff
        if seconds < 1:
            return f"{int(seconds * 1000)}ms"
        elif seconds < 60:
            return f"{round(seconds, 1)}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            remaining_seconds = round(seconds % 60, 1)
            return f"{minutes}m{remaining_seconds}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            remaining_seconds = round(seconds % 60, 1)
        return f"{hours}h{minutes}m{remaining_seconds}s"
    
    """ If the parsed file have no message name -> Display one in DBC"""
    @property
    def message_name(self) -> str:
        return self._user_message_name
        
    @message_name.setter
    def message_name(self, value: str):
        self._user_message_name = value

    """ 2026/02/08: ljust() only works with monospace fontsv """
    def format_line_log(self, message_name_max_len = 30) -> str:
        message_name_len = message_name_max_len if message_name_max_len > 30 else 30
        str_timestamp = f"{self.timestamp:.6f}".ljust(15)
        channel_idx_str = f"CH{self.channel_idx}".ljust(4)
        direction = self.direction.ljust(4)
        str_diff = self.get_format_timediff()
        can_id_str = f"{self.can_id:X}".rjust(8)
        message_name = self.message_name
        name = message_name.ljust(message_name_len)
        separator = " - " if message_name else "   "
        data_len = str(self.data_len).ljust(3)
        raw_data_bytes = self.raw_data.upper()
        return f"{str_timestamp:>9} {str_diff:<10} {channel_idx_str:<4} {direction:<2} {can_id_str:>8}{separator}{name:<{message_name_len}} {data_len:>2}: {raw_data_bytes}"
    

""" 20260716 NOTE: This class is the Viewmodel data for displaying a log line.
                It should not contains the business logic like cantools.database.can.Message
"""
# @dataclass
# class CANLogLine:
#    # """ This is the data from parse, not guarantee to map with DBC"""
#    # """ Modify for write operation, then should re-calculate the msg and signal"""
#     channel: str
#     can_id: int
#     direction: str  # 'Rx' or 'Tx'
#     data_len: int
#     data: list[int]
#     changed: bool = False  # True if raw_data changed from previous of same CAN ID
#     line_number: int = 0
#     timestamp: float = 0.0
#     last_timestamp: float = 0.0
#     _timediff: float = 0.0
#     _user_message_name: str = field(default="")
#     #message_obj: Optional[Message] = field(default=None)
#     """ NOTE: Qt Index Model will handle the look up index mapping for us, so do not need to store dict here."""
#     signals: list[DecodedSignalLine] = field(default=list)
#     last_data: list[int] = field(default=list)
#     _color_id: str = ""
    
#     @property 
#     def raw_data(self) -> str:
#         # Hex string like "00 1A FF"
#         return " ".join(f"{int(b) & 0xFF:02X}" for b in self.data)

#     @property 
#     def last_raw_data(self) -> str:
#         return " ".join(f"{int(b) & 0xFF:02X}" for b in self.last_data)

#     @property
#     def channel_idx(self) -> int:
#         raw = str(self.channel or "")
#         digits = ""
#         for ch in reversed(raw):
#             if ch.isdigit():
#                 digits = ch + digits
#             elif digits:
#                 break

#         if digits:
#             try:
#                 return int(digits)
#             except Exception:
#                 return 0

#         return 0
    
#     @property
#     def color_id(self) -> str:
#         return self._color_id

#     def set_color(self, value: str):
#         self._color_id = value

#     @property
#     def timediff(self) -> float:
#         if self._timediff > 0.0:
#             return self._timediff
        
#         if self.timestamp > self.last_timestamp:
#             return self.timestamp - self.last_timestamp
#         else:
#             return 0.0
        
#     @timediff.setter
#     def timediff(self, value: float):
#         self._timediff = float(value)

#     def get_format_timediff(self) -> str:
#         seconds = self.timediff
#         if seconds < 1:
#             return f"{int(seconds * 1000)}ms"
#         elif seconds < 60:
#             return f"{round(seconds, 1)}s"
#         elif seconds < 3600:
#             minutes = int(seconds // 60)
#             remaining_seconds = round(seconds % 60, 1)
#             return f"{minutes}m{remaining_seconds}s"
#         else:
#             hours = int(seconds // 3600)
#             minutes = int((seconds % 3600) // 60)
#             remaining_seconds = round(seconds % 60, 1)
#         return f"{hours}h{minutes}m{remaining_seconds}s"
    
#     """ If the parsed file have no message name -> Display one in DBC"""
#     @property
#     def message_name(self) -> str:
#         return self._user_message_name
        
#     @message_name.setter
#     def message_name(self, value: str):
#         self._user_message_name = value

#     """ 2026/02/08: ljust() only works with monospace fontsv """
#     def format_line_log(self, message_name_max_len = 30) -> str:
#         message_name_len = message_name_max_len if message_name_max_len > 30 else 30
#         str_timestamp = f"{self.timestamp:.6f}".ljust(15)
#         channel_idx_str = f"CH{self.channel_idx}".ljust(4)
#         direction = self.direction.ljust(4)
#         str_diff = self.get_format_timediff()
#         can_id_str = f"{self.can_id:X}".rjust(8)
#         message_name = self.message_name
#         name = message_name.ljust(message_name_len)
#         separator = " - " if message_name else "   "
#         data_len = str(self.data_len).ljust(3)
#         raw_data_bytes = self.raw_data.upper()
#         return f"{str_timestamp:>9} {str_diff:<10} {channel_idx_str:<4} {direction:<2} {can_id_str:>8}{separator}{name:<{message_name_len}} {data_len:>2}: {raw_data_bytes}"

    

""" STRICT PERFORMACE CONSIDERATION: This class is designed"""
# @dataclass
# class CANLogFile:
#     file_path: str
#     file_dump: str = field(default="")
#     total_lines: int = field(default=0)
#     verified_size: int = field(default=0)
#     log_entries: Dict[int, CANLogLine] = field(default_factory=dict) # Collecting at parsing time
#     can_ids: list[int] = field(default_factory=list) # Collecting at parsing time
#     messsages: List[Message] = field(default_factory=list)
#     canid_lines_index: Dict[int, List[int]] = field(default_factory=dict)
#     canid_line_pos_index: Dict[int, Dict[int, int]] = field(default_factory=dict)
#     signal_lines_index: Dict[int, Dict[str, List[int]]] = field(default_factory=dict)
#     signal_line_pos_index: Dict[int, Dict[str, Dict[int, int]]] = field(default_factory=dict)
#     signal_timestamps_index: Dict[int, Dict[str, List[float]]] = field(default_factory=dict)
#     signal_raw_values_index: Dict[int, Dict[str, List[Optional[int]]]] = field(default_factory=dict)
#     signal_values_index: Dict[int, Dict[str, List[Optional[float]]]] = field(default_factory=dict)

#     @property
#     def file_name(self) -> str:
#         if not self.file_path:
#             return ""
#         return Path(self.file_path).name

#     @property
#     def signal_names(self) -> List[str]:
#         return list({
#             signal_name
#             for signals_by_name in self.signal_lines_index.values()
#             for signal_name in signals_by_name
#         })

#     def clear_signal_metadata(self):
#         self.canid_lines_index.clear()
#         self.canid_line_pos_index.clear()
#         self.signal_lines_index.clear()
#         self.signal_line_pos_index.clear()
#         self.signal_timestamps_index.clear()
#         self.signal_raw_values_index.clear()
#         self.signal_values_index.clear()

#     def upsert_signal_metadata(
#         self,
#         line_number: int,
#         can_id: int,
#         signal_name: str,
#         timestamp: float,
#         raw_value: Optional[int] = None,
#         value: Optional[float] = None,
#     ):
#         if can_id not in self.canid_lines_index:
#             self.canid_lines_index[can_id] = []
#             self.canid_line_pos_index[can_id] = {}

#         if can_id not in self.signal_lines_index:
#             self.signal_lines_index[can_id] = {}
#             self.signal_line_pos_index[can_id] = {}
#             self.signal_timestamps_index[can_id] = {}
#             self.signal_raw_values_index[can_id] = {}
#             self.signal_values_index[can_id] = {}

#         if signal_name not in self.signal_lines_index[can_id]:
#             self.signal_lines_index[can_id][signal_name] = []
#             self.signal_line_pos_index[can_id][signal_name] = {}
#             self.signal_timestamps_index[can_id][signal_name] = []
#             self.signal_raw_values_index[can_id][signal_name] = []
#             self.signal_values_index[can_id][signal_name] = []

#         # [can-id].append(line)
#         can_line_pos = self.canid_line_pos_index[can_id]
#         if line_number not in can_line_pos:
#             can_line_pos[line_number] = len(self.canid_lines_index[can_id])
#             self.canid_lines_index[can_id].append(line_number)

#         # [can-id][signal_name].append(line/timestamp/raw/value)
#         signal_line_pos = self.signal_line_pos_index[can_id][signal_name]
#         signal_lines = self.signal_lines_index[can_id][signal_name]
#         signal_timestamps = self.signal_timestamps_index[can_id][signal_name]
#         signal_raw_values = self.signal_raw_values_index[can_id][signal_name]
#         signal_values = self.signal_values_index[can_id][signal_name]

#         if line_number in signal_line_pos:
#             idx = signal_line_pos[line_number]
#             signal_timestamps[idx] = timestamp
#             signal_raw_values[idx] = raw_value
#             signal_values[idx] = value
#         else:
#             signal_line_pos[line_number] = len(signal_lines)
#             signal_lines.append(line_number)
#             signal_timestamps.append(timestamp)
#             signal_raw_values.append(raw_value)
#             signal_values.append(value)

#     def get_signal_metadata(
#         self,
#         can_id: int,
#         signal_name: str,
#     ) -> List[SignalMetadata]:
#         lines = self.signal_lines_index.get(can_id, {}).get(signal_name, [])
#         timestamps = self.signal_timestamps_index.get(can_id, {}).get(signal_name, [])
#         raw_values = self.signal_raw_values_index.get(can_id, {}).get(signal_name, [])
#         values = self.signal_values_index.get(can_id, {}).get(signal_name, [])

#         result: List[SignalMetadata] = []
#         for idx in range(len(lines)):
#             result.append(
#                 SignalMetadata(
#                     timestamp=timestamps[idx],
#                     raw_value=raw_values[idx],
#                     value=values[idx],
#                 )
#             )
#         return result

#     def get_messages_by_timestamp(self, st: float, target_search: List[CANLogLine]) -> List[CANLogLine]:
#         return self.get_messages_by_timestamp_range(st, st, target_search)

#     def get_all_can_ids(self) -> List[int]:
#         return self.can_ids
    
#     def get_all_lines(self) -> List[CANLogLine]:
#         return list(self.log_entries.values())

#     def get_file_name(self) -> str:
#         return self.file_name

#     def set_color_for_lines(self, lines: List[CANLogLine], color: str):
#         internal_ids = {id(line) for _,line in self.log_entries.items()}
#         for line in lines:
#             if id(line) not in internal_ids:
#                 LOG.critical("Skipping foreign CANLogLine object")
#                 continue
#             line.set_color(color)

#     def clear_color_for_lines(self, lines: List[CANLogLine]):
#         internal_ids = {id(line) for _,line in self.log_entries.items()}
#         for line in lines:
#             if id(line) not in internal_ids:
#                 LOG.critical("Skipping foreign CANLogLine object")
#                 continue
#             line.set_color("")

#     def get_timestamps_of_mux_signal_by_id(
#         self,
#         target_signal_names: Dict[int, List[str]],
#         cb: Callable
#         ) -> Dict[str, List[float]]:
#         result:  Dict[str, List[float]] = {}
#         #for can_id, signal_names in target_signal_names:
#         target_lines = self.get_messages_by_list_id([target_signal_names.keys()])
#         for i, line in enumerate(target_lines):
#             signals = line.message_obj.signals
#             for sig_name, _ in signals.items(): 
#                 if sig_name in [target_signal_names.values()]:
#                     st = line.timestamp
#                     result[sig_name].append(st)
#         return result

#     def get_timestamps_of_signal_by_list_ids(
#         self,
#         target_signal_names: Dict[int, List[str]]
#         ) -> Dict[str, List[float]]:
#         result: Dict[str, List[float]]  = defaultdict(list)
#         for i, (can_id, signal_names) in enumerate(target_signal_names.items()):
#             sts: List[float] = []
#             target_lines = self.get_messages_by_list_id([can_id])
#             sts = self.get_timestamps_of_target_log_line(target_lines)
#             for signal_name in signal_names:
#                 result[signal_name] = sts
#         return result

#     def get_timestamps_of_target_log_line(
#         self,
#         target_log_lines: List[CANLogLine]
#         ) -> List[float]:
#         return [line.timestamp for line in target_log_lines]

#     def get_signal_values_by_ids(
#         self, 
#         can_ids: List[int],
#         target_signal_names: List[str],
#         cb: Callable = None
#     ) -> Dict[str, List[Any]]:
#         result = {name: [] for name in target_signal_names}
#         for i, can_id in enumerate(can_ids):
#             target_msg_lines = self.get_messages_by_list_id([can_id])
#             for line in target_msg_lines:
#                 # if line.message_obj.cal_signal_value() or True:
#                     signals = line.message_obj.signals
#                     for sig_name, sig in signals.items(): 
#                         if sig_name in target_signal_names:   
#                             val = sig.value
#                             result[sig_name].append(val)
#         return result

#     def get_messages_by_list_signal_raw_value(
#         self,
#         signal_search: Dict[SignalName, List[int]],
#         can_ids: List[int] = None,
#     ) -> List[CANLogLine]:
#         if not can_ids:
#             raise KeyError("Either can_ids or target_search_lines must be provided")
#         target_search_lines = self.get_messages_by_list_id(can_ids)
#         return self.get_signals_by_list_signal_raw_value(signal_search, target_search_lines)
    
#     def get_signals_by_list_signal_raw_value(
#             self,
#             signal_search: Dict[SignalName, List[int]],
#             target_search_lines: List[CANLogLine]
#             ):
#         result = []
#         signal_search: Dict[SignalName, List[int]] = {}
        
#         for entry in target_search_lines:
#             # if entry.message_obj.cal_signal_value() or True:
#                 for signal_name in entry.message_obj.signals:
#                     if signal_name in signal_search:
#                         if entry.message_obj.signals[signal_name].raw_value is None:
#                             result.append(entry)
#                         elif entry.message_obj.signals[signal_name].raw_value in signal_search[signal_name]:
#                             result.append(entry)
#                             break
#         return result

#     """
#     This method shall return a list of references to the result CANLogLine
#     """
#     def get_messages_by_list_id(
#         self, 
#         can_ids: List[int], 
#         target_search_lines: List[CANLogLine] = None,
#         ) -> List["CANLogLine"]:
#         if target_search_lines:
#             return [entry for entry in target_search_lines if entry.can_id in can_ids]
#         else:
#             return [entry for _, entry in self.log_entries.items() if entry.can_id in can_ids]

#     def get_dict_messages_by_list_id(
#         self,
#         can_ids: List[int],
#         target_search_lines: List[CANLogLine] | None = None,
#     ) -> Dict[int, List[CANLogLine]]:

#         result: Dict[int, List[CANLogLine]] = defaultdict(list)

#         source = target_search_lines if target_search_lines is not None \
#                 else self.log_entries.values()

#         for entry in source:
#             if entry.can_id in can_ids:
#                 result[entry.can_id].append(entry)

#         return dict(result)

#     def group_messages_by_can_id(
#         self,
#         target_search_lines: List[CANLogLine],
#     ) -> Dict[int, List[CANLogLine]]:

#         grouped: Dict[int, List[CANLogLine]] = defaultdict(list)

#         for entry in target_search_lines:
#             grouped[entry.can_id].append(entry)

#         return dict(grouped)


#     def filter_messages_by_list_id(self, can_ids: List[int]) -> List[CANLogLine]:
#         return [entry for line, entry in self.log_entries.items() if entry.can_id not in can_ids]

#     def get_messages_change_by_list_id(self, can_ids: List[int]) -> List[CANLogLine]:
#         return [entry for line, entry in self.log_entries.items() if (entry.can_id in can_ids) and (entry.changed)]

#     def get_messages_by_direction(self, direction: str, search_region: List[CANLogLine] = None):
#         return [entry for entry in search_region if entry.direction.lower() == direction.lower()]
    
#     def get_messages_by_channel(self, channel: str, search_region: List[CANLogLine] = None):
#         if search_region:
#             return [entry for entry in search_region if  entry.channel == channel]
#         else:
#             return [entry for _, entry in self.log_entries.items() if entry.channel == channel]
    
#     def get_messages_by_timestamp_range(
#         self,
#         from_t: float, 
#         to_t: float, 
#         search_region: List[CANLogLine] = None
#         ) -> List[CANLogLine]:
#         if not search_region:
#             search_region = list(self.log_entries.values())
#         return [entry for entry in search_region if entry.timestamp >= from_t and entry.timestamp <= to_t]
    
#     def get_can_ids(self, search_region: List[CANLogLine]) -> Set[int]:
#         if not search_region:
#             return set()
#         return {entry.can_id for entry in search_region}



@dataclass(init=False)
class SignalFilter:
    """ Signal info is the formula to calculate the raw_value"""
    """ BUG: Raw value could be None so it is necessary to handle the case None"""
    _signal_info: cantools.database.can.Signal = None
    _msg_info: cantools.database.can.Message = None
    _rawvalue: int = None
    _can_id: Optional[int] = None
    color: str = ""

    def __init__(
        self,
        signal_info: Optional[cantools.database.can.Signal] = None,
        message_info: Optional[cantools.database.can.Message] = None,
        rawvalue: Optional[int] = None,
        color: str = "",
        can_id: Optional[int] = None,
        _signal_info: Optional[cantools.database.can.Signal] = None,
        _msg_info: Optional[cantools.database.can.Message] = None,
        _rawvalue: Optional[int] = None,
        raw_value: Optional[int] = None,
    ):
        self._signal_info = signal_info if signal_info is not None else _signal_info
        self._msg_info = message_info if message_info is not None else _msg_info

        resolved_raw = rawvalue
        if resolved_raw is None and raw_value is not None:
            resolved_raw = raw_value
        if resolved_raw is None:
            resolved_raw = _rawvalue
        self._rawvalue = resolved_raw

        resolved_can_id = can_id
        if resolved_can_id is None and self._msg_info is not None:
            try:
                resolved_can_id = int(self._msg_info.frame_id)
            except Exception:
                resolved_can_id = None
        self._can_id = int(resolved_can_id) if resolved_can_id is not None else None

        self.color = color

    @property
    def message_name(self):
        if not self._msg_info:
            return None
        return self._msg_info.name
    
    @property
    def can_id(self):
        if not self._msg_info:
            return self._can_id
        return self._msg_info.frame_id
    
    @property
    def msg_info(self):
        return self._msg_info

    @msg_info.setter
    def msg_info(self, value: cantools.database.can.Message):
        if value is self._msg_info:
            return
        self._msg_info = value
        if value is not None:
            try:
                self._can_id = int(value.frame_id)
            except Exception:
                pass

    @property
    def signal_info(self):
        return self._signal_info

    @signal_info.setter
    def signal_info(self, value: cantools.database.can.Signal):
        if value is self._signal_info:
            return
        self._signal_info = value
        #self.notify()

    @property
    def rawvalue(self):
        return self._rawvalue

    @rawvalue.setter
    def rawvalue(self, value: int):
        if value == self._rawvalue:
            return
        self._rawvalue = value
        #self.notify()

    @property
    def sig_name(self) -> str:
        if not self._signal_info:
            return None
        return self._signal_info.name

    @property
    def signal_id(self) -> Optional[int]:
        if not self._signal_info:
            return None
        if self._signal_info.spn is None:
            return None
        return int(self._signal_info.spn)
    
    """ MOD 0127"""
    @property
    def value(self) -> str:
        if self.rawvalue is None:
            return "--"

        offset = self.signal_info.offset
        str_scale = f"{self.signal_info.scale:.15f}".rstrip('0').rstrip('.')
        scale_value = float(str_scale)
        if self.signal_info.choices:
            try:
                index = int(self._rawvalue)
                value_result = str(self.signal_info.choices[index])
            except (ValueError, KeyError):
                self.log.debug("Unknown")
                value_result = "Unknown"

        else:
            def count_decimal_places(f: float) -> int:
                s = str(f)
                if '.' in s:
                    return len(s.split('.')[-1].rstrip('0'))
                return 0
            value_raw = float(self._rawvalue)
            decimal_place = count_decimal_places(scale_value)
            value = value_raw * scale_value + offset
            value_result = str(round(value, decimal_place))
        return value_result

    @value.setter
    def value(self, physical_value: float):
        self.set_physical_value(physical_value)

    def set_physical_value(self, physical_value: float) -> bool:
        """
        Set physical value for non-choice signals.
        Conversion:
            raw = round((physical - offset) / scale)
            raw is clamped by bit length/sign
        Returns True if applied, False otherwise.
        """
        if not self.signal_info:
            return False

        if self.signal_info.choices:
            return False

        try:
            if isinstance(physical_value, str):
                physical = float(str(physical_value).strip().split()[0].replace(",", "."))
            else:
                physical = float(physical_value)
        except (TypeError, ValueError, IndexError):
            return False

        scale = float(self.signal_info.scale)
        offset = float(self.signal_info.offset)
        if scale == 0.0:
            return False

        raw = int(round((physical - offset) / scale))

        bit_length = int(self.signal_info.length)
        if bool(self.signal_info.is_signed):
            min_raw = -(2 ** (bit_length - 1))
            max_raw = (2 ** (bit_length - 1)) - 1
        else:
            min_raw = 0
            max_raw = (2 ** bit_length) - 1

        raw = max(min_raw, min(max_raw, raw))
        self.rawvalue = raw
        return True
    
    @property
    def is_choice_signal(self) -> bool:
        return self.signal_info.choices

    @property
    def choice_strings(self) -> List[str]:
        return self.get_choice_strings()

    def get_choice_strings(self) -> List[str]:
        if not self.signal_info or not self.signal_info.choices:
            return []
        return [str(choice) for _, choice in self.signal_info.choices.items()]
    
    @property
    def min_max(self) -> Tuple[int, int]:
        selected_signal = self.signal_info
        offset = selected_signal.offset
        scale_value = selected_signal.scale
        if selected_signal.choices:
            min_raw = 0
            max_raw = len(selected_signal.choices) - 1
        elif selected_signal.minimum is not None and selected_signal.maximum is not None:
            min_value = selected_signal.minimum
            max_value = selected_signal.maximum
            # Compute raw values and round appropriately to int
            min_raw = int(round((min_value - offset) / scale_value))
            max_raw = int(round((max_value - offset) / scale_value))
        else:
            min_raw = 0
            max_raw = 255  # fallback default
        return min_raw, max_raw
    
    @property
    def unit(self):
        if not self.signal_info:
            return "--"
        if not self.signal_info.unit:
            return "--"
        return self.signal_info.unit

"""
@dataclass(frozen=True)
class DeviceInfoLine:
    vendor_name: str
    channel_name: str
    channel_index: int
    state: DeviceState

    @property
    def is_available(self):
        return self.state is DeviceState.AVAILABLE

    @property
    def is_acquired(self):
        return self.state is DeviceState.ACQUIRED

    @property
    def is_disconnected(self):
        return self.state is DeviceState.DISCONNECTED
"""
