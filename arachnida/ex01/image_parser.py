from html.parser import HTMLParser

class ImageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.images = []
    
    def handle_starttag(self, tag, attrs):
        if tag == "img":
            for attr, value in attrs:
                if attr == "src":
                    self.images.append(value)
        elif tag == "a"
            for attr, value in attrs:
                if attr == "href" and value:
                    self.links.append(value)
