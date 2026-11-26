import struct

from exif import parse_exif

EXIF_HEADER = b"Exif\x00\x00"

SOF_MARKERS = [m for m in range(0xC0, 0xD0) if m not in (0xC4, 0xC8, 0xCC)]

def iter_segments(data):
    if data[:2] != b"\xff\xd8":
        raise ValueError("missing JPEG start-of-image marker")
    pos = 2
    while pos < len(data):
        if data[pos] != 0xFF:
            raise ValueError(f"expected a marker at offset {pos}")
        while pos < len(data) and data[pos] == 0xFF:
            pos += 1
        if pos >= len(data):
            break
        marker = data[pos]
        pos += 1

        if marker == 0xD9:
            break
        if marker == 0x01 or 0xD0 <= marker <= 0xD7:
            continue

        if pos + 2 > len(data):
            raise ValueError("truncated JPEG segment header")
        (length,) = struct.unpack_from(">H", data, pos)
        if length < 2 or pos + length > len(data):
            raise ValueError("truncated or invalid JPEG segment")
        yield marker, data[pos + 2: pos + length]

        if marker == 0xDA:
            break
        pos += length

def parse_jfif(payload):
    version, units, xdens, ydens = struct.unpack_from(">HBHH", payload, 5)
    unit_names = {0: "none (aspect ratio)", 1: "dpi", 2: "dpcm"}
    return [
        ("Version", f"{version >> 8}.{version & 0xFF:02d}"),
        ("Density", f"{xdens} x {ydens} {unit_names.get(units, '?')}"),
    ]

def parse_frame(payload):
    precision, height, width, components = struct.unpack_from(">BHHB", payload)
    return [
        ("Dimensions", f"{width} x {height} pixels"),
        ("Bits per sample", str(precision)),
        ("Components", str(components)),
    ]

def parse(path):
    with open(path, "rb") as f:
        data = f.read()
    
    frame, jfif, comments, exif = [], [], [], []
    for marker, payload in iter_segments(data):
        if marker in SOF_MARKERS and len(payload) >= 6 and not frame:
            frame = parse_frame(payload)
        elif marker == 0xE0 and payload.startswith(b"JFIF\x00") and len(payload) >= 12:
            jfif = parse_jfif(payload)
        elif marker == 0xE1 and payload.startswith(EXIF_HEADER):
            exif += parse_exif(payload[len(EXIF_HEADER):])
        elif marker == 0xFE:
            text = payload.rstrip(b"\x00").decode("utf-8", errors="replace")
            comments.append(("Comment", text))    

    sections = []
    if frame:
        sections.append(("JPEG image", frame))
    if jfif:
        sections.append(("JFIF", jfif))
    if comments:
        sections.append(("JPEG comments", comments))
    return sections + exif