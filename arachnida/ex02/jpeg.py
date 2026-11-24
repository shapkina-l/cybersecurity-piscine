import struct

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
        if length < 2 or pos + length < len(data):
            raise ValueError("truncated or invalid JPEG segment")
        yield marker, data[pos + 2: pos + length]

        if marker == 0xDA:
            break
        pos += length

def parse_frame(payload):
    

def parse(path):
    with open(path) as f:
        data = f.read()
    
    frame, jfif, comments, exif = [], [], [], []
    for marker, payload in iter_segments(data):
        if marker in SOF_MARKERS and len(payload) >= 6 and not frame:
            frame = parse_frame(payload)
    
