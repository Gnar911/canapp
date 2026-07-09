from dataclasses import dataclass, field
from typing import Optional, List, Dict, Callable, Any, Tuple, Set
from collections import defaultdict
from enum import Enum
from pathlib import Path
import mmap as _mmap
import struct
import heapq
import cantools
from lw.logger_setup import LOG
# region Class: Data (Signal/Message/CanInfo/BirateFDInfo...)
SignalName = str
RawValue = int
value = str
@dataclass
class Signal:
    raw_value: int   # DECODED DATA
    is_cnt: Optional[bool] = field(default=False) # Is signal a Counter?
    is_chk: Optional[bool] = field(default=False) # Is signal a Checksum?
    changed: Optional[bool] = field(default=False)
    _sig_info: cantools.database.can.Signal = None # STATIC DATA
    _runtime_signal_name: str = field(default="")
    _runtime_value: Optional[float] = field(default=None)

    @property
    def rawvalue(self) -> int:
        return self.raw_value

    @rawvalue.setter
    def rawvalue(self, value: int):
        self.set_raw_value(value)

    def get_raw_value(self) -> int:
        return self.raw_value

    def set_raw_value(self, value: int):
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            return

        min_raw, max_raw = self.min_max
        self.raw_value = max(min_raw, min(max_raw, parsed))

    def set_physical_value(self, physical_value: float) -> bool:
        """
        Set physical value for non-choice signal:
            raw = round((physical - offset) / scale)
            raw is clamped by min_max
        """
        if self.is_choice_value or not self.sig_info:
            return False

        try:
            if isinstance(physical_value, str):
                physical = float(str(physical_value).strip().split()[0].replace(",", "."))
            else:
                physical = float(physical_value)
        except (TypeError, ValueError, IndexError):
            return False

        scale = float(self.value_scale)
        if scale == 0.0:
            return False

        raw = int(round((physical - float(self.value_offset)) / scale))
        self.set_raw_value(raw)
        return True

    def get_choice_strings(self) -> List[str]:
        if not self._sig_info or not self._sig_info.choices:
            return []
        return [str(choice) for _, choice in self._sig_info.choices.items()]
    
    @property
    def min_max(self) -> Tuple[int, int]:
        selected_signal = self._sig_info
        if not selected_signal:
            return (0, 255)
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
    def sig_info(self):
        return self._sig_info

    @sig_info.setter
    def sig_info(self, value: cantools.database.can.Signal):
        if value is self._sig_info:
            return
        self._sig_info = value

    @property
    def signal_name(self) -> str:
        if not self.sig_info:
            return self._runtime_signal_name if self._runtime_signal_name else ""
        return self.sig_info.name

    @property
    def value_offset(self):
        if not self.sig_info:
            return None
        return self.sig_info.offset if self.sig_info.offset else 0
    
    @property
    def value_len(self):
        if not self.sig_info:
            return None
        return self.sig_info.length

    @property
    def value_choices(self):
        if not self.sig_info:
            return None
        return self.sig_info.choices if self.sig_info.choices else {}

    @property
    def value_unit(self):
        if not self.sig_info:
            return None
        return self.sig_info.unit if self.sig_info.unit else ""

    @property
    def value_scale(self):
        if not self.sig_info:
            return None
        return self.sig_info.scale if self.sig_info.scale else 1.0

    @property
    def value_float(self) -> float:
        if not self.sig_info:
            if self._runtime_value is not None:
                return float(self._runtime_value)
            return float(self.raw_value)
        if self.is_choice_value:
            raise KeyError("choice signal has no value float")
        return (float(self.raw_value) * self.value_scale) + self.value_offset

    @property
    def value(self) -> str:
        if not self.sig_info:
            if self._runtime_value is not None:
                return str(self._runtime_value)
            return str(self.raw_value)
        return self.value_choice_str if self.is_choice_value else self.value_str

    @value.setter
    def value(self, physical_value: float):
        self.set_physical_value(physical_value)

    @property
    def value_str(self) -> str:
        if not self.sig_info:
            if self._runtime_value is not None:
                return str(self._runtime_value)
            return str(self.raw_value)
        return str((float(self.raw_value) * self.value_scale) + self.value_offset)

    @property
    def value_choice(self) -> str:
        if self.value_choices is None:
            return ""
        if self.raw_value in self.value_choices:
            return f"{self.raw_value}: {self.value_choices[self.raw_value]}"
        else:
            return ""
        
    @property
    def value_choice_str(self) -> str:
        if self.value_choices is None:
            return "Unknown"
        if self.raw_value in self.value_choices:
            return str(self.value_choices[self.raw_value])
        else:
            return "Unknown"

    @property
    def is_choice_value(self) -> bool:
        if not self.value_choices:
            return False
        else:
            return True

    def cal_cnt(self):
        if self.is_cnt:
            self.raw_value += 1
            if self.raw_value >= 2**self.value_len:
                self.raw_value = 0

    def get_format_signal_show(self, max_len_name: int = 30):
        name = self.signal_name.ljust(max_len_name)
        if not self.is_choice_value:
            show_value = f"{self.value} {self.value_unit}"
        else:
            show_value = self.value_choice_str
        return f"{name} = {show_value}"
    
""" TODO: With the data no cost performce to calculate like message_name... 
        -> No need to store cache/state for it, use runtime calculate by @property"""
@dataclass
class Message:
    # can_id: int
    """TODO: Bind this to can_id"""
    _msg_info: cantools.database.can.Message
    is_fd: bool
    periodic: float
    direction: str  # 'Rx' or 'Tx'
    data_len: int
    data: List[int]
    changed: bool
    curr_timestamp: float = field(default=0.0)
    last_timestamp: float = field(default=0.0)
    is_need_update_signal: bool = field(default=False)
    _cached_signals: Dict[str, Signal] = field(default_factory=dict)
    signame_max_len: int = field(default=0)
    last_data: List[int] = field(default_factory=list)
    _runtime_can_id: int = field(default=0)
    _runtime_message_name: str = field(default="")

    @property
    def message_name(self):
        if self._msg_info is not None:
            return self._msg_info.name
        return self._runtime_message_name if self._runtime_message_name else ""
    
    @property
    def can_id(self):
        if self._msg_info is not None:
            return self._msg_info.frame_id
        return int(self._runtime_can_id)
    
    @property
    def msg_info(self):
        return self._msg_info

    @msg_info.setter
    def msg_info(self, value: cantools.database.can.Message):
        if value is self._msg_info:
            return
        self._msg_info = value

    @property
    def timediff(self) -> float:
        if self.curr_timestamp > self.last_timestamp:
            return self.curr_timestamp - self.last_timestamp
        else:
            return 0.0
    
    @property
    def checkum(self) -> int:
        return 0

    @property
    def decode_data(self) -> bytes:
        return bytes(self.data)

    def encode(
        self,
        scaling: bool = False,
        padding: bool = False,
        strict: bool = True,
    ) -> bytes:
        """
        Encode payload bytes using only current `_cached_signals` raw values.

        - Updates `self.data` and `self.data_len` from encoded payload.
        Returns encoded payload bytes.
        """
        if not self.msg_info:
            raise ValueError("Message info is not available for encoding")

        if self.can_id != self.msg_info.frame_id:
            raise ValueError("CAN ID does not match bound message definition")

        if not self._cached_signals:
            raise ValueError("No cached signals available to encode payload")

        signal_values: Dict[str, Any] = {}
        for sig_name, sig in self._cached_signals.items():
            if sig is None or sig.raw_value is None:
                raise ValueError(f"Cached signal '{sig_name}' has invalid raw value")
            signal_values[sig_name] = int(sig.raw_value)

        try:
            payload = self.msg_info.encode(
                signal_values,
                scaling=scaling,
                padding=padding,
                strict=strict,
            )
        except Exception as exc:
            LOG.critical(f"Encode payload failed for CANID[{self.can_id:X}]: {exc}")
            raise

        self.last_data = list(self.data)
        self.data = list(payload)
        self.data_len = len(self.data)
        self.changed = self.last_data != self.data
        return payload
    
    def update_current_timestamp(self, curr: float):
        # shift last curr to last timestamp
        self.last_timestamp = self.curr_timestamp
        # replace last curr to new curr
        self.curr_timestamp = curr
        
    @property
    def dlc(self):
        # Failsafe if len larger than 64
        dlc = 15
        if not self.is_fd or self.data_len <= 8:
            # CAN Standard
            dlc = 8
        elif self.data_len <= 12:
            dlc = 9
        elif self.data_len <= 16:
            dlc = 10
        elif self.data_len <= 20:
            dlc = 11
        elif self.data_len <= 24:
            dlc = 12
        elif self.data_len <= 32:
            dlc = 13
        elif self.data_len <= 48:
            dlc = 14
        elif self.data_len <= 64:
            dlc = 15
        return dlc

    @property
    def signals(self) -> Dict[str, Signal]:
        return self._cached_signals

    def cal_signal_value(self) -> Dict[str, Signal]:
        if not self.msg_info:
            return {}
        
        if self.can_id != self.msg_info.frame_id:
            return {}
        # Chuẩn hóa data, nếu data len không đúng so với database
        # thì có khả năng decode bị fail, nên cần lấp đầy hoặc cắt bớt data trước khi decode
        # tuy nhiên cần báo lỗi data đấy vào log
        if self.msg_info.length != len(self.data):
            LOG.critical(f"CANID[{self.can_id:X}] Data size not valid with database: valid len[{self.msg_info.length}], real len[{len(self.data)}]")
            self.data = (self.data + [0] * self.msg_info.length)[:self.msg_info.length]
            self.data_len = self.msg_info.length
        try:
            sigs = self.msg_info.decode(self.decode_data, decode_choices=False, scaling=False, allow_truncated=True)
            last_sigs = sigs.copy()            
            if self.changed:
                last_sigs = self.msg_info.decode(bytes(self.last_data), decode_choices=False, scaling=False, allow_truncated=True)
        except Exception as e:
            LOG.critical(f"Process Signal has unknown exception: {e}")
            return {}
        
        signals = {}
        for sig in sigs.items():
            sig_name = sig[0]
            sig_info = self.msg_info.get_signal_by_name(sig_name)
            sig_raw_value = int(sig[1])
            sigchange = False

            if self.changed:
                if sig_name not in last_sigs:
                    sigchange = True
                else:
                    if last_sigs[sig_name] != sig_raw_value:
                        sigchange = True
            signal = Signal(
                _sig_info = sig_info,
                raw_value=sig_raw_value,
                is_cnt=False,
                is_chk=False,
                changed=sigchange,
            )
            signals[sig_name] = signal
            if len(sig_name) > self.signame_max_len:
                self.signame_max_len = len(sig_name)
        
        self._cached_signals = signals
        return signals


    def get_signals_value_show(self) -> Dict[str,str]:
        if not self.signals or len(self.signals) == 0:
            return {}
        ret = {}
        for signame, siginfo in self.signals.items():
            ret[signame] = siginfo.get_format_signal_show(self.signame_max_len)
        return ret

    def get_signal_raw_value_by_name(self, signal_name):
        for sig_n in self.signals:
            if sig_n ==  signal_name:
                return self.signals[sig_n].raw_value

    def get_signals_name_list(self) -> List[str]:
        if len(self.signals.keys()) > 0:
            return [key for key in self.signals.keys()]

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

    # def get_format_message_show(self, msg_max_len: int = 30) -> str:
    #     message_name_len = max(msg_max_len, 30)
    #     can_id_str = f"{self.can_id:X}".rjust(8)
    #     name = (self.message_name or "UNKNOWN")[:message_name_len]
    #     direction = self.direction
    #     str_diff = self.get_format_timediff()
    #     int_timestamp = int(self.curr_timestamp)
    #     str_timestamp = f"{int(int_timestamp)}.{int((self.curr_timestamp - int_timestamp) * 1000):03d}"
    #     data_len = self.data_len
    #     databytes = ' '.join(f"{x:02X}" for x in self.data)

    #     return f"{str_timestamp:>9} {str_diff:<10} {direction:<2} {can_id_str:>8} - {name:<{message_name_len}} {data_len:>2}: {databytes}"

@dataclass
class SignalMetadata:
    timestamp: float
    raw_value: Optional[int] = None
    value: Optional[float] = None

