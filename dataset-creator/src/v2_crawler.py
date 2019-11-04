import time
import grequests
import multiprocessing
import itertools

import numpy as np
import pandas as pd

from bs4 import BeautifulSoup
from bs4 import element
from tqdm import tqdm

import resource
resource.setrlimit(resource.RLIMIT_NOFILE, (110000, 110000))

csv_fname = "data/p4k_reviews.csv"

review_base = "https://pitchfork.com/reviews/albums/"
page_base = "https://pitchfork.com/reviews/albums/?page={}"
genius_base = "https://genius.com/albums/{}/{}"

cols = [ "artist", "album", "genre", "label", "review", "date", "score"]
review_df = pd.DataFrame(columns=cols)

def main():

    start_time = time.time()

    max_pages = 1813
    desired_pages = 100

    print(f"scraping {desired_pages} pages of reviews")

    # Get list of page urls of the form https://pitchfork.com/reviews/albums/?page={}
    #page_nums = [np.random.randint(1, max_pages) for x in range(desired_pages)]
    page_nums = range(1, desired_pages+1)
    page_urls = [page_base.format(x) for x in page_nums]

    # Make concurrent requests to all page urls
    page_requests  = (grequests.get(u) for u in page_urls)
    page_responses = grequests.map(page_requests)

    # From each "page" webpage, scrape the page and pull out all of the review links
    print("getting review urls...")
    with multiprocessing.Pool() as p:
        review_urls = p.map(get_review_urls, page_responses)

    # Get list of review urls
    review_urls = list(itertools.chain.from_iterable(review_urls))

    print(f"found {len(review_urls)} review urls")

    # Make recurrent requests to all review urls
    review_requests  = (grequests.get(u) for u in review_urls)
    review_responses = grequests.map(review_requests)

    # From each "review" webpage, scrape the review information and return a dict
    print("getting review attributes...")
    with multiprocessing.Pool() as p:
        review_info_list = p.map(scrape_review, review_responses)

    print("saving to csv...")
    global review_df
    for review_dict in review_info_list:
        review_df = review_df.append(review_dict, ignore_index=True)
    review_df.to_csv(csv_fname, index=False)

    print("finished execution in %.2f seconds" % (time.time() - start_time))

def scrape_review(review_response):

    review_soup = BeautifulSoup(review_response.content, "html.parser")

    tombstone = review_soup.find("div", {"class": "single-album-tombstone"})

    artist = tombstone.find("ul", {
        "class": "artist-links artist-list single-album-tombstone__artist-links"
    })
    album  = tombstone.find("h1", {"class": "single-album-tombstone__review-title"})
    score  = review_soup.find("span", {"class": "score"})
    publish_date = review_soup.find("time", {"class": "pub-date"})["datetime"]
    genre = review_soup.find("a", {"class": "genre-list__link"})
    label = review_soup.find("li", {"class": "labels-list__item"})
    review_p = review_soup.find("div", {"class": "contents dropcap"}).findAll("p")

    publish_date = publish_date[0:10]

    review_text = "".join(paragraph.text for paragraph in review_p)

    csv_info = {
        "artist": artist,
        "album": album,
        "genre": genre,
        "label": label,
        "review": review_text,
        "date": publish_date,
        "score": score
    }

    for k, v in csv_info.items():
        if isinstance(v, element.Tag):
            csv_info[k] = v.text

    return csv_info

def get_review_urls(page_response):

    p4k_base = "https://pitchfork.com"

    page_soup = BeautifulSoup(page_response.content, "html.parser")

    page_review_divs = page_soup.findAll("div", {"class": "review"})
    review_urls = [
        p4k_base + x.find("a", {"class": "review__link"})["href"] \
        for x in page_review_divs
    ]

    return review_urls

if __name__ == "__main__":
    main()
