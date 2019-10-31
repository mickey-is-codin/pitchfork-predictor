import csv
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

csv_fname = "data/p4k_reviews.csv"

def main():

    print("\nCrawling Pitchfork for review scores\n\n")

    pages_2_scrape = 50

    make_csv_header()
    scrape_review_pages(pages_2_scrape)

def make_csv_header():

    csv_header_string = "artist,album,genre,review,lyrics,date,score\n"

    with open(csv_fname, "w") as csv_file:
        csv_file.write(csv_header_string)

def scrape_review_pages(pages_2_scrape):

    p4k_base = "https://pitchfork.com"
    review_page_base = "https://pitchfork.com/reviews/albums/"

    print("Scraping...")
    for page in range(1, pages_2_scrape):

        print(f"{review_page_base}?page={page}")
        page_url  = f"{review_page_base}?page={page}"
        page_html = requests.get(page_url).content
        page_soup = BeautifulSoup(page_html, "html.parser")

        page_review_divs = page_soup.findAll("div", {"class": "review"})
        for review_div in tqdm(page_review_divs):
            review_link = review_div.find("a", {"class": "review__link"})["href"]

            review_html = requests.get(p4k_base + review_link).content
            review_soup = BeautifulSoup(review_html, "html.parser")

            try:
                tombstone = review_soup.find("div", {"class": "single-album-tombstone"})

                artist = tombstone.find("li").find("a")
                album  = tombstone.find("h1", {"class": "single-album-tombstone__review-title"})
                score  = review_soup.find("span", {"class": "score"})
                publish_date = review_soup.find("time", {"class": "pub-date"})["datetime"]
                genre = review_soup.find("a", {"class": "genre-list__link"})
                review_p = review_soup.find("div", {"class": "contents dropcap"}).findAll("p")

                artist = artist.text
                album  = album.text
                score  = score.text
                genre  = genre.text

                publish_date = publish_date[0:10]

                review_text = ""
                for paragraph in review_p:
                    review_text += paragraph.text

                album_lyrics = get_album_lyrics(artist, album)

            except AttributeError as error:
                print("Error retriving info")
                next

            print(score)
            if "span" in score:
                score = score.text
            print(score)

            csv_info = [artist, album, genre, review_text, album_lyrics, publish_date, score]

            append_csv(csv_info)

def get_album_lyrics(artist, album):

    album_lyrics = ""

    url_artist = artist.replace(" ", "-").capitalize()
    url_album  = album.replace(" ", "-").capitalize()

    genius_album_url  = f"https://genius.com/albums/{url_artist}/{url_album}"
    genius_album_html = requests.get(genius_album_url).content

    album_page_soup = BeautifulSoup(genius_album_html, "html.parser")

    track_rows = album_page_soup.findAll("div", {"class": "chart_row-content"})
    for row in track_rows:
        song_link = row.find("a", {"class": "u-display_block"})["href"]
        song_html = requests.get(song_link).content
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

def append_csv(csv_info):

    csv_writer = csv.writer(open(csv_fname, "a"))
    csv_writer.writerow(csv_info)

if __name__ == "__main__":
    main()
