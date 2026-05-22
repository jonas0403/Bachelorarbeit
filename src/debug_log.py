import os

_file_handle = None
_file_path = None

def open_file(file_path):
    global _file_handle, _file_path
    close_file()
    _file_path = file_path
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    _file_handle = open(file_path, "w", encoding="utf-8")

def debug(msg):
    if _file_handle is not None:
        _file_handle.write(str(msg) + "\n")
        _file_handle.flush()

def close_file():
    global _file_handle
    if _file_handle is not None:
        _file_handle.close()
        _file_handle = None

def file_path():
    return _file_path