@dataclass
class CANLogLine:
    """ This is the data from parse, not guarantee to map with DBC"""
    """ Modify for write operation, then should re-calculate the msg and signal"""
    channel: str
    can_id: int
    direction: str  # 'Rx' or 'Tx'
    data_len: int
    raw_data: str  # Hex string like "00 1A FF"
    changed: bool = False  # True if raw_data changed from previous of same CAN ID
    line_number: int = 0
    timestamp: float = 0.0
    last_timestamp: float = 0.0
    _timediff: float = 0.0
    _user_message_name: str = field(default="")
    message_obj: Optional[Message] = field(default=None)
    last_raw_data: Optional[str] = field(default="")
    _color_id: str = ""

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
        
    def cal_message_obj(self, msg_info: cantools.database.can.Message = None) -> Message:
        """ Just let the can log line display whatever it read from parsed file, even no recognition of this Message"""
        """ Signals will be calculated in real time (by the time it is refered) by msg_info"""
        if self.message_obj:
            if self.message_obj.msg_info == msg_info:
                return self.message_obj
        self.message_obj = Message(
            _msg_info = msg_info,
            is_fd=True,
            periodic=0.0,
            direction=self.direction,
            data_len=self.data_len,
            data=[int(x, 16) for x in self.raw_data.strip().split()],
            changed=self.changed,
            curr_timestamp=self.timestamp,
            last_timestamp=self.last_timestamp,
            is_need_update_signal=False,
            last_data=[int(x, 16) for x in self.last_raw_data.strip().split()])
        if self.data_len != len(self.message_obj.data):
            LOG.critical(f"Rawdata have wrong size: Size[{self.data_len}], Real Size[{len(self.message_obj.data)}], Data[{self.raw_data}]")
            self.message_obj.data = (self.message_obj.data + [0] * self.data_len)[:self.data_len]
        return self.message_obj

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
        if not self.message_obj:
            return ""
        if getattr(self.message_obj, "msg_info", None) is None:
            return ""
        name = self.message_obj.message_name
        return name if name is not None else ""
        
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
        
    def get_list_signal_show_fromline(self) -> Dict[str,str]:
        # Check have message obj
        if not self.message_obj:
            LOG.critical(f"Process invalid, message object be not calculated")
            return {}         
        # Cal signals 
        # self.cal_signal_for_line()
        # Get signal show
        ret = self.message_obj.get_signals_value_show()
        # Return 
        return ret
    
    def get_list_signal_name_fromline(self) -> Dict[str,str]:
        # Check have message obj
        if not self.message_obj:
            LOG.critical(f"Process invalid, message object be not calculated")
            return {}         
        # Cal signals 
        #self.cal_signal_for_line()
        # Get signal show
        ret = self.message_obj.get_signals_name_list()
        return ret

class SendState(Enum):
    NONE = 0
    PAUSED = 1
    SENDING = 2
    DISCONNETED = 3
    
@dataclass
class CANLogPlay(CANLogLine):
    send_state: SendState = SendState.NONE

    @property
    def is_disconnect(self) -> bool:
        return self.send_state == SendState.DISCONNETED

    @property
    def is_disconnected(self) -> bool:
        return self.is_disconnect

    @property
    def is_paused(self) -> bool:
        return self.send_state == SendState.PAUSED

    @property
    def is_send(self) -> bool:
        return self.send_state == SendState.SENDING

    @is_send.setter
    def is_send(self, value):
        if isinstance(value, SendState):
            self.send_state = value
            return
        if bool(value):
            self.send_state = SendState.SENDING
        elif self.send_state != SendState.DISCONNETED:
            self.send_state = SendState.PAUSED
    
# class DataLogState(Enum):
#     UNAVAILABLE = 0
#     AVAILABLE = 3

""" STRICT PERFORMACE CONSIDERATION: This class is designed"""
@dataclass
class CANLogFile:
    file_path: str
    file_dump: str = field(default="")
    total_lines: int = field(default=0)
    verified_size: int = field(default=0)
    log_entries: Dict[int, CANLogLine] = field(default_factory=dict) # Collecting at parsing time
    # state: DataLogState = DataLogState.UNAVAILABLE
    # is_loading: bool = False
    can_ids: list[int] = field(default_factory=list) # Collecting at parsing time
    messsages: List[Message] = field(default_factory=list)
    canid_lines_index: Dict[int, List[int]] = field(default_factory=dict)
    canid_line_pos_index: Dict[int, Dict[int, int]] = field(default_factory=dict)
    signal_lines_index: Dict[int, Dict[str, List[int]]] = field(default_factory=dict)
    signal_line_pos_index: Dict[int, Dict[str, Dict[int, int]]] = field(default_factory=dict)
    signal_timestamps_index: Dict[int, Dict[str, List[float]]] = field(default_factory=dict)
    signal_raw_values_index: Dict[int, Dict[str, List[Optional[int]]]] = field(default_factory=dict)
    signal_values_index: Dict[int, Dict[str, List[Optional[float]]]] = field(default_factory=dict)

    @property
    def file_name(self) -> str:
        if not self.file_path:
            return ""
        return Path(self.file_path).name

    @property
    def signal_names(self) -> List[str]:
        return list({
            signal_name
            for signals_by_name in self.signal_lines_index.values()
            for signal_name in signals_by_name
        })

    def clear_signal_metadata(self):
        self.canid_lines_index.clear()
        self.canid_line_pos_index.clear()
        self.signal_lines_index.clear()
        self.signal_line_pos_index.clear()
        self.signal_timestamps_index.clear()
        self.signal_raw_values_index.clear()
        self.signal_values_index.clear()

    def upsert_signal_metadata(
        self,
        line_number: int,
        can_id: int,
        signal_name: str,
        timestamp: float,
        raw_value: Optional[int] = None,
        value: Optional[float] = None,
    ):
        if can_id not in self.canid_lines_index:
            self.canid_lines_index[can_id] = []
            self.canid_line_pos_index[can_id] = {}

        if can_id not in self.signal_lines_index:
            self.signal_lines_index[can_id] = {}
            self.signal_line_pos_index[can_id] = {}
            self.signal_timestamps_index[can_id] = {}
            self.signal_raw_values_index[can_id] = {}
            self.signal_values_index[can_id] = {}

        if signal_name not in self.signal_lines_index[can_id]:
            self.signal_lines_index[can_id][signal_name] = []
            self.signal_line_pos_index[can_id][signal_name] = {}
            self.signal_timestamps_index[can_id][signal_name] = []
            self.signal_raw_values_index[can_id][signal_name] = []
            self.signal_values_index[can_id][signal_name] = []

        # [can-id].append(line)
        can_line_pos = self.canid_line_pos_index[can_id]
        if line_number not in can_line_pos:
            can_line_pos[line_number] = len(self.canid_lines_index[can_id])
            self.canid_lines_index[can_id].append(line_number)

        # [can-id][signal_name].append(line/timestamp/raw/value)
        signal_line_pos = self.signal_line_pos_index[can_id][signal_name]
        signal_lines = self.signal_lines_index[can_id][signal_name]
        signal_timestamps = self.signal_timestamps_index[can_id][signal_name]
        signal_raw_values = self.signal_raw_values_index[can_id][signal_name]
        signal_values = self.signal_values_index[can_id][signal_name]

        if line_number in signal_line_pos:
            idx = signal_line_pos[line_number]
            signal_timestamps[idx] = timestamp
            signal_raw_values[idx] = raw_value
            signal_values[idx] = value
        else:
            signal_line_pos[line_number] = len(signal_lines)
            signal_lines.append(line_number)
            signal_timestamps.append(timestamp)
            signal_raw_values.append(raw_value)
            signal_values.append(value)

    def get_signal_metadata(
        self,
        can_id: int,
        signal_name: str,
    ) -> List[SignalMetadata]:
        lines = self.signal_lines_index.get(can_id, {}).get(signal_name, [])
        timestamps = self.signal_timestamps_index.get(can_id, {}).get(signal_name, [])
        raw_values = self.signal_raw_values_index.get(can_id, {}).get(signal_name, [])
        values = self.signal_values_index.get(can_id, {}).get(signal_name, [])

        result: List[SignalMetadata] = []
        for idx in range(len(lines)):
            result.append(
                SignalMetadata(
                    timestamp=timestamps[idx],
                    raw_value=raw_values[idx],
                    value=values[idx],
                )
            )
        return result

    def get_messages_by_timestamp(self, st: float, target_search: List[CANLogLine]) -> List[CANLogLine]:
        return self.get_messages_by_timestamp_range(st, st, target_search)

    def get_all_can_ids(self) -> List[int]:
        return self.can_ids
    
    def get_all_lines(self) -> List[CANLogLine]:
        return list(self.log_entries.values())

    def get_file_name(self) -> str:
        return self.file_name

    def set_color_for_lines(self, lines: List[CANLogLine], color: str):
        internal_ids = {id(line) for _,line in self.log_entries.items()}
        for line in lines:
            if id(line) not in internal_ids:
                LOG.critical("Skipping foreign CANLogLine object")
                continue
            line.set_color(color)

    def clear_color_for_lines(self, lines: List[CANLogLine]):
        internal_ids = {id(line) for _,line in self.log_entries.items()}
        for line in lines:
            if id(line) not in internal_ids:
                LOG.critical("Skipping foreign CANLogLine object")
                continue
            line.set_color("")

    def get_timestamps_of_mux_signal_by_id(
        self,
        target_signal_names: Dict[int, List[str]],
        cb: Callable
        ) -> Dict[str, List[float]]:
        result:  Dict[str, List[float]] = {}
        #for can_id, signal_names in target_signal_names:
        target_lines = self.get_messages_by_list_id([target_signal_names.keys()])
        for i, line in enumerate(target_lines):
            signals = line.message_obj.signals
            for sig_name, _ in signals.items(): 
                if sig_name in [target_signal_names.values()]:
                    st = line.timestamp
                    result[sig_name].append(st)
        return result

    def get_timestamps_of_signal_by_list_ids(
        self,
        target_signal_names: Dict[int, List[str]]
        ) -> Dict[str, List[float]]:
        result: Dict[str, List[float]]  = defaultdict(list)
        for i, (can_id, signal_names) in enumerate(target_signal_names.items()):
            sts: List[float] = []
            target_lines = self.get_messages_by_list_id([can_id])
            sts = self.get_timestamps_of_target_log_line(target_lines)
            for signal_name in signal_names:
                result[signal_name] = sts
        return result

    def get_timestamps_of_target_log_line(
        self,
        target_log_lines: List[CANLogLine]
        ) -> List[float]:
        return [line.timestamp for line in target_log_lines]

    def get_signal_values_by_ids(
        self, 
        can_ids: List[int],
        target_signal_names: List[str],
        cb: Callable = None
    ) -> Dict[str, List[Any]]:
        result = {name: [] for name in target_signal_names}
        for i, can_id in enumerate(can_ids):
            target_msg_lines = self.get_messages_by_list_id([can_id])
            for line in target_msg_lines:
                # if line.message_obj.cal_signal_value() or True:
                    signals = line.message_obj.signals
                    for sig_name, sig in signals.items(): 
                        if sig_name in target_signal_names:   
                            val = sig.value
                            result[sig_name].append(val)
        return result

    def get_messages_by_list_signal_raw_value(
        self,
        signal_search: Dict[SignalName, List[int]],
        can_ids: List[int] = None,
    ) -> List[CANLogLine]:
        if not can_ids:
            raise KeyError("Either can_ids or target_search_lines must be provided")
        target_search_lines = self.get_messages_by_list_id(can_ids)
        return self.get_signals_by_list_signal_raw_value(signal_search, target_search_lines)
    
    def get_signals_by_list_signal_raw_value(
            self,
            signal_search: Dict[SignalName, List[int]],
            target_search_lines: List[CANLogLine]
            ):
        result = []
        signal_search: Dict[SignalName, List[int]] = {}
        
        for entry in target_search_lines:
            # if entry.message_obj.cal_signal_value() or True:
                for signal_name in entry.message_obj.signals:
                    if signal_name in signal_search:
                        if entry.message_obj.signals[signal_name].raw_value is None:
                            result.append(entry)
                        elif entry.message_obj.signals[signal_name].raw_value in signal_search[signal_name]:
                            result.append(entry)
                            break
        return result

    """
    This method shall return a list of references to the result CANLogLine
    """
    def get_messages_by_list_id(
        self, 
        can_ids: List[int], 
        target_search_lines: List[CANLogLine] = None,
        ) -> List["CANLogLine"]:
        if target_search_lines:
            return [entry for entry in target_search_lines if entry.can_id in can_ids]
        else:
            return [entry for _, entry in self.log_entries.items() if entry.can_id in can_ids]

    def get_dict_messages_by_list_id(
        self,
        can_ids: List[int],
        target_search_lines: List[CANLogLine] | None = None,
    ) -> Dict[int, List[CANLogLine]]:

        result: Dict[int, List[CANLogLine]] = defaultdict(list)

        source = target_search_lines if target_search_lines is not None \
                else self.log_entries.values()

        for entry in source:
            if entry.can_id in can_ids:
                result[entry.can_id].append(entry)

        return dict(result)

    def group_messages_by_can_id(
        self,
        target_search_lines: List[CANLogLine],
    ) -> Dict[int, List[CANLogLine]]:

        grouped: Dict[int, List[CANLogLine]] = defaultdict(list)

        for entry in target_search_lines:
            grouped[entry.can_id].append(entry)

        return dict(grouped)


    def filter_messages_by_list_id(self, can_ids: List[int]) -> List[CANLogLine]:
        return [entry for line, entry in self.log_entries.items() if entry.can_id not in can_ids]

    def get_messages_change_by_list_id(self, can_ids: List[int]) -> List[CANLogLine]:
        return [entry for line, entry in self.log_entries.items() if (entry.can_id in can_ids) and (entry.changed)]

    def get_messages_by_direction(self, direction: str, search_region: List[CANLogLine] = None):
        return [entry for entry in search_region if entry.direction.lower() == direction.lower()]
    
    def get_messages_by_channel(self, channel: str, search_region: List[CANLogLine] = None):
        if search_region:
            return [entry for entry in search_region if  entry.channel == channel]
        else:
            return [entry for _, entry in self.log_entries.items() if entry.channel == channel]
    
    def get_messages_by_timestamp_range(
        self,
        from_t: float, 
        to_t: float, 
        search_region: List[CANLogLine] = None
        ) -> List[CANLogLine]:
        if not search_region:
            search_region = list(self.log_entries.values())
        return [entry for entry in search_region if entry.timestamp >= from_t and entry.timestamp <= to_t]
    
    def get_can_ids(self, search_region: List[CANLogLine]) -> Set[int]:
        if not search_region:
            return set()
        return {entry.can_id for entry in search_region}



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


