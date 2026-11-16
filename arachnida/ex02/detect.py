SIGNATURES = {
    "jpeg": (b"\xff\xd8\xff",),
    "png": (b"\x89PNG\r\n\x1a\n",),
    "gif": (b"GIF87a", b"GIF89a"),
    "bmp": (b"BM",),
}

EXTENSIONS = {
    "jpeg": (".jpg", ".jpeg"),
    "png": (".png",),
    "gif": (".gif",),
    "bmp": (".bmp",),
}

def detect_format(path):
    with open(path, "rb") as f:
        header = f.read(8)
    for name, magics in SIGNATURES.items():
        if header.startswith(magics):
            return name
    return None
    
def extension_matches(path, fmt):
    return path.lower().endswith(EXTENSIONS[fmt])