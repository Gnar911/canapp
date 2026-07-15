# region: Helper function
from typing import Tuple, List
import textwrap
import os
import shutil
import subprocess
from pathlib import Path
import csv
from datetime import datetime
from can_sdk.data_object import CANLogLine

def extract_msg_view_format(value):
    hex_part = value.split(']')[0][1:]      # lấy nội dung trong []
    dec_id = int(hex_part, 16)              # chuyển hex → int
    name_part = value.split(']', 1)[1].strip()
    return dec_id, name_part

def extract_list_msg_view_format(value) -> List[Tuple]:
    hex_part = value.split(']')[0][1:]      # lấy nội dung trong []
    dec_id = int(hex_part, 16)              # chuyển hex → int
    name_part = value.split(']', 1)[1].strip()
    return dec_id, name_part


def wrap_text_by_word_boundary(text, max_length=20):
    return '\n'.join(textwrap.wrap(text, width=max_length, break_long_words=False, break_on_hyphens=False))

def open_in_editor(filepath: str):
    """
    Open the given file in Notepad++ if it’s on the PATH,
    otherwise open it in the default Notepad.
    """
    path = Path(filepath).absolute()
    try:
        subprocess.Popen([r"C:\Program Files\Notepad++\notepad++.exe", str(path)])
    except:
        subprocess.Popen(["notepad.exe", str(path)])

def open_in_excel(filepath: str):
    try:
        path = Path(filepath).absolute()
        os.startfile(path)
    except:
        path = Path(filepath).absolute()
        excel_path = r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE"

        try:
            subprocess.Popen([excel_path, str(path)])
        except FileNotFoundError:
            # fallback to default handler
            import os
            os.startfile(path)

def blend_colors(hex1, hex2, ratio=0.5):
    # Convert hex to RGB tuple
    def hex_to_rgb(h): return tuple(int(h[i:i+2], 16) for i in (1, 3, 5))
    def rgb_to_hex(rgb): return "#{:02X}{:02X}{:02X}".format(*rgb)

    rgb1 = hex_to_rgb(hex1)
    rgb2 = hex_to_rgb(hex2)

    blended = tuple(int(a * (1 - ratio) + b * ratio) for a, b in zip(rgb1, rgb2))
    return rgb_to_hex(blended)


def write_log_csv(self, filepath, lines: list[CANLogLine], save_filepath: str = None):
    if not save_filepath:
        save_filepath = filepath + "_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".csv"
    with open(save_filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        msg_filt = self.data[filepath].group_messages_by_can_id(lines)

        for can_id, msg_lines in msg_filt.items():
            # ---- Message header ----
            writer.writerow([
                "Time",
                "Channel",
                "CAN ID",
                "Message Name",
                "Direction",
                "DLC",
                "Data",
            ])

            # ---- Signal header (from first message) ----
            sig_names = msg_lines[0].get_list_signal_name_fromline()
            writer.writerow(sig_names)

            # ---- Message + signal rows ----
            for l in msg_lines:
                # message row
                writer.writerow([
                    f"{l.timestamp:.6f}",
                    l.channel,
                    f"0x{l.can_id:X}",
                    l.message_name or "",
                    l.direction,
                    l.data_len,
                    l.raw_data,
                ])

                # signal row (aligned with sig_names)
                writer.writerow([
                    str(l.message_obj.signals[sig].raw_value)
                    if sig in l.message_obj.signals else ""
                    for sig in sig_names
                ])

            # ---- Empty row between CAN ID groups ----
            writer.writerow([])
            writer.writerow([])
            writer.writerow([])
            writer.writerow([])
            writer.writerow([])