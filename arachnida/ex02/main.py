import os
import sys

import jpeg
from attributes import get_basic_attributes
from detect import detect_format, extension_matches
from output import print_section

PARSERS = {
    "jpeg": jpeg.parse,
}

SUPPORTED_EXTENSIONS = (".jpg", ".jpeg", ".png", ".gif", ".bmp")

def print_usage():
    print("Usage: ./scorpion FILE1 [FILE2 ...]", file=sys.stderr)

def check_file(path):
    if not os.path.exists(path):
        return "no such file"
    if not os.path.isfile(path):
        return "not a regular file"
    if not os.access(path, os.R_OK):
        return "permission denied"
    if not path.lower().endswith(SUPPORTED_EXTENSIONS):
        return "unsupported extension (expected jpg, jpeg, png, gif, bmp)"
    return None

def process_file(path):
    """Print the metadata of one file."""
    fmt = detect_format(path)
    if fmt is None:
        raise ValueError("not a supported image (expected jpeg, png, gif, bmp)")

    print(f"=== {path} ===")
    attrs = get_basic_attributes(path)
    attrs.append(("Format", fmt.upper()))
    if not extension_matches(path, fmt):
        attrs.append(("Warning", "extension does not match the real format"))
    print_section("File attributes", attrs)

    parser = PARSERS.get(fmt)
    if parser:
        for title, items in parser(path):
            print_section(title, items)
    print()

def main(argv):
    files = argv[1:]
    if not files:
        print_usage()
        return 1
    
    exit_code = 0
    for path in files:
        error = check_file(path)
        if error:
            print(f"scorpion: {path}: {error}", file=sys.stderr)
            exit_code = 1
            continue
        try:    
            process_file(path)
        except Exception as exc:
            print(f"scorpion: {path}: {exc}", file=sys.stderr)
            exit_code = 1
    return exit_code  


if __name__ == "__main__":
    sys.exit(main(sys.argv))
