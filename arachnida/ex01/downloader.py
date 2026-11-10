import urllib.request
import urllib.error

from urllib.request import urlopen
from urllib.parse import urlparse, unquote
from pathlib import Path

def download_page(url):
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            html = response.read().decode("utf-8")
            return html
    except urllib.error.URLError as error:
        print(f"Error downloading {url}: {error}")
        return None

def download_image(image_url, output_dir):
    filename = Path(unquote(urlparse(image_url).path)).name

    if not filename:
        print(f"Could not determine filename: {image_url}")
        return

    Path(output_dir).mkdir(parents=True, exist_ok=True)

    filepath = Path(output_dir) / filename

    try:
        with urlopen(image_url, timeout=10) as response:
            image_data = response.read()
        with open(filepath, "wb") as file:
            file.write(image_data)
        print(f"Downloaded: {filepath}")

    except Exception as error:
        print(f"Failed to download {image_url}: {error}")