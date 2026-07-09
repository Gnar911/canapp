# region: Helper function
from typing import Optional, Tuple, List
import textwrap
import os
import shutil
import subprocess
from pathlib import Path
import re

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

def hex_raw_to_bytes(raw: str) -> bytes:
    """
    "00 1A FF" | "001AFF" | "00,1A,FF" -> bytes
    """
    if not raw:
        return b""

    s = raw.strip().upper()

    # normalize separators
    s = re.sub(r"[,\-_:]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()

    parts = s.split(" ")

    # case: space-separated bytes
    if len(parts) > 1:
        return bytes(int(p, 16) for p in parts if p)

    # case: no spaces (e.g. 001AFF)
    if len(s) % 2 != 0:
        raise ValueError(f"Invalid hex string length: {raw}")

    return bytes(int(s[i:i+2], 16) for i in range(0, len(s), 2))

""" bytes_to_hex_raw(b"\x00\x1A\xFF")
# "00 1A FF" """
def bytes_to_hex_raw(data: bytes) -> str:
    """
    bytes -> "00 1A FF"
    """
    return " ".join(f"{b:02X}" for b in data)