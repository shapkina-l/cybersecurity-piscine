import struct
from fractions import Fraction

TYPE_SIZES = {1: 1, 2: 1, 3: 2, 4: 4, 5: 8, 6: 1, 7: 1, 8: 2, 9: 4, 10: 8, 11: 4, 12: 8}

TYPE_CODES = {1: "B", 3: "H", 4: "I", 6: "b", 8: "h", 9: "i", 11: "f", 12: "d"}

EXIF_POINTER = 0x8769      # in IFD0: offset of the Exif sub-IFD
GPS_POINTER = 0x8825       # in IFD0: offset of the GPS sub-IFD
INTEROP_POINTER = 0xA005   # in the Exif sub-IFD (ignored)

IFD0_TAGS = {
    0x010E: "ImageDescription",
    0x010F: "Make",
    0x0110: "Model",
    0x0112: "Orientation",
    0x011A: "XResolution",
    0x011B: "YResolution",
    0x0128: "ResolutionUnit",
    0x0131: "Software",
    0x0132: "DateTime",
    0x013B: "Artist",
    0x8298: "Copyright",
}

EXIF_TAGS = {
    0x829A: "ExposureTime",
    0x829D: "FNumber",
    0x8822: "ExposureProgram",
    0x8827: "ISOSpeedRatings",
    0x9000: "ExifVersion",
    0x9003: "DateTimeOriginal",
    0x9004: "DateTimeDigitized",
    0x9201: "ShutterSpeedValue",
    0x9202: "ApertureValue",
    0x9204: "ExposureBiasValue",
    0x9207: "MeteringMode",
    0x9209: "Flash",
    0x920A: "FocalLength",
    0x927C: "MakerNote",
    0x9286: "UserComment",
    0xA002: "PixelXDimension",
    0xA003: "PixelYDimension",
    0xA402: "ExposureMode",
    0xA403: "WhiteBalance",
    0xA405: "FocalLengthIn35mmFilm",
    0xA406: "SceneCaptureType",
    0xA420: "ImageUniqueID",
    0xA430: "CameraOwnerName",
    0xA431: "BodySerialNumber",
    0xA432: "LensSpecification",
    0xA433: "LensMake",
    0xA434: "LensModel",
}

GPS_TAGS = {
    0x00: "GPSVersionID",
    0x01: "GPSLatitudeRef",
    0x02: "GPSLatitude",
    0x03: "GPSLongitudeRef",
    0x04: "GPSLongitude",
    0x05: "GPSAltitudeRef",
    0x06: "GPSAltitude",
    0x07: "GPSTimeStamp",
    0x1D: "GPSDateStamp",
}

def read_header(data):
    """Return (endian, offset_of_IFD0). `endian` is a struct prefix."""
    if len(data) < 8:
        raise ValueError("EXIF block too short")
    if data[:2] == b"II":
        endian = "<"
    elif data[:2] == b"MM":
        endian = ">"
    else:
        raise ValueError("invalid EXIF byte order mark")
    magic, offset = struct.unpack_from(endian + "HI", data, 2)
    if magic != 42:
        raise ValueError("invalid TIFF magic number")
    return endian, offset

def decode_value(data, endian, typ, count, field_pos):
    """Decode one entry's value. Returns None if it can't be decoded."""
    size = TYPE_SIZES.get(typ)
    if size is None:
        return None
    total = size * count
    if total <= 4:
        start = field_pos
    else:
        (start,) = struct.unpack_from(endian + "I", data, field_pos)
    if start + total > len(data):
        return None
    raw = data[start:start + total]

    if typ == 2:                               # ASCII string
        return raw.split(b"\x00")[0].decode("utf-8", errors="replace").strip()
    if typ == 7:                               # UNDEFINED: raw bytes
        return raw
    if typ in (5, 10):                         # (S)RATIONAL: numerator/denominator
        code = "I" if typ == 5 else "i"
        nums = struct.unpack(f"{endian}{count * 2}{code}", raw)
        values = [Fraction(nums[i], nums[i + 1]) if nums[i + 1] else None
                  for i in range(0, len(nums), 2)]
    else:
        values = list(struct.unpack(f"{endian}{count}{TYPE_CODES[typ]}", raw))
    return values[0] if count == 1 else tuple(values)

def read_ifd(data, endian, offset):
    """Return a list of (tag, value) for the IFD at `offset`."""
    if offset + 2 > len(data):
        raise ValueError("IFD offset outside EXIF block")
    (num_entries,) = struct.unpack_from(endian + "H", data, offset)
    entries = []
    pos = offset + 2
    for _ in range(num_entries):
        if pos + 12 > len(data):
            break                              # truncated: keep what we have
        tag, typ, count = struct.unpack_from(endian + "HHI", data, pos)
        entries.append((tag, decode_value(data, endian, typ, count, pos + 8)))
        pos += 12
    return entries

def format_bytes(raw):
    if raw.startswith(b"ASCII\x00\x00\x00"):   # UserComment charset prefix
        raw = raw[8:]
    text = raw.rstrip(b"\x00")
    if text and all(32 <= c < 127 for c in text):
        return text.decode("ascii")
    return f"<{len(raw)} bytes of binary data>"

def format_value(value):
    if value is None:
        return "undefined"
    if isinstance(value, Fraction):
        if value.denominator == 1:
            return str(value.numerator)
        return f"{value} ({float(value):.4g})"
    if isinstance(value, bytes):
        return format_bytes(value)
    if isinstance(value, tuple):
        shown = ", ".join(format_value(v) for v in value[:16])
        return shown + (", ..." if len(value) > 16 else "")
    return str(value)

def build_section(title, entries, names, skip=()):
    """Turn raw (tag, value) entries into a (title, [(label, text), ...])."""
    attrs = []
    for tag, value in entries:
        if tag in skip or value is None:
            continue
        label = names.get(tag, f"Tag 0x{tag:04X}")
        attrs.append((label, format_value(value)))
    return (title, attrs) if attrs else None

def dms_to_decimal(dms, ref):
    """(degrees, minutes, seconds) + 'N'/'S'/'E'/'W' -> signed decimal degrees."""
    degrees, minutes, seconds = (float(x) for x in dms)
    value = degrees + minutes / 60 + seconds / 3600
    return -value if ref in ("S", "W") else value

def gps_position(entries):
    """Return 'lat, lon' in decimal degrees, or None if not available."""
    tags = dict(entries)
    try:
        lat = dms_to_decimal(tags[0x02], tags[0x01])
        lon = dms_to_decimal(tags[0x04], tags[0x03])
    except (KeyError, TypeError, ValueError):
        return None
    return f"{lat:.6f}, {lon:.6f}"

def parse_exif(data):
    endian, ifd0_offset = read_header(data)
    ifd0 = read_ifd(data, endian, ifd0_offset)

    exif_ifd, gps_ifd = [], []
    for tag, value in ifd0:
        if tag == EXIF_POINTER and isinstance(value, int):
            exif_ifd = read_ifd(data, endian, value)
        elif tag == GPS_POINTER and isinstance(value, int):
            gps_ifd = read_ifd(data, endian, value)

    gps = build_section("EXIF: GPS", gps_ifd, GPS_TAGS)
    if gps:
        position = gps_position(gps_ifd)
        if position:
            gps[1].append(("Position", position))

    sections = [
        build_section("EXIF: image", ifd0, IFD0_TAGS,
                      skip=(EXIF_POINTER, GPS_POINTER)),
        build_section("EXIF: camera", exif_ifd, EXIF_TAGS,
                      skip=(INTEROP_POINTER,)),
        gps,
    ]
    return [s for s in sections if s]