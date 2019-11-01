import time
import requests
import multiprocessing

import numpy as np
import pandas as pd

from bs4 import BeautifulSoup
from bs4 import element
from tqdm import tqdm

csv_fname = "data/p4k_reviews.csv"

def main():

    prog_start = time.time()

    max_pages = 1813
    num_pages = 1

    print(f"\nRetrieving review data from {num_pages} page(s) of Pitchfork scores\n\n")

    pages_2_scrape = [np.random.randint(1, max_pages) for x in range(num_pages)]

    review_df = scrape_review_pages(pages_2_scrape)

    review_df.to_csv("data/p4k_reviews.csv")

    prog_end = time.time()
    print(f"Program executed in {prog_end - prog_start} seconds")

def scrape_review_pages(pages_2_scrape):

    cols = [
        "artist",
        "album",
        "genre",
        "review",
        "lyrics",
        "date",
        "score"
    ]
    review_df = pd.DataFrame(columns=cols)

    p4k_base = "https://pitchfork.com"
    review_page_base = "https://pitchfork.com/reviews/albums/"

    num_reviews = 0
    print("Scraping...")

    for page in pages_2_scrape:

        print(f"{review_page_base}?page={page}")

        page_url  = f"{review_page_base}?page={page}"
        page_html = requests.get(page_url).text
        page_soup = BeautifulSoup(page_html, "html.parser")

        review_links = get_review_links(page_soup)
        for review_link in review_links:

            review_info = get_review_info(p4k_base, review_link)

            if review_info is None:
                print("Error getting review info")
                continue

            review_info["lyrics"] = get_album_lyrics(
                review_info["artist"],
                review_info["album"]
            )

            review_df = review_df.append(review_info, ignore_index=True)

            num_reviews += 1
            print(f"Retrieved {num_reviews} reviews")

    return review_df

def get_review_links(page_soup):

    review_links = []

    page_review_divs = page_soup.findAll("div", {"class": "review"})
    for review_div in page_review_divs:
        review_links.append(review_div.find("a", {"class": "review__link"})["href"])

    return review_links

def get_review_info(p4k_base, review_link):

    review_html = requests.get(p4k_base + review_link).text
    review_soup = BeautifulSoup(review_html, "html.parser")

    tombstone = review_soup.find("div", {"class": "single-album-tombstone"})

    artist = tombstone.find("li").find("a")
    album  = tombstone.find("h1", {"class": "single-album-tombstone__review-title"})
    score  = review_soup.find("span", {"class": "score"})
    publish_date = review_soup.find("time", {"class": "pub-date"})["datetime"]
    genre = review_soup.find("a", {"class": "genre-list__link"})
    review_p = review_soup.find("div", {"class": "contents dropcap"}).findAll("p")

    publish_date = publish_date[0:10]

    review_text = ""
    for paragraph in review_p:
        review_text += paragraph.text

    csv_info = {
        "artist": artist,
        "album": album,
        "genre": genre,
        "review": review_text,
        "lyrics": None,
        "date": publish_date,
        "score": score
    }

    if csv_info["artist"] is None:
        return None

    if csv_info["album"] is None:
        return None

    if csv_info["genre"] is None:
        return None

    if csv_info["date"] is None:
        return None

    if csv_info["score"] is None:
        return None

    for k, v in csv_info.items():
        if isinstance(v, element.Tag):
            csv_info[k] = v.text

    return csv_info

def get_album_lyrics(artist, album):

    album_lyrics = ""

    url_artist = artist.replace(" ", "-").capitalize()
    url_album  = album.replace(" ", "-").capitalize()

    genius_album_url  = f"https://genius.com/albums/{url_artist}/{url_album}"
    genius_album_html = requests.get(genius_album_url).text

    album_page_soup = BeautifulSoup(genius_album_html, "html.parser")

    track_rows = album_page_soup.findAll("div", {"class": "chart_row-content"})
    for row in track_rows:
        song_link = row.find("a", {"class": "u-display_block"})["href"]
        song_html = requests.get(song_link).text
        song_soup = BeautifulSoup(song_html, "html.parser")

        lyrics_div = song_soup.find("div", {"class": "lyrics"})

        if (lyrics_div == None):
            return None
        else:
            lyrics_p = lyrics_div.find("p")

            if lyrics_p == None:
                return None
            else:
                lyrics_p = lyrics_p.text

        album_lyrics += lyrics_p

    return album_lyrics

if __name__ == "__main__":
    main()
