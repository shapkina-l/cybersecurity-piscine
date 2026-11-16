import os 
import datetime

def format_size(num_bytes):
    size = float(num_bytes)
    for unit in ("B", "KiB", "MiB", "GiB"):
        if size < 1024 or unit == "GiB":
            if unit == "B":
                return f"{num_bytes} bytes"
            return f"{size:.1f} {unit} ({num_bytes} bytes)"
        size /= 1024

def format_time(timestamp):
    return datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")

def get_basic_attributes(path):
    st = os.stat(path)
    attrs = [
        ("File name", os.path.basename(path)),
        ("Size", format_size(st.st_size)),
        ("Modified", format_time(st.st_mtime)),
        ("Accessed", format_time(st.st_atime)),
    ]
    birth = getattr(st, "st_birthtime", None)
    if birth is not None:
        attrs.append(("Created", format_time(birth)))
    else:
        attrs.append(("Status changed", format_time(st.st_ctime)))
    return attrs