# class DataLogState(Enum):
#     UNAVAILABLE = 0
#     AVAILABLE = 3

@dataclass
class CANLogRawDiskFile:
    data_mmap_path: str
    index_mmap_path: str
    channel_index_mmap_path: str = field(default="")
    direction_index_mmap_path: str = field(default="")

    total_lines: int = field(default=0)
    verified_size: int = field(default=0)
    mmap_file_count: int = field(default=0)
    mmap_capacity: int = field(default=1_000_000)
    # state: DataLogState = DataLogState.UNAVAILABLE
    # is_loading: bool = False
    #file_path: str
    can_ids: List[int] = field(default_factory=list)
    channels: List[str] = field(default_factory=list)

    _ENTRY_SIZE: int = 107
    _DATA_HEADER_SIZE: int = 32
    _ENTRY_STRUCT: Any = field(default=struct.Struct("<IddIBBB64s16s"), init=False, repr=False)
    _INDEX_HEADER_SIZE: int = 40
    _INDEX_HDR_STRUCT: Any = field(default=struct.Struct("<IIIIIIIII4x"), init=False, repr=False)
    _INDEX_FILTER_STRUCT: Any = field(default=struct.Struct("<IQQQII"), init=False, repr=False)
    _CHANNEL_INDEX_HEADER_SIZE: int = 32
    _CHANNEL_INDEX_HDR_STRUCT: Any = field(default=struct.Struct("<IIIII12x"), init=False, repr=False)
    _CHANNEL_FILTER_STRUCT: Any = field(default=struct.Struct("<B15sQII"), init=False, repr=False)
    _DIRECTION_INDEX_HEADER_SIZE: int = 32
    _DIRECTION_INDEX_HDR_STRUCT: Any = field(default=struct.Struct("<IIIII12x"), init=False, repr=False)
    _DIRECTION_FILTER_STRUCT: Any = field(default=struct.Struct("<B7xQII"), init=False, repr=False)
    _multi_can_merge_state: Dict[Tuple[bool, Tuple[int, ...]], Dict[str, Any]] = field(default_factory=dict, init=False, repr=False)

    # Lightweight catalog: can_id → list of per-segment descriptors.
    # Each descriptor = (seg_path, row_pool_base, row_pool_off, count,
    #                     changed_pool_base, changed_pool_off, changed_count)
    # Only filter metadata is read — NO row data loaded into RAM.
    _can_id_catalog: Dict[int, List[tuple]] = field(default_factory=dict, init=False, repr=False)
    _can_id_timestamp_bounds: Dict[int, Tuple[float, float]] = field(default_factory=dict, init=False, repr=False)
    _global_timestamp_bounds: Optional[Tuple[float, float]] = field(default=None, init=False, repr=False)
    _channel_catalog: Dict[str, List[tuple]] = field(default_factory=dict, init=False, repr=False)
    _direction_catalog: Dict[str, List[tuple]] = field(default_factory=dict, init=False, repr=False)
    _multi_channel_merge_state: Dict[Tuple[str, ...], Dict[str, Any]] = field(default_factory=dict, init=False, repr=False)
    _multi_direction_merge_state: Dict[Tuple[str, ...], Dict[str, Any]] = field(default_factory=dict, init=False, repr=False)

    # @property
    # def file_name(self) -> str:
    #     if not self.file_path:
    #         return ""
    #     return Path(self.file_path).name

    # ────────────────────────────────────────────────────────────────────
    #  Mmap path management
    # ────────────────────────────────────────────────────────────────────
    def data_segment_paths(self) -> List[Path]:
        return self._segment_paths(self.data_mmap_path, "data")

    def index_segment_paths(self) -> List[Path]:
        return self._segment_paths(self.index_mmap_path, "index")

    def channel_index_segment_paths(self) -> List[Path]:
        base_path = self.channel_index_mmap_path
        if not base_path and self.index_mmap_path:
            stem = self.index_mmap_path[:-5] if self.index_mmap_path.endswith(".mmap") else self.index_mmap_path
            base_path = stem + ".channel.mmap"
        return self._segment_paths(base_path, "channel-index") if base_path else []

    def direction_index_segment_paths(self) -> List[Path]:
        base_path = self.direction_index_mmap_path
        if not base_path and self.index_mmap_path:
            stem = self.index_mmap_path[:-5] if self.index_mmap_path.endswith(".mmap") else self.index_mmap_path
            base_path = stem + ".direction.mmap"
        return self._segment_paths(base_path, "direction-index") if base_path else []

    def _segment_paths(self, base_path: str, kind: str) -> List[Path]:
        base = Path(base_path)
        folder = base.parent
        stem = base.name[:-5] if base.name.endswith(".mmap") else base.name
        # Accept both base paths (e.g. *.data.mmap) and explicit numbered
        # segment paths (e.g. *.data.000.mmap) by stripping the numeric suffix.
        stem_parts = stem.rsplit(".", 1)
        if len(stem_parts) == 2 and stem_parts[1].isdigit() and len(stem_parts[1]) == 3:
            stem = stem_parts[0]
        return sorted(folder.glob(f"{stem}.[0-9][0-9][0-9].mmap"))
    
    # ────────────────────────────────────────────────────────────────────
    #  API for filter rows
    # ────────────────────────────────────────────────────────────────────
    def get_page_from_row_indices(self, first_line: int, page_size: int) -> List[CANLogLine]:
        start = max(0, int(first_line))
        end = start + max(0, int(page_size))
        return self.get_messages_by_row_indices(range(start, end))

    def get_page_from_can_id_row_indices(self, can_id: int, first_line: int, page_size: int) -> List[CANLogLine]:
        page_rows = self._read_row_page_from_mmap(can_id, first_line, page_size)
        return self.get_messages_by_row_indices(page_rows)

    def get_page_from_can_ids_row_indices(self, can_ids: List[int], first_line: int, page_size: int) -> List[CANLogLine]:
        merged = self._merge_can_ids_page_from_mmap(can_ids, first_line, page_size, changed=False)
        return self.get_messages_by_row_indices(merged)

    def get_page_from_can_id_changed_row_indices(self, can_id: int, first_line: int, page_size: int) -> List[CANLogLine]:
        page_rows = self._read_changed_row_page_from_mmap(can_id, first_line, page_size)
        return self.get_messages_by_row_indices(page_rows)

    def get_page_from_can_ids_changed_row_indices(self, can_ids: List[int], first_line: int, page_size: int) -> List[CANLogLine]:
        merged = self._merge_can_ids_page_from_mmap(can_ids, first_line, page_size, changed=True)
        return self.get_messages_by_row_indices(merged)

    def get_page_from_channel_row_indices(self, channel: str, first_line: int, page_size: int) -> List[CANLogLine]:
        page_rows = self._read_channel_row_page_from_mmap(channel, first_line, page_size)
        return self.get_messages_by_row_indices(page_rows)

    def get_page_from_channels_row_indices(self, channels: List[str], first_line: int, page_size: int) -> List[CANLogLine]:
        merged = self._merge_channels_page_from_mmap(channels, first_line, page_size)
        return self.get_messages_by_row_indices(merged)

    def get_page_from_direction_row_indices(self, direction: str, first_line: int, page_size: int) -> List[CANLogLine]:
        page_rows = self._read_direction_row_page_from_mmap(direction, first_line, page_size)
        return self.get_messages_by_row_indices(page_rows)

    def get_page_from_directions_row_indices(self, directions: List[str], first_line: int, page_size: int) -> List[CANLogLine]:
        merged = self._merge_directions_page_from_mmap(directions, first_line, page_size)
        return self.get_messages_by_row_indices(merged)

    def get_page_from_timestamp_range(self,from_t: float,to_t: float,first_line: int,page_size: int,) -> List[CANLogLine]:
        lo_t = float(from_t)
        hi_t = float(to_t)
        if lo_t > hi_t:
            lo_t, hi_t = hi_t, lo_t

        start_row = self.get_start_row_by_timestamp(lo_t)
        end_row = self.get_end_row_by_timestamp(hi_t)
        if end_row <= start_row:
            return []

        offset = max(0, int(first_line))
        size = max(0, int(page_size))
        if size == 0:
            return []

        window_total = end_row - start_row
        if offset >= window_total:
            return []

        global_first = start_row + offset
        take = min(size, window_total - offset)
        return self.get_page_from_row_indices(global_first, take)
    
    # ────────────────────────────────────────────────────────────────────
    #  API for row
    # ────────────────────────────────────────────────────────────────────
    def get_start_row_by_timestamp(self, timestamp: float) -> int:
        if self.total_lines <= 0:
            self.refresh_mmap_runtime()
        total = int(self.total_lines)
        if total <= 0:
            return 0

        segs = self.data_segment_paths()
        if not segs:
            return 0

        seg_cache: Dict[int, Tuple[Any, _mmap.mmap, int, Any]] = {}
        try:
            return self._timestamp_lower_bound_global(segs, total, float(timestamp), seg_cache)
        finally:
            for f, mm, _, _ in seg_cache.values():
                mm.close()
                f.close()

    def get_start_row_by_can_id_timestamp(self, can_id: int, timestamp: float) -> int:
        total = self.get_total_count_by_can_id(int(can_id))
        if total <= 0:
            return 0
        return self._timestamp_lower_bound_indexed(
            total_count=total,
            read_row_index_at_pos=lambda pos: self._read_row_index_at_pos_can_id(int(can_id), pos),
            target_ts=float(timestamp),
        )

    def get_start_row_by_channel_timestamp(self, channel: str, timestamp: float) -> int:
        total = self.get_total_count_by_channel(channel)
        if total <= 0:
            return 0
        return self._timestamp_lower_bound_indexed(
            total_count=total,
            read_row_index_at_pos=lambda pos: self._read_row_index_at_pos_channel(channel, pos),
            target_ts=float(timestamp),
        )

    def get_start_row_by_direction_timestamp(self, direction: str, timestamp: float) -> int:
        total = self.get_total_count_by_direction(direction)
        if total <= 0:
            return 0
        return self._timestamp_lower_bound_indexed(
            total_count=total,
            read_row_index_at_pos=lambda pos: self._read_row_index_at_pos_direction(direction, pos),
            target_ts=float(timestamp),
        )

    def get_end_row_by_timestamp(self, timestamp: float) -> int:
        """Upper-bound end row (first row with timestamp > target) in global space."""
        if self.total_lines <= 0:
            self.refresh_mmap_runtime()
        total = int(self.total_lines)
        if total <= 0:
            return 0

        segs = self.data_segment_paths()
        if not segs:
            return 0

        seg_cache: Dict[int, Tuple[Any, _mmap.mmap, int, Any]] = {}
        try:
            return self._timestamp_upper_bound_global(segs, total, float(timestamp), seg_cache)
        finally:
            for f, mm, _, _ in seg_cache.values():
                mm.close()
                f.close()

    def get_end_row_by_can_id_timestamp(self, can_id: int, timestamp: float) -> int:
        """Upper-bound end row in CAN-ID filtered space."""
        total = self.get_total_count_by_can_id(int(can_id))
        if total <= 0:
            return 0
        return self._timestamp_upper_bound_indexed(
            total_count=total,
            read_row_index_at_pos=lambda pos: self._read_row_index_at_pos_can_id(int(can_id), pos),
            target_ts=float(timestamp),
        )

    def get_end_row_by_channel_timestamp(self, channel: str, timestamp: float) -> int:
        """Upper-bound end row in channel filtered space."""
        total = self.get_total_count_by_channel(channel)
        if total <= 0:
            return 0
        return self._timestamp_upper_bound_indexed(
            total_count=total,
            read_row_index_at_pos=lambda pos: self._read_row_index_at_pos_channel(channel, pos),
            target_ts=float(timestamp),
        )

    def get_end_row_by_direction_timestamp(self, direction: str, timestamp: float) -> int:
        """Upper-bound end row in direction filtered space."""
        total = self.get_total_count_by_direction(direction)
        if total <= 0:
            return 0
        return self._timestamp_upper_bound_indexed(
            total_count=total,
            read_row_index_at_pos=lambda pos: self._read_row_index_at_pos_direction(direction, pos),
            target_ts=float(timestamp),
        )

    def get_start_row_by_can_id_changed_timestamp(self, can_id: int, timestamp: float) -> int:
        """Lower-bound start row in CAN-ID changed-only filtered space."""
        total = self.get_changed_count_by_can_id(int(can_id))
        if total <= 0:
            return 0
        return self._timestamp_lower_bound_indexed(
            total_count=total,
            read_row_index_at_pos=lambda pos: self._read_changed_row_index_at_pos_can_id(int(can_id), pos),
            target_ts=float(timestamp),
        )

    def get_end_row_by_can_id_changed_timestamp(self, can_id: int, timestamp: float) -> int:
        """Upper-bound end row in CAN-ID changed-only filtered space."""
        total = self.get_changed_count_by_can_id(int(can_id))
        if total <= 0:
            return 0
        return self._timestamp_upper_bound_indexed(
            total_count=total,
            read_row_index_at_pos=lambda pos: self._read_changed_row_index_at_pos_can_id(int(can_id), pos),
            target_ts=float(timestamp),
        )
    
    # ────────────────────────────────────────────────────────────────────
    #  API for size
    # ────────────────────────────────────────────────────────────────────
    def get_total_count_by_can_id(self, can_id: int) -> int:
        """Total row count for one CAN-ID (all + unchanged + changed)."""
        self._ensure_can_id_catalog()
        segs = self._can_id_catalog.get(int(can_id), [])
        return sum(c for _, _, _, c, _, _, _ in segs)

    def get_changed_count_by_can_id(self, can_id: int) -> int:
        """Changed-row count for one CAN-ID."""
        self._ensure_can_id_catalog()
        segs = self._can_id_catalog.get(int(can_id), [])
        return sum(cc for _, _, _, _, _, _, cc in segs)

    def get_total_count_by_can_ids(self, can_ids: List[int]) -> int:
        """Total row count across multiple CAN-IDs (sum, not merged)."""
        self._ensure_can_id_catalog()
        total = 0
        seen: Set[int] = set()
        for cid_raw in can_ids:
            cid = int(cid_raw)
            if cid in seen:
                continue
            seen.add(cid)
            segs = self._can_id_catalog.get(cid, [])
            total += sum(c for _, _, _, c, _, _, _ in segs)
        return total

    def get_changed_count_by_can_ids(self, can_ids: List[int]) -> int:
        """Changed-row count across multiple CAN-IDs."""
        self._ensure_can_id_catalog()
        total = 0
        seen: Set[int] = set()
        for cid_raw in can_ids:
            cid = int(cid_raw)
            if cid in seen:
                continue
            seen.add(cid)
            segs = self._can_id_catalog.get(cid, [])
            total += sum(cc for _, _, _, _, _, _, cc in segs)
        return total

    def get_total_count_by_channel(self, channel: str) -> int:
        self._ensure_channel_catalog()
        segs = self._channel_catalog.get(str(channel).lower(), [])
        return sum(c for _, _, _, c, _ in segs)

    def get_total_count_by_channels(self, channels: List[str]) -> int:
        self._ensure_channel_catalog()
        total = 0
        seen: Set[str] = set()
        for channel in channels:
            key = str(channel).lower()
            if key in seen:
                continue
            seen.add(key)
            segs = self._channel_catalog.get(key, [])
            total += sum(c for _, _, _, c, _ in segs)
        return total

    def get_total_count_by_direction(self, direction: str) -> int:
        self._ensure_direction_catalog()
        segs = self._direction_catalog.get(self._normalize_direction_key(direction), [])
        return sum(c for _, _, _, c, _ in segs)

    def get_total_count_by_directions(self, directions: List[str]) -> int:
        self._ensure_direction_catalog()
        total = 0
        seen: Set[str] = set()
        for direction in directions:
            key = self._normalize_direction_key(direction)
            if key in seen:
                continue
            seen.add(key)
            segs = self._direction_catalog.get(key, [])
            total += sum(c for _, _, _, c, _ in segs)
        return total

    # ────────────────────────────────────────────────────────────────────
    #  API for timestamp
    # ────────────────────────────────────────────────────────────────────

    def get_first_last_timestamp(self) -> Tuple[Optional[float], Optional[float]]:
        if self._global_timestamp_bounds is not None:
            return self._global_timestamp_bounds

        if self.total_lines <= 0:
            self.refresh_mmap_runtime()
        if self.total_lines <= 0:
            return None, None

        segs = self.data_segment_paths()
        if not segs:
            return None, None

        first_entry = self._read_entry_by_global_row(segs, 0)
        last_entry = self._read_entry_by_global_row(segs, int(self.total_lines) - 1)
        if first_entry is None or last_entry is None:
            return None, None

        self._global_timestamp_bounds = (float(first_entry.timestamp), float(last_entry.timestamp))
        return self._global_timestamp_bounds

    def get_first_last_timestamp_by_can_id(self, can_id: int) -> Tuple[Optional[float], Optional[float]]:
        self._ensure_can_id_catalog()
        bounds = self._can_id_timestamp_bounds.get(int(can_id))
        if bounds is None:
            return None, None
        return float(bounds[0]), float(bounds[1])

    def get_first_last_timestamp_by_can_ids(self, can_ids: List[int]) -> Tuple[Optional[float], Optional[float]]:
        self._ensure_can_id_catalog()

        seen: Set[int] = set()
        first_ts: Optional[float] = None
        last_ts: Optional[float] = None
        for can_id in can_ids:
            cid = int(can_id)
            if cid in seen:
                continue
            seen.add(cid)
            bounds = self._can_id_timestamp_bounds.get(cid)
            if bounds is None:
                continue
            f, l = float(bounds[0]), float(bounds[1])
            first_ts = f if first_ts is None else min(first_ts, f)
            last_ts = l if last_ts is None else max(last_ts, l)

        return first_ts, last_ts

    def get_timestamps_by_can_id(self, can_id: int) -> List[float]:
        rows = self.get_row_indices_by_list_id([int(can_id)])
        if not rows:
            return []

        segs = self.data_segment_paths()
        if not segs:
            return []

        timestamps: List[float] = []
        seg_cache: Dict[int, Tuple[Any, _mmap.mmap, int, Any]] = {}
        try:
            for row in rows:
                ts = self._read_timestamp_by_global_row_cached(segs, int(row), seg_cache)
                if ts is not None:
                    timestamps.append(float(ts))
        finally:
            for f, mm, _, _ in seg_cache.values():
                mm.close()
                f.close()

        return timestamps

    def get_timestamp_by_row(self, row_index: int) -> Optional[float]:
        """Timestamp for a global row index (0-based)."""
        if self.total_lines <= 0:
            self.refresh_mmap_runtime()
        if self.total_lines <= 0:
            return None

        row = int(row_index)
        if row < 0 or row >= int(self.total_lines):
            return None

        segs = self.data_segment_paths()
        if not segs:
            return None

        entry = self._read_entry_by_global_row(segs, row)
        if entry is None:
            return None
        return float(entry.timestamp)

    def get_timestamp_by_can_id_row(
        self,
        can_id: int,
        row_index: int,
        changed: bool = False,
    ) -> Optional[float]:
        """Timestamp for a row index within one CAN-ID filtered space (0-based)."""
        row = int(row_index)
        if row < 0:
            return None

        if changed:
            rows = self._read_changed_row_page_from_mmap(int(can_id), row, 1)
        else:
            rows = self._read_row_page_from_mmap(int(can_id), row, 1)
        if not rows:
            return None

        return self.get_timestamp_by_row(int(rows[0]))

    def get_timestamp_by_can_ids_row(
        self,
        can_ids: List[int],
        row_index: int,
        changed: bool = False,
    ) -> Optional[float]:
        """Timestamp for a row index within merged CAN-IDs filtered space (0-based)."""
        row = int(row_index)
        if row < 0:
            return None

        rows = self._merge_can_ids_page_from_mmap(
            can_ids=can_ids,
            first_line=row,
            page_size=1,
            changed=changed,
        )
        if not rows:
            return None

        return self.get_timestamp_by_row(int(rows[0]))

    def get_timestamp_by_channel_row(self, channel: str, row_index: int) -> Optional[float]:
        row = int(row_index)
        if row < 0:
            return None

        rows = self._read_channel_row_page_from_mmap(channel, row, 1)
        if not rows:
            return None
        return self.get_timestamp_by_row(int(rows[0]))

    ############################# Internal #################################    
    def _read_timestamp_by_global_row_cached(
        self,
        segs: List[Path],
        global_row: int,
        seg_cache: Dict[int, Tuple[Any, _mmap.mmap, int, Any]],
    ) -> Optional[float]:
        row = int(global_row)
        if row < 0:
            return None
        seg_idx = row // self.mmap_capacity
        local_idx = row % self.mmap_capacity
        if seg_idx < 0 or seg_idx >= len(segs):
            return None

        if seg_idx not in seg_cache:
            f = open(segs[seg_idx], "rb")
            mm = _mmap.mmap(f.fileno(), 0, access=_mmap.ACCESS_READ)
            entry_size, entry_struct = self._get_data_entry_layout(segs[seg_idx])
            seg_cache[seg_idx] = (f, mm, entry_size, entry_struct)

        _, mm, entry_size, entry_struct = seg_cache[seg_idx]
        offset = self._DATA_HEADER_SIZE + local_idx * entry_size
        if offset + entry_size > len(mm):
            return None

        _, timestamp, _, _, _, _, _, _, _ = entry_struct.unpack_from(mm, offset)
        return float(timestamp)

    def _timestamp_lower_bound_global(
        self,
        segs: List[Path],
        total: int,
        target_ts: float,
        seg_cache: Dict[int, Tuple[Any, _mmap.mmap, int, Any]],
    ) -> int:
        lo, hi = 0, int(total)
        while lo < hi:
            mid = (lo + hi) // 2
            ts = self._read_timestamp_by_global_row_cached(segs, mid, seg_cache)
            if ts is None or ts < target_ts:
                lo = mid + 1
            else:
                hi = mid
        return lo

    def _timestamp_upper_bound_global(
        self,
        segs: List[Path],
        total: int,
        target_ts: float,
        seg_cache: Dict[int, Tuple[Any, _mmap.mmap, int, Any]],
    ) -> int:
        lo, hi = 0, int(total)
        while lo < hi:
            mid = (lo + hi) // 2
            ts = self._read_timestamp_by_global_row_cached(segs, mid, seg_cache)
            if ts is None or ts <= target_ts:
                lo = mid + 1
            else:
                hi = mid
        return lo

    def _read_row_index_at_pos_can_id(self, can_id: int, pos: int) -> Optional[int]:
        rows = self._read_row_page_from_mmap(int(can_id), int(pos), 1)
        return int(rows[0]) if rows else None

    def _read_row_index_at_pos_channel(self, channel: str, pos: int) -> Optional[int]:
        rows = self._read_channel_row_page_from_mmap(channel, int(pos), 1)
        return int(rows[0]) if rows else None

    def _read_row_index_at_pos_direction(self, direction: str, pos: int) -> Optional[int]:
        rows = self._read_direction_row_page_from_mmap(direction, int(pos), 1)
        return int(rows[0]) if rows else None

    def _read_changed_row_index_at_pos_can_id(self, can_id: int, pos: int) -> Optional[int]:
        rows = self._read_changed_row_page_from_mmap(int(can_id), int(pos), 1)
        return int(rows[0]) if rows else None

    def _timestamp_lower_bound_indexed(
        self,
        total_count: int,
        read_row_index_at_pos: Callable[[int], Optional[int]],
        target_ts: float,
    ) -> int:
        total = int(total_count)
        if total <= 0:
            return 0

        segs = self.data_segment_paths()
        if not segs:
            return 0

        seg_cache: Dict[int, Tuple[Any, _mmap.mmap, int, Any]] = {}

        def ts_by_pos(pos: int) -> float:
            row = read_row_index_at_pos(pos)
            if row is None:
                return float("inf")
            ts = self._read_timestamp_by_global_row_cached(segs, row, seg_cache)
            return float("inf") if ts is None else float(ts)

        try:
            lo, hi = 0, total
            while lo < hi:
                mid = (lo + hi) // 2
                if ts_by_pos(mid) < float(target_ts):
                    lo = mid + 1
                else:
                    hi = mid
            return lo
        finally:
            for f, mm, _, _ in seg_cache.values():
                mm.close()
                f.close()

    def _timestamp_upper_bound_indexed(
        self,
        total_count: int,
        read_row_index_at_pos: Callable[[int], Optional[int]],
        target_ts: float,
    ) -> int:
        total = int(total_count)
        if total <= 0:
            return 0

        segs = self.data_segment_paths()
        if not segs:
            return 0

        seg_cache: Dict[int, Tuple[Any, _mmap.mmap, int, Any]] = {}

        def ts_by_pos(pos: int) -> float:
            row = read_row_index_at_pos(pos)
            if row is None:
                return float("inf")
            ts = self._read_timestamp_by_global_row_cached(segs, row, seg_cache)
            return float("inf") if ts is None else float(ts)

        try:
            lo, hi = 0, total
            while lo < hi:
                mid = (lo + hi) // 2
                if ts_by_pos(mid) <= float(target_ts):
                    lo = mid + 1
                else:
                    hi = mid
            return lo
        finally:
            for f, mm, _, _ in seg_cache.values():
                mm.close()
                f.close()

    # ────────────────────────────────────────────────────────────────────
    #  Lightweight catalog — reads only the small filter entries (36 bytes
    #  per CAN-ID per segment). NO row data is loaded into RAM.
    # ────────────────────────────────────────────────────────────────────
    def _ensure_can_id_catalog(self):
        """Populate *_can_id_catalog* from the index segment headers.

        Each entry is a list of per-segment descriptors:
            (seg_path, row_pool_base, row_pool_off, count,
             changed_pool_base, changed_pool_off, changed_count)
        """
        if self._can_id_catalog:
            return

        catalog: Dict[int, List[tuple]] = defaultdict(list)
        bounds: Dict[int, Tuple[float, float]] = {}
        for seg_path in self.index_segment_paths():
            with open(seg_path, "rb") as f:
                mm = _mmap.mmap(f.fileno(), 0, access=_mmap.ACCESS_READ)
                try:
                    if len(mm) < self._INDEX_HEADER_SIZE:
                        continue
                    (
                        can_id_count, _, _, _,
                        max_can_ids,
                        max_row_pool_size,
                        max_changed_row_pool_size,
                        max_ts_pool_size, _,
                    ) = self._INDEX_HDR_STRUCT.unpack_from(mm, 0)

                    filter_base = self._INDEX_HEADER_SIZE
                    row_pool_base = filter_base + max_can_ids * self._INDEX_FILTER_STRUCT.size
                    changed_pool_base = row_pool_base + max_row_pool_size * 4
                    ts_pool_base = changed_pool_base + max_changed_row_pool_size * 4

                    for i in range(can_id_count):
                        off = filter_base + i * self._INDEX_FILTER_STRUCT.size
                        if off + self._INDEX_FILTER_STRUCT.size > len(mm):
                            break
                        cid, rp_off, crp_off, tp_off, count, changed_count = \
                            self._INDEX_FILTER_STRUCT.unpack_from(mm, off)
                        if count == 0 and changed_count == 0:
                            continue
                        catalog[int(cid)].append((
                            seg_path,
                            row_pool_base, int(rp_off), int(count),
                            changed_pool_base, int(crp_off), int(changed_count),
                        ))

                        if int(count) > 0:
                            first_addr = ts_pool_base + int(tp_off) * 8
                            last_addr = ts_pool_base + (int(tp_off) + int(count) - 1) * 8
                            if first_addr + 8 <= len(mm) and last_addr + 8 <= len(mm):
                                first_ts = float(struct.unpack_from("<d", mm, first_addr)[0])
                                last_ts = float(struct.unpack_from("<d", mm, last_addr)[0])
                                cid_i = int(cid)
                                if cid_i not in bounds:
                                    bounds[cid_i] = (first_ts, last_ts)
                                else:
                                    cur_first, _ = bounds[cid_i]
                                    bounds[cid_i] = (cur_first, last_ts)
                finally:
                    mm.close()

        self._can_id_catalog = dict(catalog)
        self._can_id_timestamp_bounds = bounds
        self.can_ids = list(self._can_id_catalog.keys())

    def _ensure_channel_catalog(self):
        if self._channel_catalog:
            return

        catalog: Dict[str, List[tuple]] = defaultdict(list)
        for seg_path in self.channel_index_segment_paths():
            with open(seg_path, "rb") as f:
                mm = _mmap.mmap(f.fileno(), 0, access=_mmap.ACCESS_READ)
                try:
                    if len(mm) < self._CHANNEL_INDEX_HEADER_SIZE:
                        continue
                    (
                        channel_count,
                        _,
                        max_channels,
                        max_row_pool_size,
                        _,
                    ) = self._CHANNEL_INDEX_HDR_STRUCT.unpack_from(mm, 0)

                    filter_base = self._CHANNEL_INDEX_HEADER_SIZE
                    row_pool_base = filter_base + max_channels * self._CHANNEL_FILTER_STRUCT.size

                    for i in range(channel_count):
                        off = filter_base + i * self._CHANNEL_FILTER_STRUCT.size
                        if off + self._CHANNEL_FILTER_STRUCT.size > len(mm):
                            break
                        channel_index, channel_raw, row_off, count, _ = self._CHANNEL_FILTER_STRUCT.unpack_from(mm, off)
                        if count == 0:
                            continue
                        channel = channel_raw.split(b"\x00", 1)[0].decode("ascii", errors="ignore").strip().lower()
                        if not channel:
                            channel = "unknown"
                        if int(row_off) + int(count) > int(max_row_pool_size):
                            continue
                        catalog[channel].append((
                            seg_path,
                            row_pool_base,
                            int(row_off),
                            int(count),
                            int(channel_index),
                        ))
                finally:
                    mm.close()

        self._channel_catalog = dict(catalog)
        self.channels = list(self._channel_catalog.keys())

    def _normalize_direction_key(self, direction: str) -> str:
        d = str(direction).strip().lower()
        if d in {"tx", "1"}:
            return "tx"
        return "rx"

    def _ensure_direction_catalog(self):
        if self._direction_catalog:
            return

        catalog: Dict[str, List[tuple]] = defaultdict(list)
        for seg_path in self.direction_index_segment_paths():
            with open(seg_path, "rb") as f:
                mm = _mmap.mmap(f.fileno(), 0, access=_mmap.ACCESS_READ)
                try:
                    if len(mm) < self._DIRECTION_INDEX_HEADER_SIZE:
                        continue
                    (
                        direction_count,
                        _,
                        max_directions,
                        max_row_pool_size,
                        _,
                    ) = self._DIRECTION_INDEX_HDR_STRUCT.unpack_from(mm, 0)

                    filter_base = self._DIRECTION_INDEX_HEADER_SIZE
                    row_pool_base = filter_base + max_directions * self._DIRECTION_FILTER_STRUCT.size

                    for i in range(direction_count):
                        off = filter_base + i * self._DIRECTION_FILTER_STRUCT.size
                        if off + self._DIRECTION_FILTER_STRUCT.size > len(mm):
                            break
                        direction_raw, row_off, count, _ = self._DIRECTION_FILTER_STRUCT.unpack_from(mm, off)
                        if count == 0:
                            continue
                        if int(row_off) + int(count) > int(max_row_pool_size):
                            continue
                        direction_key = "tx" if int(direction_raw) == 1 else "rx"
                        catalog[direction_key].append((
                            seg_path,
                            row_pool_base,
                            int(row_off),
                            int(count),
                            int(direction_raw),
                        ))
                finally:
                    mm.close()

        self._direction_catalog = dict(catalog)

    def _read_direction_row_page_from_mmap(
        self,
        direction: str,
        first_line: int,
        page_size: int,
    ) -> List[int]:
        self._ensure_direction_catalog()
        segs = self._direction_catalog.get(self._normalize_direction_key(direction), [])
        if not segs:
            return []

        start = max(0, int(first_line))
        size = max(0, int(page_size))
        if size == 0:
            return []

        result: List[int] = []
        skipped = 0
        remaining = size

        for seg_path, row_pool_base, row_off, count, _ in segs:
            if remaining <= 0:
                break
            skip_in_seg = max(0, start - skipped)
            if skip_in_seg >= count:
                skipped += count
                continue

            read_start = skip_in_seg
            read_count = min(remaining, count - skip_in_seg)

            with open(seg_path, "rb") as f:
                mm = _mmap.mmap(f.fileno(), 0, access=_mmap.ACCESS_READ)
                try:
                    addr = row_pool_base + (row_off + read_start) * 4
                    if addr + read_count * 4 <= len(mm):
                        result.extend(struct.unpack_from(f"<{read_count}I", mm, addr))
                finally:
                    mm.close()

            remaining -= read_count
            skipped += count

        return result

    def _read_channel_row_page_from_mmap(
        self,
        channel: str,
        first_line: int,
        page_size: int,
    ) -> List[int]:
        self._ensure_channel_catalog()
        segs = self._channel_catalog.get(str(channel).lower(), [])
        if not segs:
            return []

        start = max(0, int(first_line))
        size = max(0, int(page_size))
        if size == 0:
            return []

        result: List[int] = []
        skipped = 0
        remaining = size

        for seg_path, row_pool_base, row_off, count, _ in segs:
            if remaining <= 0:
                break
            skip_in_seg = max(0, start - skipped)
            if skip_in_seg >= count:
                skipped += count
                continue

            read_start = skip_in_seg
            read_count = min(remaining, count - skip_in_seg)

            with open(seg_path, "rb") as f:
                mm = _mmap.mmap(f.fileno(), 0, access=_mmap.ACCESS_READ)
                try:
                    addr = row_pool_base + (row_off + read_start) * 4
                    if addr + read_count * 4 <= len(mm):
                        result.extend(struct.unpack_from(f"<{read_count}I", mm, addr))
                finally:
                    mm.close()

            remaining -= read_count
            skipped += count

        return result

    # ────────────────────────────────────────────────────────────────────
    #  Direct-from-mmap page reads — ZERO RAM caching of row indices.
    #  Only the requested page_size uint32 values are read.
    # ────────────────────────────────────────────────────────────────────
    def _read_row_page_from_mmap(
        self, can_id: int, first_line: int, page_size: int,
    ) -> List[int]:
        """Read a page of row indices for *one* CAN-ID straight from mmap."""
        self._ensure_can_id_catalog()
        segs = self._can_id_catalog.get(int(can_id), [])
        if not segs:
            return []

        start = max(0, int(first_line))
        size = max(0, int(page_size))
        if size == 0:
            return []

        result: List[int] = []
        skipped = 0
        remaining = size

        for seg_path, row_pool_base, rp_off, count, *_ in segs:
            if remaining <= 0:
                break
            skip_in_seg = max(0, start - skipped)
            if skip_in_seg >= count:
                skipped += count
                continue

            read_start = skip_in_seg
            read_count = min(remaining, count - skip_in_seg)

            with open(seg_path, "rb") as f:
                mm = _mmap.mmap(f.fileno(), 0, access=_mmap.ACCESS_READ)
                try:
                    addr = row_pool_base + (rp_off + read_start) * 4
                    if addr + read_count * 4 <= len(mm):
                        result.extend(struct.unpack_from(f"<{read_count}I", mm, addr))
                finally:
                    mm.close()

            remaining -= read_count
            skipped += count

        return result

    def _read_changed_row_page_from_mmap(
        self, can_id: int, first_line: int, page_size: int,
    ) -> List[int]:
        """Read a page of *changed* row indices for one CAN-ID from mmap."""
        self._ensure_can_id_catalog()
        segs = self._can_id_catalog.get(int(can_id), [])
        if not segs:
            return []

        start = max(0, int(first_line))
        size = max(0, int(page_size))
        if size == 0:
            return []

        result: List[int] = []
        skipped = 0
        remaining = size

        for seg_path, _, _, _, changed_pool_base, crp_off, changed_count in segs:
            if remaining <= 0:
                break
            if changed_count == 0:
                continue
            skip_in_seg = max(0, start - skipped)
            if skip_in_seg >= changed_count:
                skipped += changed_count
                continue

            read_start = skip_in_seg
            read_count = min(remaining, changed_count - skip_in_seg)

            with open(seg_path, "rb") as f:
                mm = _mmap.mmap(f.fileno(), 0, access=_mmap.ACCESS_READ)
                try:
                    addr = changed_pool_base + (crp_off + read_start) * 4
                    if addr + read_count * 4 <= len(mm):
                        result.extend(struct.unpack_from(f"<{read_count}I", mm, addr))
                finally:
                    mm.close()

            remaining -= read_count
            skipped += changed_count

        return result

    def _merge_channels_page_from_mmap(
        self,
        channels: List[str],
        first_line: int,
        page_size: int,
    ) -> List[int]:
        self._ensure_channel_catalog()

        start = max(0, int(first_line))
        size = max(0, int(page_size))
        if size == 0:
            return []

        unique_channels: List[str] = []
        seen: Set[str] = set()
        for channel in channels:
            key = str(channel).lower()
            if key not in seen:
                seen.add(key)
                unique_channels.append(key)

        state_key: Tuple[str, ...] = tuple(unique_channels)

        def _build_sources(keys: List[str]) -> Tuple[List[List[tuple]], List[int]]:
            ch_segs_local: List[List[tuple]] = []
            ch_totals_local: List[int] = []
            for key in keys:
                cat = self._channel_catalog.get(key, [])
                if not cat:
                    ch_segs_local.append([])
                    ch_totals_local.append(0)
                    continue
                seg_list = [(sp, rpb, ro, c) for sp, rpb, ro, c, _ in cat if c > 0]
                ch_segs_local.append(seg_list)
                ch_totals_local.append(sum(c for _, _, _, c in seg_list))
            return ch_segs_local, ch_totals_local

        state = self._multi_channel_merge_state.get(state_key)
        if not state or int(state.get("next_first_line", 0)) != start:
            ch_segs, ch_totals = _build_sources(unique_channels)
            heap_q: List[Tuple[int, int, int]] = []
            state = {
                "unique_channels": unique_channels,
                "ch_segs": ch_segs,
                "ch_totals": ch_totals,
                "heap": heap_q,
                "next_first_line": 0,
            }
        else:
            ch_segs = state["ch_segs"]
            ch_totals = state["ch_totals"]
            heap_q = state["heap"]

        mmap_cache: Dict[Path, Tuple[Any, _mmap.mmap]] = {}

        def _open_mm(seg_path: Path) -> _mmap.mmap:
            if seg_path not in mmap_cache:
                fh = open(seg_path, "rb")
                mm = _mmap.mmap(fh.fileno(), 0, access=_mmap.ACCESS_READ)
                mmap_cache[seg_path] = (fh, mm)
            return mmap_cache[seg_path][1]

        def _read_at(ci: int, pos: int) -> int:
            offset = 0
            for seg_path, pool_base, pool_off, count in ch_segs[ci]:
                if pos < offset + count:
                    local = pos - offset
                    mm = _open_mm(seg_path)
                    addr = pool_base + (pool_off + local) * 4
                    return struct.unpack_from("<I", mm, addr)[0]
                offset += count
            raise IndexError(pos)

        def _pop_next() -> Optional[Tuple[int, int, int]]:
            if not heap_q:
                return None
            row_val, ci, cursor = heapq.heappop(heap_q)
            nxt = cursor + 1
            if nxt < ch_totals[ci]:
                heapq.heappush(heap_q, (_read_at(ci, nxt), ci, nxt))
            return row_val, ci, cursor

        try:
            if not heap_q and int(state.get("next_first_line", 0)) == 0:
                for ci in range(len(unique_channels)):
                    if ch_totals[ci] > 0:
                        heapq.heappush(heap_q, (_read_at(ci, 0), ci, 0))

            current_offset = int(state.get("next_first_line", 0))
            while current_offset < start and heap_q:
                popped = _pop_next()
                if popped is None:
                    break
                current_offset += 1

            merged: List[int] = []
            produced = 0
            while produced < size and heap_q:
                popped = _pop_next()
                if popped is None:
                    break
                row_val, _, _ = popped
                merged.append(row_val)
                produced += 1
                current_offset += 1

            state["heap"] = heap_q
            state["next_first_line"] = current_offset
            self._multi_channel_merge_state[state_key] = state
            return merged
        finally:
            for fh, mm in mmap_cache.values():
                mm.close()
                fh.close()

    def _merge_directions_page_from_mmap(
        self,
        directions: List[str],
        first_line: int,
        page_size: int,
    ) -> List[int]:
        self._ensure_direction_catalog()

        start = max(0, int(first_line))
        size = max(0, int(page_size))
        if size == 0:
            return []

        unique_directions: List[str] = []
        seen: Set[str] = set()
        for direction in directions:
            key = self._normalize_direction_key(direction)
            if key not in seen:
                seen.add(key)
                unique_directions.append(key)

        state_key: Tuple[str, ...] = tuple(unique_directions)

        def _build_sources(keys: List[str]) -> Tuple[List[List[tuple]], List[int]]:
            dir_segs_local: List[List[tuple]] = []
            dir_totals_local: List[int] = []
            for key in keys:
                cat = self._direction_catalog.get(key, [])
                if not cat:
                    dir_segs_local.append([])
                    dir_totals_local.append(0)
                    continue
                seg_list = [(sp, rpb, ro, c) for sp, rpb, ro, c, _ in cat if c > 0]
                dir_segs_local.append(seg_list)
                dir_totals_local.append(sum(c for _, _, _, c in seg_list))
            return dir_segs_local, dir_totals_local

        state = self._multi_direction_merge_state.get(state_key)
        if not state or int(state.get("next_first_line", 0)) != start:
            dir_segs, dir_totals = _build_sources(unique_directions)
            heap_q: List[Tuple[int, int, int]] = []
            state = {
                "unique_directions": unique_directions,
                "dir_segs": dir_segs,
                "dir_totals": dir_totals,
                "heap": heap_q,
                "next_first_line": 0,
            }
        else:
            dir_segs = state["dir_segs"]
            dir_totals = state["dir_totals"]
            heap_q = state["heap"]

        mmap_cache: Dict[Path, Tuple[Any, _mmap.mmap]] = {}

        def _open_mm(seg_path: Path) -> _mmap.mmap:
            if seg_path not in mmap_cache:
                fh = open(seg_path, "rb")
                mm = _mmap.mmap(fh.fileno(), 0, access=_mmap.ACCESS_READ)
                mmap_cache[seg_path] = (fh, mm)
            return mmap_cache[seg_path][1]

        def _read_at(di: int, pos: int) -> int:
            offset = 0
            for seg_path, pool_base, pool_off, count in dir_segs[di]:
                if pos < offset + count:
                    local = pos - offset
                    mm = _open_mm(seg_path)
                    addr = pool_base + (pool_off + local) * 4
                    return struct.unpack_from("<I", mm, addr)[0]
                offset += count
            raise IndexError(pos)

        def _pop_next() -> Optional[Tuple[int, int, int]]:
            if not heap_q:
                return None
            row_val, di, cursor = heapq.heappop(heap_q)
            nxt = cursor + 1
            if nxt < dir_totals[di]:
                heapq.heappush(heap_q, (_read_at(di, nxt), di, nxt))
            return row_val, di, cursor

        try:
            if not heap_q and int(state.get("next_first_line", 0)) == 0:
                for di in range(len(unique_directions)):
                    if dir_totals[di] > 0:
                        heapq.heappush(heap_q, (_read_at(di, 0), di, 0))

            current_offset = int(state.get("next_first_line", 0))
            while current_offset < start and heap_q:
                popped = _pop_next()
                if popped is None:
                    break
                current_offset += 1

            merged: List[int] = []
            produced = 0
            while produced < size and heap_q:
                popped = _pop_next()
                if popped is None:
                    break
                row_val, _, _ = popped
                merged.append(row_val)
                produced += 1
                current_offset += 1

            state["heap"] = heap_q
            state["next_first_line"] = current_offset
            self._multi_direction_merge_state[state_key] = state
            return merged
        finally:
            for fh, mm in mmap_cache.values():
                mm.close()
                fh.close()

    def _merge_can_ids_page_from_mmap(
        self,
        can_ids: List[int],
        first_line: int,
        page_size: int,
        changed: bool = False,
    ) -> List[int]:
        """Cursor-based heap merge for multiple CAN IDs.

        Sequential requests (first_line grows by previous page size) continue from
        stored heap/cursor state and run in O(page_size * log N).
        """
        self._ensure_can_id_catalog()

        start = max(0, int(first_line))
        size = max(0, int(page_size))
        if size == 0:
            return []

        # De-duplicate CAN IDs while preserving order
        unique_cids: List[int] = []
        seen: Set[int] = set()
        for cid_raw in can_ids:
            cid = int(cid_raw)
            if cid not in seen:
                seen.add(cid)
                unique_cids.append(cid)

        state_key: Tuple[bool, Tuple[int, ...]] = (bool(changed), tuple(unique_cids))

        def _build_sources(cids: List[int]) -> Tuple[List[List[tuple]], List[int]]:
            cid_segs_local: List[List[tuple]] = []
            cid_totals_local: List[int] = []
            for cid in cids:
                cat = self._can_id_catalog.get(cid, [])
                if not cat:
                    cid_segs_local.append([])
                    cid_totals_local.append(0)
                    continue
                if changed:
                    seg_list = [(sp, cpb, cro, cc) for sp, _, _, _, cpb, cro, cc in cat if cc > 0]
                else:
                    seg_list = [(sp, rpb, ro, c) for sp, rpb, ro, c, _, _, _ in cat if c > 0]
                cid_segs_local.append(seg_list)
                cid_totals_local.append(sum(c for _, _, _, c in seg_list))
            return cid_segs_local, cid_totals_local

        state = self._multi_can_merge_state.get(state_key)
        if not state or int(state.get("next_first_line", 0)) != start:
            cid_segs, cid_totals = _build_sources(unique_cids)
            heap_q: List[Tuple[int, int, int]] = []
            # Fresh state starts at virtual merged offset 0.
            state = {
                "unique_cids": unique_cids,
                "cid_segs": cid_segs,
                "cid_totals": cid_totals,
                "heap": heap_q,
                "next_first_line": 0,
            }
        else:
            cid_segs = state["cid_segs"]
            cid_totals = state["cid_totals"]
            heap_q = state["heap"]

        # Open mmaps lazily, close at end
        mmap_cache: Dict[Path, Tuple[Any, _mmap.mmap]] = {}

        def _open_mm(seg_path: Path) -> _mmap.mmap:
            if seg_path not in mmap_cache:
                fh = open(seg_path, "rb")
                mm = _mmap.mmap(fh.fileno(), 0, access=_mmap.ACCESS_READ)
                mmap_cache[seg_path] = (fh, mm)
            return mmap_cache[seg_path][1]

        def _read_at(ci: int, pos: int) -> int:
            """Read the uint32 row index at virtual position *pos* for CAN-ID #ci."""
            offset = 0
            for seg_path, pool_base, pool_off, count in cid_segs[ci]:
                if pos < offset + count:
                    local = pos - offset
                    mm = _open_mm(seg_path)
                    addr = pool_base + (pool_off + local) * 4
                    return struct.unpack_from("<I", mm, addr)[0]
                offset += count
            raise IndexError(pos)

        def _pop_next() -> Optional[Tuple[int, int, int]]:
            if not heap_q:
                return None
            row_val, ci, cursor = heapq.heappop(heap_q)
            nxt = cursor + 1
            if nxt < cid_totals[ci]:
                heapq.heappush(heap_q, (_read_at(ci, nxt), ci, nxt))
            return row_val, ci, cursor

        try:
            # Seed only when state is fresh
            if not heap_q and int(state.get("next_first_line", 0)) == 0:
                for ci in range(len(unique_cids)):
                    if cid_totals[ci] > 0:
                        heapq.heappush(heap_q, (_read_at(ci, 0), ci, 0))

            # Advance cursor to requested start if needed
            current_offset = int(state.get("next_first_line", 0))
            while current_offset < start and heap_q:
                popped = _pop_next()
                if popped is None:
                    break
                current_offset += 1

            merged: List[int] = []
            produced = 0
            while produced < size and heap_q:
                popped = _pop_next()
                if popped is None:
                    break
                row_val, _, _ = popped
                merged.append(row_val)
                produced += 1
                current_offset += 1

            state["heap"] = heap_q
            state["next_first_line"] = current_offset
            self._multi_can_merge_state[state_key] = state

            return merged
        finally:
            for fh, mm in mmap_cache.values():
                mm.close()
                fh.close()

    def refresh_can_ids_runtime(self):
        # Clear lightweight catalog so it re-scans on next demand
        self._can_id_catalog.clear()
        self._can_id_timestamp_bounds.clear()
        self._global_timestamp_bounds = None
        self._channel_catalog.clear()
        self._direction_catalog.clear()
        self.channels = []
        # Clear cursor states for multi-CAN pagination
        self._multi_can_merge_state.clear()
        self._multi_channel_merge_state.clear()
        self._multi_direction_merge_state.clear()
        # Rebuild catalog (cheap — only filter metadata, no row data)
        self._ensure_can_id_catalog()
        self._ensure_channel_catalog()
        self._ensure_direction_catalog()

    def _get_data_entry_layout(self, seg_path: Path) -> Tuple[int, Any]:
        return self._ENTRY_SIZE, self._ENTRY_STRUCT

    def _read_entry_by_global_row(
        self,
        segs: List[Path],
        global_row: int,
        seg_cache: Optional[Dict[int, Tuple[Any, _mmap.mmap, int, Any]]] = None,
    ) -> Optional[CANLogLine]:
        seg_idx = int(global_row) // self.mmap_capacity
        local_idx = int(global_row) % self.mmap_capacity
        if seg_idx < 0 or seg_idx >= len(segs):
            return None

        if seg_cache is None:
            return self._read_entry_from_segment(segs[seg_idx], local_idx)

        if seg_idx not in seg_cache:
            f = open(segs[seg_idx], "rb")
            mm = _mmap.mmap(f.fileno(), 0, access=_mmap.ACCESS_READ)
            entry_size, entry_struct = self._get_data_entry_layout(segs[seg_idx])
            seg_cache[seg_idx] = (f, mm, entry_size, entry_struct)

        _, mm, entry_size, entry_struct = seg_cache[seg_idx]
        offset = self._DATA_HEADER_SIZE + local_idx * entry_size
        if offset + entry_size > len(mm):
            return None

        line_number, timestamp, last_timestamp, can_id, direction_raw, data_len, changed_raw, data_bytes, channel_raw = entry_struct.unpack_from(mm, offset)
        raw_data = " ".join(f"{b:02X}" for b in data_bytes[:data_len])
        channel = channel_raw.split(b"\x00", 1)[0].decode("ascii", errors="ignore")
        direction = "Tx" if direction_raw == 1 else "Rx"
        return CANLogLine(
            channel=channel,
            can_id=int(can_id),
            direction=direction,
            data_len=int(data_len),
            raw_data=raw_data,
            changed=bool(changed_raw),
            line_number=int(line_number),
            timestamp=float(timestamp),
            last_timestamp=float(last_timestamp)
        )

    """ O(row_indices) """
    def get_messages_by_row_indices(self, row_indices: List[int]) -> List[CANLogLine]:
        segs = self.data_segment_paths()
        if not segs:
            return []

        row_list = row_indices
        result: List[CANLogLine] = []
        seg_cache: Dict[int, Tuple[Any, _mmap.mmap, int, Any]] = {}
        try:
            for global_row in row_list:
                entry = self._read_entry_by_global_row(segs, int(global_row), seg_cache)
                if entry is not None:
                    result.append(entry)
        finally:
            for f, mm, _, _ in seg_cache.values():
                mm.close()
                f.close()
        return result


    def _read_segment_write_count(self, seg_path: Path) -> int:
        try:
            with open(seg_path, "rb") as f:
                hdr = f.read(8)
                if len(hdr) < 8:
                    return 0
                return int(struct.unpack("<Q", hdr)[0])
        except Exception:
            return 0

    def _read_segment_capacity(self, seg_path: Path) -> int:
        try:
            with open(seg_path, "rb") as f:
                f.seek(8)
                raw = f.read(4)
                if len(raw) < 4:
                    return self.mmap_capacity
                cap = int(struct.unpack("<I", raw)[0])
                return cap if cap > 0 else self.mmap_capacity
        except Exception:
            return self.mmap_capacity

    def refresh_mmap_runtime(self):
        segs = self.data_segment_paths()
        self.mmap_file_count = len(segs)
        if segs:
            self.mmap_capacity = self._read_segment_capacity(segs[0])
        self.total_lines = sum(self._read_segment_write_count(seg) for seg in segs)

    def mmap_file_total(self):
        return self.mmap_file_count

    @property
    def loaded_lines(self):
        return self.total_lines

    def _read_entry_from_segment(self, seg_path: Path, local_idx: int) -> Optional[CANLogLine]:
        entry_size, entry_struct = self._get_data_entry_layout(seg_path)
        offset = self._DATA_HEADER_SIZE + local_idx * entry_size
        try:
            with open(seg_path, "rb") as f:
                mm = _mmap.mmap(f.fileno(), 0, access=_mmap.ACCESS_READ)
                try:
                    if offset + entry_size > len(mm):
                        return None
                    line_number, timestamp, last_timestamp, can_id, direction_raw, data_len, changed_raw, data_bytes, channel_raw = entry_struct.unpack_from(mm, offset)
                finally:
                    mm.close()
        except Exception:
            return None

        raw_data = " ".join(f"{b:02X}" for b in data_bytes[:data_len])
        channel = channel_raw.split(b"\x00", 1)[0].decode("ascii", errors="ignore")
        direction = "Tx" if direction_raw == 1 else "Rx"

        line = CANLogLine(
            channel=channel,
            can_id=int(can_id),
            direction=direction,
            data_len=int(data_len),
            raw_data=raw_data,
            changed=bool(changed_raw),
            line_number=int(line_number),
            timestamp=float(timestamp),
            last_timestamp=float(last_timestamp),
            last_raw_data="",
        )

        line.cal_message_obj()
        #### If decode mmap exist -> create Signal object from rawvalue.mmap, value.mmap ####
        return line

    def get_page_lines(self, first_line: int, page_size: int) -> List[CANLogLine]:
        start = max(0, int(first_line))
        end = start + max(0, int(page_size))
        return self.get_messages_by_row_indices(range(start, end))

    def get_all_can_ids(self) -> List[int]:
        self._ensure_can_id_catalog()
        return self.can_ids

    def get_all_channels(self) -> List[str]:
        self._ensure_channel_catalog()
        return self.channels
    
    def get_all_lines(self) -> List[CANLogLine]:
        return self.get_page_lines(0, 20_000)

    def get_row_indices_by_list_id(self, can_ids: List[int]) -> List[int]:
        result: List[int] = []
        for can_id in can_ids:
            cid = int(can_id)
            total = self.get_total_count_by_can_id(cid)
            if total > 0:
                result.extend(self._read_row_page_from_mmap(cid, 0, total))
        return result

    def get_row_indices_by_channel(self, channel: str) -> List[int]:
        total = self.get_total_count_by_channel(channel)
        if total <= 0:
            return []
        return self._read_channel_row_page_from_mmap(channel, 0, total)

    def get_row_indices_by_direction(self, direction: str) -> List[int]:
        total = self.get_total_count_by_direction(direction)
        if total <= 0:
            return []
        return self._read_direction_row_page_from_mmap(direction, 0, total)

    def get_row_indices_by_directions(self, directions: List[str]) -> List[int]:
        total = self.get_total_count_by_directions(directions)
        if total <= 0:
            return []
        return self._merge_directions_page_from_mmap(directions, 0, total)

    def get_row_indices_by_channels(self, channels: List[str]) -> List[int]:
        total = self.get_total_count_by_channels(channels)
        if total <= 0:
            return []
        return self._merge_channels_page_from_mmap(channels, 0, total)

    def filter_row_indices_by_direction(self, direction: str, row_indices) -> List[int]:
        if row_indices is None:
            return self.get_row_indices_by_direction(direction)
        rows = list(row_indices)
        lines = self.get_messages_by_row_indices(rows)
        d = direction.lower()
        return [rows[i] for i, entry in enumerate(lines) if entry.direction.lower() == d]

    def filter_row_indices_by_channel(self, channel: str, row_indices) -> List[int]:
        rows = list(row_indices)
        lines = self.get_messages_by_row_indices(rows)
        return [rows[i] for i, entry in enumerate(lines) if entry.channel == channel]

    def filter_row_indices_by_timestamp_range(self, from_t: float, to_t: float, row_indices) -> List[int]:
        rows = list(row_indices)
        if not rows:
            return []

        lo_t = float(from_t)
        hi_t = float(to_t)
        if lo_t > hi_t:
            lo_t, hi_t = hi_t, lo_t

        segs = self.data_segment_paths()
        if not segs:
            return []

        seg_cache: Dict[int, Tuple[Any, _mmap.mmap, int, Any]] = {}

        def ts_at_pos(pos: int) -> float:
            ts = self._read_timestamp_by_global_row_cached(segs, int(rows[pos]), seg_cache)
            return float("inf") if ts is None else float(ts)

        try:
            lo, hi = 0, len(rows)
            while lo < hi:
                mid = (lo + hi) // 2
                if ts_at_pos(mid) < lo_t:
                    lo = mid + 1
                else:
                    hi = mid
            start = lo

            lo, hi = start, len(rows)
            while lo < hi:
                mid = (lo + hi) // 2
                if ts_at_pos(mid) <= hi_t:
                    lo = mid + 1
                else:
                    hi = mid
            end = lo

            return rows[start:end]
        finally:
            for f, mm, _, _ in seg_cache.values():
                mm.close()
                f.close()

