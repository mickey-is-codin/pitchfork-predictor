import csv
import requests
from bs4 import BeautifulSoup

csv_fname = "data/p4k_reviews.csv"

def main():

    print("\nCrawling Pitchfork for review scores\n\n")

    pages_2_scrape = 10

    make_csv_header()
    scrape_review_pages(pages_2_scrape)

def make_csv_header():

    csv_header_string = "date, album, artist, review_content, album_lyrics, score\n"

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

        # Looking for links with class "review__link"
        page_review_divs = page_soup.findAll("div", {"class": "review"})
        for review_div in page_review_divs:
            review_link = review_div.find("a", {"class": "review__link"})["href"]

            review_html = requests.get(p4k_base + review_link).content
            review_soup = BeautifulSoup(review_html, "html.parser")

            tombstone = review_soup.find("div", {"class": "single-album-tombstone"})

            artist = tombstone.find("li").find("a")
            album  = tombstone.find("h1", {"class": "single-album-tombstone__review-title"})
            score  = review_soup.find("span", {"class": "score"})

            publish_date = review_soup.find("time", {"class": "pub-date"})["datetime"]

            genre = review_soup.find("a", {"class": "genre-list__link"})

            review_p = review_soup.find("div", {"class": "contents dropcap"}).findAll("p")

            if  (
                    artist       == None or
                    album        == None or
                    score        == None or
                    publish_date == None or
                    review_p     == None
                ):
                next
            else:
                artist = artist.text
                album  = album.text
                score  = score.text
                publish_date = publish_date[0:10]
                review_text = ""
                for paragraph in review_p:
                    review_text += paragraph.text

            # print(
            #     f"Artist: {artist}, \n"
            #     f"Album: {album}, \n"
            #     f"Genre: {genre}, \n"
            #     f"Score: {score}, \n"
            #     f"Date: {publish_date}"
            # )

            csv_info = [artist, album, genre, review_text, publish_date, score]

            append_csv(csv_info)

def append_csv(csv_info):

    csv_writer = csv.writer(open(csv_fname, "a"))
    csv_writer.writerow(csv_info)

if __name__ == "__main__":
    main()
