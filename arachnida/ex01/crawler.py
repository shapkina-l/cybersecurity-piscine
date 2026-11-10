from urllib.parse import urljoin, urlparse
from pathlib import Path

from downloader import download_page, download_image
from image_parser import ImageParser

EXTENSIONS = (".jpg", ".jpeg", ".png", ".gif", ".bmp")

def has_valid_extension(image_url):
    path = urlparse(image_url).path
    return Path(path).suffix.lower() in EXTENSIONS

def get_links(base_url, raw_links):
    links = []
    for link in raw_links:
    #todo

def scrape(url, output_dir):
    html = download_page(url)
    if html is None:
        return
    
    parser = ImageParser()
    parser.feed(html)

    images = parser.images

    for image in images:
        image_url = urljoin(url, image)
        if not has_valid_extension(image_url):
            continue
        download_image(image_url, output_dir)
