import struct

COMPRESSION = {
    0: "none (BI_RGB)",
    1: "RLE 8-bit",
    2: "RLE 4-bit",
    3: "bit fields (BI_BITFIELDS)",
    4: "JPEG",
    5: "PNG",
    6: "bit fields with alpha",
}

HEADER_NAMES = {
    12: "BITMAPCOREHEADER (OS/2)",
    40: "BITMAPINFOHEADER",
    52: "BITMAPV2INFOHEADER",
    56: "BITMAPV3INFOHEADER",
    64: "OS/2 BITMAPCOREHEADER2",
    108: "BITMAPV4HEADER",
    124: "BITMAPV5HEADER",
}

def parse(path):
    with open(path, "rb") as f:
        data = f.read()

    if data[:2] != b"BM":
        raise ValueError("missing BMP signature")
    if len(data) < 18:
        raise ValueError("truncated BMP header")

    declared_size, data_offset = struct.unpack_from("<I4xI", data, 2)
    (header_size,) = struct.unpack_from("<I", data, 14)

    header = [
        ("Declared file size", f"{declared_size} bytes"),
        ("Pixel data offset", f"{data_offset} bytes"),
        ("DIB header", f"{HEADER_NAMES.get(header_size, 'unknown')} ({header_size} bytes)"),
    ]
    if declared_size != len(data):
        header.append(("Warning", f"declared size differs from the real size ({len(data)} bytes)"))

    if header_size == 12:                          # old OS/2 header, 16-bit fields
        if len(data) < 14 + 12:
            raise ValueError("truncated BMP header")
        width, height, _planes, bpp = struct.unpack_from("<HHHH", data, 18)
        image = [
            ("Dimensions", f"{width} x {height} pixels"),
            ("Bits per pixel", str(bpp)),
        ]
        return [("BMP header", header), ("BMP image", image)]

    if header_size < 40:
        raise ValueError(f"unsupported BMP header size ({header_size})")
    if len(data) < 14 + 40:
        raise ValueError("truncated BMP header")

    width, height, _planes, bpp, compression, image_size, xppm, yppm, colors, important = \
        struct.unpack_from("<iiHHIIiiII", data, 18)

    image = [
        ("Dimensions", f"{width} x {abs(height)} pixels"),
        ("Row order", "top-down" if height < 0 else "bottom-up"),
        ("Bits per pixel", str(bpp)),
        ("Compression", COMPRESSION.get(compression, f"unknown ({compression})")),
    ]
    if image_size:
        image.append(("Image data size", f"{image_size} bytes"))
    if xppm or yppm:
        image.append(("Resolution", f"{xppm} x {yppm} pixels/m "
                      f"({xppm * 0.0254:.0f} x {yppm * 0.0254:.0f} dpi)"))
    if colors:
        image.append(("Colors in palette", str(colors)))
    elif bpp <= 8:
        image.append(("Colors in palette", f"{1 << bpp} (default)"))
    if important:
        image.append(("Important colors", str(important)))

    return [("BMP header", header), ("BMP image", image)]
