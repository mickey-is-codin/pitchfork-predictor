import time
import grequests
import multiprocessing
import itertools

import pitchfork

import numpy as np
import pandas as pd

from bs4 import BeautifulSoup
from bs4 import element
from tqdm import tqdm

csv_fname = "data/p4k_reviews.csv"

p4k_base = "https://pitchfork.com"
review_base = "https://pitchfork.com/reviews/albums/"
page_base = "https://pitchfork.com/reviews/albums/?page={}"
lyrics_base = "https://genius.com/albums/{}/{}"

cols = [ "artist", "album", "genre", "review", "lyrics", "date", "score"]
review_df = pd.DataFrame(columns=cols)

def main():

    start_time = time.time()

    max_pages = 1813
    desired_pages = 5

    # Get list of page urls of the form https://pitchfork.com/reviews/albums/?page={}
    page_nums = [np.random.randint(1, max_pages) for x in range(desired_pages)]
    page_urls = [page_base.format(x) for x in page_nums]

    # Make concurrent requests to all page urls
    page_requests  = (grequests.get(u) for u in page_urls)
    page_responses = grequests.map(page_requests)

    # Goal is to get a list with desired_pages elements. Each element is a dict for
    # all of the album reviews on that page
    with multiprocessing.Pool() as p:
        artist_album_list = p.map(get_page_albums, page_responses)

    for page in artist_album_list:

        with multiprocessing.Pool() as p:
            scores = p.map(get_api_info, page)

    print(len(scores))
    print(scores)

    print(f"Program executed in {time.time() - start_time} seconds")

def get_api_info(review_dict):

    print(review_dict["artist"], review_dict["album"])
    try:
        p = pitchfork.search(review_dict["artist"], review_dict["album"])
    except IndexError as e:
        return None

    return p.score()

def get_page_albums(page_response):

    page_review_info = []
    page_soup = BeautifulSoup(page_response.content, "html.parser")

    artist_tags = page_soup.findAll("ul", {"class": "artist-list review__title-artist"})
    album_tags  = page_soup.findAll("h2", {"class": "review__title-album"})

    for tag_ix in range(len(artist_tags)):
        page_review_info.append({
            "artist": artist_tags[tag_ix].text,
            "album": album_tags[tag_ix].text
        })

    return page_review_info

if __name__ == "__main__":
    main()
