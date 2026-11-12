import argparse

from crawler import crawl

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("url")
    parser.add_argument("-r", action="store_true")
    parser.add_argument("-l", type=int, default=5)
    parser.add_argument("-p", default="./data/")

    args = parser.parse_args()

    visited = set()
    downloaded = set()

    level = args.l if args.r else 1
    crawl(args.url, level, args.p, visited, downloaded)
    
if __name__ == "__main__":
    main()
