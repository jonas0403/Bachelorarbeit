"""
File-based debug logging for MULTALL Stage Generator.
All debug output is written to a single file with timestamps and section markers.
"""

import os
from datetime import datetime

_file_handle = None
_file_path = None

def open_file(file_path):
    global _file_handle, _file_path
    close_file()
    _file_path = file_path
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    _file_handle = open(file_path, "w", encoding="utf-8")
    _write_line(f"Debug log opened: {file_path}")
    _write_line(f"Session started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    _write_line("")

def debug(msg, context=None):
    if _file_handle is not None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        prefix = f"[{timestamp}]"
        if context:
            prefix += f" [{context}]"
        _write_line(f"{prefix} {msg}")

def section(title):
    if _file_handle is not None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        _write_line("")
        _write_line("=" * 80)
        _write_line(f"[{timestamp}] === {title} ===")
        _write_line("=" * 80)
        _write_line("")

def _write_line(text):
    if _file_handle is not None:
        _file_handle.write(text + "\n")
        _file_handle.flush()

def close_file():
    global _file_handle
    if _file_handle is not None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        _write_line("")
        _write_line(f"[{timestamp}] Debug log closed.")
        _file_handle.close()
        _file_handle = None

def file_path():
    return _file_path
