import struct

MAX_TEXT = 200

def shorten(text):
    text = " ".join(text.split())
    if len(text) > MAX_TEXT:
        return text[:MAX_TEXT] + "..."
    return text

def read_sub_blocks(data, pos):
    """Read a chain of length-prefixed sub-blocks. Returns (blocks, next_pos)."""
    blocks = []
    while True:
        if pos >= len(data):
            raise ValueError("truncated GIF data")
        size = data[pos]
        pos += 1
        if size == 0:
            return blocks, pos
        if pos + size > len(data):
            raise ValueError("truncated GIF data")
        blocks.append(data[pos:pos + size])
        pos += size

def parse(path):
    with open(path, "rb") as f:
        data = f.read()

    if data[:6] not in (b"GIF87a", b"GIF89a"):
        raise ValueError("missing GIF header")
    if len(data) < 13:
        raise ValueError("truncated GIF header")

    version = data[3:6].decode("ascii")
    width, height, packed, background, aspect = struct.unpack_from("<HHBBB", data, 6)
    has_global_table = bool(packed & 0x80)
    global_colors = 2 << (packed & 0x07) if has_global_table else 0
    pos = 13
    if has_global_table:
        pos += 3 * global_colors

    frames = 0
    total_delay = 0              # in hundredths of a second
    loops = None
    comments = []
    applications = []
    transparent = False

    while pos < len(data):
        block = data[pos]
        pos += 1

        if block == 0x3B:                          # trailer: end of file
            break

        elif block == 0x21:                        # extension
            if pos >= len(data):
                raise ValueError("truncated GIF extension")
            label = data[pos]
            pos += 1
            blocks, pos = read_sub_blocks(data, pos)

            if label == 0xF9 and blocks and len(blocks[0]) >= 4:      # graphic control
                flags, delay, _index = struct.unpack_from("<BHB", blocks[0])
                total_delay += delay
                if flags & 0x01:
                    transparent = True
            elif label == 0xFE:                                        # comment
                text = b"".join(blocks).decode("utf-8", errors="replace")
                comments.append(("Comment", shorten(text)))
            elif label == 0xFF and blocks and len(blocks[0]) >= 11:    # application
                name = blocks[0][:11].decode("latin-1")
                applications.append(name.strip())
                if name.startswith("NETSCAPE2.0") and len(blocks) > 1 \
                        and blocks[1][0] == 1 and len(blocks[1]) >= 3:
                    (loops,) = struct.unpack_from("<H", blocks[1], 1)

        elif block == 0x2C:                        # image descriptor (one frame)
            if pos + 9 > len(data):
                raise ValueError("truncated GIF image descriptor")
            frame_packed = data[pos + 8]
            pos += 9
            if frame_packed & 0x80:                # local color table
                pos += 3 * (2 << (frame_packed & 0x07))
            pos += 1                               # LZW minimum code size
            _, pos = read_sub_blocks(data, pos)
            frames += 1

        else:
            raise ValueError(f"unknown GIF block 0x{block:02X} at offset {pos - 1}")

    else:
        raise ValueError("GIF has no trailer (file may be truncated)")

    image = [
        ("Version", version),
        ("Dimensions", f"{width} x {height} pixels"),
        ("Global color table", f"{global_colors} colors" if has_global_table else "none"),
    ]
    if has_global_table:
        image.append(("Background color", f"index {background}"))
    if aspect:
        image.append(("Pixel aspect ratio", f"{(aspect + 15) / 64:.3f}"))
    image.append(("Frames", str(frames)))
    if frames > 1:
        image.append(("Total duration", f"{total_delay / 100:.2f} s"))
        if loops is not None:
            image.append(("Loops", "forever" if loops == 0 else str(loops)))
    if transparent:
        image.append(("Transparency", "yes"))
    for name in applications:
        image.append(("Application", name))

    sections = [("GIF image", image)]
    if comments:
        sections.append(("GIF comments", comments))
    return sections
