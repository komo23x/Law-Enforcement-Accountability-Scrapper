import bs4
from bs4 import BeautifulSoup
import requests
import re
import csv
from datetime import datetime

# Get search terms from searchTerms.txt file
list_of_search_terms = []
with open('searchTerms.txt') as f:
    list_of_search_terms = f.read().splitlines()

# Bing news limit's search results based on a code passed to
# qft=interval%3d"<Interval code>"
# intervals = {"5m": "1",
#              "15m": "2",
#              "30m": "3",
#              "1h": "4",
#              "4h": "5",
#              "6h": "6",
#              "1d": "7",
#              "1w": "8",
#              "30d": "9"}

url = 'https://www.bing.com/news/infinitescrollajax?q={0}&qft=interval%3d"7"&first={1}&infinitescroll=1'
compiled_urls = {}

# Run query for each search term
for search_word in list_of_search_terms:
    print("Searching for %s" % search_word)
    compiled_urls[search_word] = set()
    formatted_search_word = search_word.replace(" ", "+")
    new_articles = True
    first_index = 0

    # Iterate through each page of results. When we run out of pages,
    # the same last few articles will be returned. Exit when no new articles
    # exist on the page
    while new_articles:
        new_articles = False
        response = requests.get(url.format(formatted_search_word, first_index))
        soup = BeautifulSoup(response.text, 'html.parser')
        url_search_results = soup.find_all('a', href=True)

        bad_urls = ["javascript:", "/news/search?q=", "/rewards", "/images", "/videos", "/maps", "/shop", "/profile",
                "/search", "/?FORM"]

        for url_s in url_search_results:
            if ((not url_s['href'].startswith(tuple(bad_urls))) and
            ("go.microsoft.com" not in url_s['href']) and
            ("coronaviruslinks" not in url_s['href']) and
            (url_s['href'] not in compiled_urls[search_word]) and
            (url_s['href'] != "#")):
                # Keep going as long as we find new URLs
                new_articles = True
                compiled_urls[search_word].add(url_s['href'])
        first_index += 10

# Follow links under each search term. Do a best effort
# headline and article extraction
rows = []
for search_word in compiled_urls:
    urls = compiled_urls[search_word]
    for url in urls:
        print(url)
        # Retrieve page text
        try:
            page = requests.get(url, timeout=5).text
        except requests.exceptions.Timeout:
            # Timeout occurred
            print("\tRequest timed out")
            row = [search_word, url, "", ""]
            rows.append(row)
            break
        except:
            # Unknown error
            print("\tUnknown error, ignoring")
            break

        # Turn page into BeautifulSoup object to access HTML tags
        soup = BeautifulSoup(page, "html.parser")

        # Get headline
        if soup.find('h1') != None:
            headline = soup.find('h1').get_text().strip().rstrip()
        else:
            headline = ""
        print("\t" + headline.lstrip())

        # Get text from all <p> tags.
        p_tags = soup.find_all('p')
        # Get the text from each of the “p” tags and strip surrounding whitespace.
        if p_tags != None:
            p_tags_text = [tag.get_text().strip() for tag in p_tags]
        else:
            p_tags_text = ""

        # Filter out sentences that contain newline characters '\n' or don't contain periods.
        sentence_list = [sentence for sentence in p_tags_text if not '\n' in sentence]
        sentence_list = [sentence for sentence in sentence_list if '.' in sentence]

        # Combine list items into string.
        article = ' '.join(sentence_list)
        article.replace(',','').strip().rstrip()

        row = [search_word, url, headline, article]
        rows.append(row)

# Get a timestamp for the csv
timestamp = datetime.now()
fields = ["Search Term", "Source", "Title", "Article Content"]
#filename = timestamp.strftime("ws1_web_crawler_results_%Y-%m-%d_%H_%M_%S.csv")
filename = "ws1_web_crawler_results.csv" 

# Write out to csv
with open(filename, 'w', encoding='utf-8', newline='') as csvfile:
    csvwriter = csv.writer(csvfile)
    csvwriter.writerow(fields)
    csvwriter.writerows(rows)
