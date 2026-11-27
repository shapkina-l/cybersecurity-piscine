import struct
import zlib

from exif import parse_exif

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"

MAX_TEXT = 200                 # long values (e.g. XMP) are shortened when printed
MAX_DECOMPRESSED = 1_000_000 

COLOR_TYPES = {
    0: "Grayscale",
    2: "RGB",
    3: "Indexed (palette)",
    4: "Grayscale + alpha",
    6: "RGB + alpha",
}

SRGB_INTENTS = {
    0: "Perceptual",
    1: "Relative colorimetric",
    2: "Saturation",
    3: "Absolute colorimetric",
}

def iter_chunks(data):
    if data[:8] != PNG_SIGNATURE:
        raise ValueError("missing PNG signature")
    pos = 8
    while pos < len(data):
        if pos + 8 > len(data):
            raise ValueError("truncated PNG chunk header")
        length, ctype = struct.unpack_from(">I4s", data, pos)
        start = pos + 8
        end = start + length
        if end + 4 > len(data):
            raise ValueError("truncated PNG chunk")
        yield ctype, data[start:end]
        if ctype == b"IEND":
            break
        pos = end + 4

def shorten(text):
    text = " ".join(text.split())              # one line, no repeated spaces
    if len(text) > MAX_TEXT:
        return text[:MAX_TEXT] + "..."
    return text

def inflate(raw):
    """Decompress zlib data, refusing to produce more than MAX_DECOMPRESSED."""
    decompressor = zlib.decompressobj()
    out = decompressor.decompress(raw, MAX_DECOMPRESSED)
    if decompressor.unconsumed_tail:
        return out + b"..."
    return out

def parse_ihdr(payload):
    width, height, depth, color, compression, flt, interlace = \
        struct.unpack_from(">IIBBBBB", payload)
    return [
        ("Dimensions", f"{width} x {height} pixels"),
        ("Bit depth", str(depth)),
        ("Color type", COLOR_TYPES.get(color, f"unknown ({color})")),
        ("Interlace", "Adam7" if interlace == 1 else "none"),
    ]

def parse_phys(payload):
    xppu, yppu, unit = struct.unpack_from(">IIB", payload)
    if unit == 1:                              # pixels per metre
        return f"{xppu} x {yppu} pixels/m ({xppu * 0.0254:.0f} x {yppu * 0.0254:.0f} dpi)"
    return f"{xppu} x {yppu} (unit unknown, aspect ratio only)"

def parse_time(payload):
    year, month, day, hour, minute, second = struct.unpack_from(">HBBBBB", payload)
    return f"{year:04d}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:{second:02d} UTC"

def parse_text(payload):
    keyword, _, text = payload.partition(b"\x00")
    return keyword.decode("latin-1"), text.decode("latin-1")

def parse_ztxt(payload):
    keyword, _, rest = payload.partition(b"\x00")
    # rest[0] is the compression method (always 0 = zlib)
    text = inflate(rest[1:])
    return keyword.decode("latin-1"), text.decode("latin-1", errors="replace")

def parse_itxt(payload):
    keyword, _, rest = payload.partition(b"\x00")
    compressed, _method = rest[0], rest[1]
    rest = rest[2:]
    _language, _, rest = rest.partition(b"\x00")
    _translated, _, text = rest.partition(b"\x00")
    if compressed:
        text = inflate(text)
    return keyword.decode("utf-8", errors="replace"), text.decode("utf-8", errors="replace")

def parse(path):
    with open(path, "rb") as f:
        data = f.read()
    
    image, texts, exif = [], [], []
    for ctype, payload in iter_chunks(data):
        if ctype == b"IHDR" and len(payload) >= 13:
            image += parse_ihdr(payload)
        elif ctype == b"acTL" and len(payload) >= 8:
            frames, plays = struct.unpack_from(">II", payload)
            image.append(("Animation", f"{frames} frames, loops: "
                          + ("forever" if plays == 0 else str(plays))))
        elif ctype == b"pHYs" and len(payload) >= 9:
            image.append(("Resolution", parse_phys(payload)))
        elif ctype == b"tIME" and len(payload) >= 7:
            image.append(("Last modified", parse_time(payload)))
        elif ctype == b"gAMA" and len(payload) >= 4:
            (gamma,) = struct.unpack_from(">I", payload)
            image.append(("Gamma", f"{gamma / 100000:.5f}"))
        elif ctype == b"sRGB" and len(payload) >= 1:
            image.append(("sRGB intent", SRGB_INTENTS.get(payload[0], "unknown")))
        elif ctype == b"iCCP":
            name = payload.split(b"\x00")[0].decode("latin-1")
            image.append(("ICC profile", name))
        elif ctype in (b"tEXt", b"zTXt", b"iTXt"):
            reader = {b"tEXt": parse_text, b"zTXt": parse_ztxt, b"iTXt": parse_itxt}[ctype]
            try:
                keyword, text = reader(payload)
            except (zlib.error, IndexError):
                keyword, text = "(unreadable text chunk)", ""
            texts.append((keyword, shorten(text)))
        elif ctype == b"eXIf":
            try:
                exif += parse_exif(payload)
            except (ValueError, struct.error):
                pass   
        
    sections = []
    if image:
        sections.append(("PNG image", image))
    if texts:
        sections.append(("PNG text", texts))
    return sections + exif    