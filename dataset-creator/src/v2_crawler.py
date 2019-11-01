import time
import requests
import multiprocessing
import itertools

import numpy as np
import pandas as pd

from bs4 import BeautifulSoup
from bs4 import element
from tqdm import tqdm

csv_fname = "data/p4k_reviews.csv"

cols = [ "artist", "album", "genre", "review", "lyrics", "date", "score"]
review_df = pd.DataFrame(columns=cols)

def main():

    start_time = time.time()

    review_base = "https://pitchfork.com/reviews/albums/"
    page_base = "https://pitchfork.com/reviews/albums/?page={}"

    max_pages = 1813
    desired_pages = 10

    page_nums = [np.random.randint(1, max_pages) for x in range(desired_pages)]
    page_urls = [page_base.format(x) for x in page_nums]

    # No multi
    # for page_url in tqdm(page_urls):
    #    review_links = get_review_links(page_url)

    # Multi
    with multiprocessing.Pool() as p:
        review_links = p.map(get_review_links, page_urls)
    review_links = list(itertools.chain.from_iterable(review_links))

    print(f"Found {len(review_links)} links for reviews")

    # No multi
    # for link in tqdm(review_links):
    #     scrape_review(link)

    # Multi
    with multiprocessing.Pool() as p:
        p.map(scrape_review, review_links)

    #review_df.to_csv(csv_fname)
    print(f"Program executed in {time.time() - start_time} seconds")

def scrape_review(review_url):

    global review_df

    review_soup = BeautifulSoup(requests.get(review_url).content, "html.parser")

    tombstone = review_soup.find("div", {"class": "single-album-tombstone"})

    artist = tombstone.find("li").find("a")
    album  = tombstone.find("h1", {"class": "single-album-tombstone__review-title"})
    score  = review_soup.find("span", {"class": "score"})
    publish_date = review_soup.find("time", {"class": "pub-date"})["datetime"]
    genre = review_soup.find("a", {"class": "genre-list__link"})
    review_p = review_soup.find("div", {"class": "contents dropcap"}).findAll("p")



def get_review_links(page_url):

    p4k_base = "https://pitchfork.com"

    page_soup = BeautifulSoup(requests.get(page_url).content, "html.parser")
    page_review_divs = page_soup.findAll("div", {"class": "review"})
    review_links = [p4k_base + x.find("a", {"class": "review__link"})["href"] for x in page_review_divs]

    return review_links

if __name__ == "__main__":
    main()