# class DecodeLogState(Enum):
#     UNAVAILABLE = 0
#     AVAILABLE = 3

CANID = int
SigID = int
@dataclass
class CANLogDecodedDiskFile:
    #file_path: str
    decode_signal_dir_mmap_path: str = field(default="")
    decode_row_index_changed_mmap_path: str = field(default="")
    decode_row_index_mmap_path: str = field(default="")
    decode_value_mmap_path: str = field(default="")
    decode_rawvalue_mmap_path: str = field(default="")
    decode_verified_size: int = field(default=0)
    decode_mmap_file_count: int = field(default=0)
    decode_current_size: int = field(default=0)
    decode_percent: int = field(default=0)
    # decode_is_loading: bool = field(default=False)
    # decode_state: DecodeLogState = DecodeLogState.UNAVAILABLE
    decode_signal_list: List[Tuple[CANID, SigID]] = field(default_factory=list)

    _DECODE_HDR_SIZE: int = 32
    _DECODE_HDR_STRUCT: Any = field(default=struct.Struct("<QII16x"), init=False, repr=False)
    _SIGNAL_DIR_HDR_STRUCT: Any = field(default=struct.Struct("<II24x"), init=False, repr=False)
    _SIGNAL_DIR_ENTRY_SIZE: int = 52
    _SIGNAL_DIR_ENTRY_STRUCT: Any = field(default=struct.Struct("<IHHQQQQIIHH"), init=False, repr=False)

    # @property
    # def file_name(self) -> str:
    #     if not self.file_path:
    #         return ""
    #     return Path(self.file_path).name

    @property
    def decode_signal_name_list(self) -> List[SignalName]:
        return [f"{can_id}:{signal_id}" for can_id, signal_id in self.decode_signal_list]

    @property
    def decode_signal_id_list(self) -> List[int]:
        seen: Set[int] = set()
        ordered: List[int] = []
        for _, signal_id in self.decode_signal_list:
            sid = int(signal_id)
            if sid in seen:
                continue
            seen.add(sid)
            ordered.append(sid)
        return ordered

    def _get_decode_signal_entries(
        self,
        signal_id: Optional[int] = None,
        can_id: Optional[int] = None,
    ) -> List[Tuple[int, int, int, int, int, int, int, int]]:
        entries = self._load_decode_signal_directory_entries()
        if signal_id is None and can_id is None:
            return entries

        matched: List[Tuple[int, int, int, int, int, int, int, int]] = []
        sid = int(signal_id) if signal_id is not None else None
        cid = int(can_id) if can_id is not None else None
        for entry in entries:
            entry_can_id, entry_signal_id = int(entry[0]), int(entry[1])
            if sid is not None and entry_signal_id != sid:
                continue
            if cid is not None and entry_can_id != cid:
                continue
            matched.append(entry)
        return matched

    def get_signal_value_list_by_key(self, can_id: int, signal_id: int) -> List[float]:
        return self.get_signal_value_list(signal_id=int(signal_id), can_id=int(can_id))

    def get_signal_rawvalue_list_by_key(self, can_id: int, signal_id: int) -> List[int]:
        return self.get_signal_rawvalue_list(signal_id=int(signal_id), can_id=int(can_id))

    def get_page_from_signal_row_indices_with_rawvalue_list(
        self,
        signal_id: int,
        rvalues: List[int],
        first_line: int = 0,
        page_size: int = 100,
    ) -> List[CANLogLine]:
        return self.get_page_from_signal_ids_row_indices_with_rawvalue_map(
            signal_rawvalues={int(signal_id): [int(v) for v in rvalues]},
            first_line=first_line,
            page_size=page_size,
            match_mode="or",
        )

    def get_signal_value_list(self, signal_id: int, can_id: Optional[int] = None) -> List[float]:
        matched = self._get_decode_signal_entries(signal_id=int(signal_id), can_id=can_id)
        if not matched:
            LOG.debug("get_signal_value_list: no directory entry for signal_id=%s can_id=%s", signal_id, can_id)
            return []

        for m in matched:
            LOG.debug(
                "get_signal_value_list: dir entry can_id=0x%X sig_id=%d idx_off=%d val_off=%d raw_off=%d chg_off=%d sample_count=%d chg_count=%d",
                m[0], m[1], m[2], m[3], m[4], m[5], m[6], m[7],
            )

        value_paths = self.decode_value_segment_paths()
        if not value_paths:
            return []

        seg_cache, capacities = self._open_decode_array_segments(value_paths)
        values: List[float] = []
        try:
            for _, _, _, value_off, _, _, sample_count, _ in matched:
                for j in range(sample_count):
                    v = self._decode_read_scalar_from_sample_pos(
                        sample_pos=value_off + j,
                        seg_cache=seg_cache,
                        capacities=capacities,
                        elem_size=8,
                        unpack_fmt="<d",
                    )
                    if v is not None:
                        values.append(float(v))
        finally:
            self._close_seg_cache(seg_cache)
        return values

    def get_signal_rawvalue_list(self, signal_id: int, can_id: Optional[int] = None) -> List[int]:
        matched = self._get_decode_signal_entries(signal_id=int(signal_id), can_id=can_id)
        if not matched:
            LOG.debug("get_signal_rawvalue_list: no directory entry for signal_id=%s can_id=%s", signal_id, can_id)
            return []

        for m in matched:
            LOG.debug(
                "get_signal_rawvalue_list: dir entry can_id=0x%X sig_id=%d sample_count=%d chg_count=%d",
                m[0], m[1], m[6], m[7],
            )

        raw_paths = self.decode_rawvalue_segment_paths()
        if not raw_paths:
            return []

        seg_cache, capacities = self._open_decode_array_segments(raw_paths)
        raw_values: List[int] = []
        try:
            for _, _, _, _, raw_off, _, sample_count, _ in matched:
                for j in range(sample_count):
                    rv = self._decode_read_scalar_from_sample_pos(
                        sample_pos=raw_off + j,
                        seg_cache=seg_cache,
                        capacities=capacities,
                        elem_size=8,
                        unpack_fmt="<q",
                    )
                    if rv is not None:
                        raw_values.append(int(rv))
        finally:
            self._close_seg_cache(seg_cache)
        return raw_values

    def get_signal_changed_row_index_list(self, signal_id: int) -> List[int]:
        entries = self._load_decode_signal_directory_entries()
        matched = [e for e in entries if e[1] == int(signal_id)]
        if not matched:
            return []

        changed_paths = self.decode_row_index_changed_segment_paths()
        if not changed_paths:
            return []

        seg_cache, capacities = self._open_decode_array_segments(changed_paths)
        changed_rows: List[int] = []
        try:
            for _, _, _, _, _, changed_off, _, changed_count in matched:
                for j in range(changed_count):
                    ridx = self._decode_read_scalar_from_sample_pos(
                        sample_pos=changed_off + j,
                        seg_cache=seg_cache,
                        capacities=capacities,
                        elem_size=4,
                        unpack_fmt="<I",
                    )
                    if ridx is not None:
                        changed_rows.append(int(ridx))
        finally:
            self._close_seg_cache(seg_cache)
        return changed_rows

    def decode_signal_dir_segment_paths(self) -> List[Path]:
        return self._decode_segment_paths(self.decode_signal_dir_mmap_path)

    def decode_row_index_segment_paths(self) -> List[Path]:
        return self._decode_segment_paths(self.decode_row_index_mmap_path)

    def decode_row_index_changed_segment_paths(self) -> List[Path]:
        return self._decode_segment_paths(self.decode_row_index_changed_mmap_path)

    def decode_value_segment_paths(self) -> List[Path]:
        return self._decode_segment_paths(self.decode_value_mmap_path)

    def decode_rawvalue_segment_paths(self) -> List[Path]:
        return self._decode_segment_paths(self.decode_rawvalue_mmap_path)

    def _decode_segment_paths(self, base_path: str) -> List[Path]:
        if not base_path:
            return []
        base = Path(base_path)
        if base.exists():
            return [base]
        stem = base.name[:-5] if base.name.endswith(".mmap") else base.name
        return sorted(base.parent.glob(f"{stem}.[0-9][0-9][0-9].mmap"))

    def _decode_global_sample_pos_to_segment_local(
        self,
        sample_pos: int,
        capacities: List[int],
    ) -> Optional[Tuple[int, int]]:
        rem = int(sample_pos)
        for seg_idx, cap in enumerate(capacities):
            if rem < cap:
                return seg_idx, rem
            rem -= cap
        return None

    def _decode_read_scalar_from_sample_pos(
        self,
        sample_pos: int,
        seg_cache: Dict[int, Tuple[Any, _mmap.mmap]],
        capacities: List[int],
        elem_size: int,
        unpack_fmt: str,
    ) -> Optional[Any]:
        mapped = self._decode_global_sample_pos_to_segment_local(sample_pos, capacities)
        if mapped is None:
            return None
        seg_idx, local = mapped
        if seg_idx not in seg_cache:
            return None
        _, mm = seg_cache[seg_idx]
        offset = self._DECODE_HDR_SIZE + local * elem_size
        if offset + elem_size > len(mm):
            return None
        return struct.unpack_from(unpack_fmt, mm, offset)[0]

    def _load_decode_signal_directory_entries(self) -> List[Tuple[int, int, int, int, int, int, int, int]]:
        entries: List[Tuple[int, int, int, int, int, int, int, int]] = []
        for seg_path in self.decode_signal_dir_segment_paths():
            with open(seg_path, "rb") as f:
                mm = _mmap.mmap(f.fileno(), 0, access=_mmap.ACCESS_READ)
                try:
                    entry_count, status = self._SIGNAL_DIR_HDR_STRUCT.unpack_from(mm, 0)
                    if status == 0 or entry_count == 0:
                        continue
                    for i in range(int(entry_count)):
                        off = self._DECODE_HDR_SIZE + i * self._SIGNAL_DIR_ENTRY_SIZE
                        if off + self._SIGNAL_DIR_ENTRY_SIZE > len(mm):
                            break
                        (
                            can_id,
                            signal_id,
                            _,
                            index_offset,
                            value_offset,
                            rawvalue_offset,
                            changed_index_offset,
                            sample_count,
                            changed_sample_count,
                            _,
                            _,
                        ) = self._SIGNAL_DIR_ENTRY_STRUCT.unpack_from(mm, off)
                        if sample_count <= 0:
                            continue
                        entries.append((
                            int(can_id),
                            int(signal_id),
                            int(index_offset),
                            int(value_offset),
                            int(rawvalue_offset),
                            int(changed_index_offset),
                            int(sample_count),
                            int(changed_sample_count),
                        ))
                finally:
                    mm.close()
        return entries

    def _open_decode_array_segments(self, paths: List[Path]) -> Tuple[Dict[int, Tuple[Any, _mmap.mmap]], List[int]]:
        seg_cache: Dict[int, Tuple[Any, _mmap.mmap]] = {}
        capacities: List[int] = []
        for i, seg_path in enumerate(paths):
            f = open(seg_path, "rb")
            mm = _mmap.mmap(f.fileno(), 0, access=_mmap.ACCESS_READ)
            seg_cache[i] = (f, mm)
            _, capacity, status = self._DECODE_HDR_STRUCT.unpack_from(mm, 0)
            capacities.append(int(capacity) if status != 0 else 0)
        return seg_cache, capacities

    def _close_seg_cache(self, seg_cache: Dict[int, Tuple[Any, _mmap.mmap]]) -> None:
        for f, mm in seg_cache.values():
            mm.close()
            f.close()

    def _read_decode_segment_status(self, seg_path: Path) -> int:
        try:
            with open(seg_path, "rb") as f:
                f.seek(12)
                raw = f.read(4)
                if len(raw) < 4:
                    return 0
                return int(struct.unpack("<I", raw)[0])
        except Exception:
            return 0

    def _read_decode_segment_write_count(self, seg_path: Path) -> int:
        try:
            with open(seg_path, "rb") as f:
                hdr = f.read(8)
                if len(hdr) < 8:
                    return 0
                return int(struct.unpack("<Q", hdr)[0])
        except Exception:
            return 0

    def refresh_decode_mmap_runtime(self):
        row_index_segs = self.decode_row_index_segment_paths()
        row_index_changed_segs = self.decode_row_index_changed_segment_paths()
        self.decode_mmap_file_count = len(row_index_segs)
        self.decode_verified_size = sum(self._read_decode_segment_write_count(seg) for seg in row_index_segs)

        signal_dir_ready = len(self.decode_signal_dir_segment_paths()) > 0
        row_index_changed_ready = len(row_index_changed_segs) > 0
        row_index_ready = len(row_index_segs) > 0
        value_ready = len(self.decode_value_segment_paths()) > 0
        rawvalue_ready = len(self.decode_rawvalue_segment_paths()) > 0

        # if not (signal_dir_ready and row_index_changed_ready and row_index_ready and value_ready and rawvalue_ready):
        #     self.decode_state = DecodeLogState.UNAVAILABLE
        #     return

        # all_done = all(self._read_decode_segment_status(seg) != 0 for seg in row_index_segs)
        # self.decode_state = DecodeLogState.AVAILABLE if all_done else DecodeLogState.UNAVAILABLE


