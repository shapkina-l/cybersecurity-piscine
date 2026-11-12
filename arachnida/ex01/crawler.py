from urllib.parse import urljoin, urlparse, urldefrag
from pathlib import Path

from downloader import download_page, download_image
from parser import Parser

EXTENSIONS = (".jpg", ".jpeg", ".png", ".gif", ".bmp")

def has_valid_extension(image_url):
    path = urlparse(image_url).path
    return Path(path).suffix.lower() in EXTENSIONS

def is_same_site(url, start_url):
    return urlparse(url).netloc.lower() == urlparse(start_url).netloc.lower()

def get_links(base_url, raw_links):
    links = []
    for link in raw_links:
        absolute = urljoin(base_url, link)
        absolute, _ = urldefrag(absolute)
        if (urlparse(absolute).scheme in ("http", "https")
                and is_same_site(absolute, base_url)
                and absolute not in links):
            links.append(absolute)
    return links

def scrape(url, output_dir, downloaded):
    html = download_page(url)
    if html is None:
        return []
    
    parser = Parser()
    parser.feed(html)

    images = parser.images

    for image in images:
        image_url = urljoin(url, image)
        if not has_valid_extension(image_url) or image_url in downloaded:
            continue
        downloaded.add(image_url)
        download_image(image_url, output_dir)
    
    return get_links(url, parser.links)

def crawl(url, level, output_dir, visited, downloaded):
    if level < 1 or url in visited:
        return
    visited.add(url)

    links = scrape(url, output_dir, downloaded)

    if level == 1:
        return
    
    for link in links:
        crawl(link, level - 1, output_dir, visited, downloaded)
