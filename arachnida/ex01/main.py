import argparse

from crawler import scrape

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("url")
    parser.add_argument("-r", action="store_true")
    parser.add_argument("-l", type=int, default=5)
    parser.add_argument("-p", default="./data/")

    args = parser.parse_args()

    visited = set()

    scrape(args.url, args.p)
    

if __name__ == "__main__":
    main()





# visited = set()

# main(url, level):
#     if level < 1:
#         return

#     if url not in visited:
#         visited.add(url)
#         scrape
#     else: 
#         return

#     if level == 1:
#         return
        
#     extract all links from current page

#     for each link:
#         scrape(link, level - 1)