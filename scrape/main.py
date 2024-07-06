import json
import time

from tqdm import tqdm

import requests
from bs4 import BeautifulSoup

USERNAME = input("Username? ")
PASSWORD = input("Password? ")

s = requests.Session()

resp = s.get('https://archiveofourown.org')
soup = BeautifulSoup(resp.text, features='html.parser')

authenticity_token = soup.find('input', {'name': 'authenticity_token'})['value']

resp = s.post('https://archiveofourown.org/users/login', params={
    'authenticity_token': authenticity_token,
    'user[login]': USERNAME,
    'user[password]': PASSWORD
})

soup = BeautifulSoup(resp.text, features='html.parser')

print(soup.body['class'])

if 'logged-out' in soup.body['class']:
    print("Login failure; trying again with same creds (this happens sometimes)")
    authenticity_token = soup.find('input', {'name': 'authenticity_token'})['value']
    resp = s.post('https://archiveofourown.org/users/login', params={
        'authenticity_token': authenticity_token,
        'user[login]': USERNAME,
        'user[password]': PASSWORD
    })
    soup = BeautifulSoup(resp.text, features='html.parser')

if 'logged-in' not in soup.body['class']:
    print("Failed to log in. Check your username/password")
    exit(0)

resp = s.get(f"https://archiveofourown.org/users/{USERNAME}/readings")
soup = BeautifulSoup(resp.text, features='html.parser')

# last_page = soup.find(id='main').
last_page = soup.select_one("#main > ol.pagination > li:nth-last-child(2) > a")
last_page = int(last_page.text)

print(f"Number of pages in history: {last_page}")

works = []
deleted_works = 0

class Work:
    def __init__(self,
                 work_id: str,
                 title: str,
                 authors: list[str],
                 giftees: list[str],
                 fandoms: list[str],
                 series: dict[str, int],
                 word_count: int,
                 view_count: int,
                 marked_for_later: bool,
                 last_visit: str,
                 most_recent_update: str,
                 changes_since_last_view: str,
                 rating: str,
                 chapters: str,
                 complete: bool,
                 relationships: list[str],
                 characters: list[str],
                 tags: list[str]):
        self.work_id = work_id
        self.title = title
        self.authors = authors
        self.giftees = giftees
        self.fandoms = fandoms
        self.series = series
        self.word_count = word_count
        self.view_count = view_count
        self.marked_for_later = marked_for_later
        self.last_visit = last_visit
        self.most_recent_update = most_recent_update
        self.changes_since_last_view = changes_since_last_view
        self.rating = rating
        self.chapters = chapters
        self.complete = complete
        self.relationships = relationships
        self.characters = characters
        self.tags = tags

def process_page(page):
    global deleted_works
    while True:
        if page.select_one("#main ol.reading") is not None:
            break
        else:
            print(resp.headers['Retry-after'])
            breakpoint()
            # print("Could not fetch page; presumably we are rate-limited")
            # print("Sleeping for 5 minutes")
            time.sleep(5 * 60)
            resp = s.get(resp.url)
            page = BeautifulSoup(resp.text, features='html.parser')
            continue
    page_works = soup.select("#main > ol.reading > li.work")
    for work in tqdm(page_works, desc="Processing works on page", leave=False):
        w = process_work(work)
        if w is None:
            deleted_works += 1
        else:
            works.append(w)

def process_work(work) -> Work | None:
    work_id = ""
    title = ""
    authors = []
    giftees = []
    fandoms = []
    rating = ""
    word_count = 0
    view_count = 0
    chapters = 0
    last_visit = ""
    most_recent_update = ""
    changes_since_last_view = ""
    marked_for_later = False
    complete = False
    relationships = []
    characters = []
    tags = []

    visit_info = work.select_one("h4.viewed.heading")
    visit_info_lines = visit_info.text.split('\n')
    if len(visit_info_lines) == 3 and '(Deleted work,' in visit_info_lines[1]:
        # This is a deleted work
        return None

    if "(Marked for Later.)" in visit_info.text:
        marked_for_later = True

    visits = visit_info_lines[-3 if marked_for_later else -2]  # should look like "Visited 2 times"

    if "once" in visits:
        view_count = 1
    else:
        try:
            view_count = int(visits.split(' ')[1])
        except ValueError:
            # should never happen
            breakpoint()

    last_visit = visit_info_lines[1][14:]
    changes_since_last_view = visit_info_lines[2][1:-1]

    work_id = work['id'].split('_')[1]

    _authors = work.select("div.header.module > h4.heading > a[rel=\"author\"]")
    if len(_authors) == 0:
        authors = []
    else:
        authors = [aut.text for aut in _authors]

    try:
        title = work.select_one("div.header.module > h4.heading > a[href^=\"/works/\"]").text
    except AttributeError:
        # generally this means the fic has been moved to a hidden collection
        return None
    except:
        # unknown error but we should figure out what it is anyway
        breakpoint()
        return None

    _giftees = work.select("div.header.module > h4.heading > a[href$=\"/gifts\"]")
    giftees = [g.text for g in _giftees]

    _fandoms = work.select("div.header.module > h5.fandoms.heading > a[href^=\"/tags/\"]")
    fandoms = [fd.text for fd in _fandoms]

    _rating = work.select_one("div.header.module > ul.required-tags span.rating")
    rating = _rating['title']

    complete = "complete-yes" in work.select_one("div.header.module > ul.required-tags span.iswip")['class']

    relationships = [x.text for x in work.select("ul.tags.commas > li.relationships")]
    characters = [x.text for x in work.select("ul.tags.commas > li.characters")]
    tags = [x.text for x in work.select("ul.tags.commas > li.freeforms")]

    _wc = work.select_one("dl.stats > dd.words").text
    if _wc == "":
        word_count = 0
        print(f"ERROR: no word count for fic '{title}'")
    else:
        word_count = int(_wc.replace(",", ""))

    chapters = work.select_one("dl.stats > dd.chapters").text

    series = {}
    series_elements = work.select("ul.series > li")
    # print(series_elements)
    # print([x.text for x in series_elements])
    for series_element in series_elements:
        _number = series_element.select_one("strong").text
        number = int(_number.replace(",", ""))
        name = series_element.select_one("a").text
        series[name] = number
        # print(_number)
        # print(number)
        # print(name)

    # print(series)

    most_recent_update = work.select_one("div.header.module > p.datetime").text

    current_work = Work(work_id, title, authors, giftees, fandoms, series, word_count, view_count, marked_for_later, last_visit, most_recent_update, changes_since_last_view, rating, chapters, complete, relationships, characters, tags)
    return current_work

process_page(soup)

for i in tqdm(range(2, last_page + 1), desc="Processing pages"):
    resp = s.get(f"https://archiveofourown.org/users/{USERNAME}/readings?page={i}")
    soup = BeautifulSoup(resp.text, features='html.parser')
    process_page(soup)

print(f"{deleted_works} deleted work(s)")

# while True:
#     eval(input("> "))

# print(json.dumps([work.__dict__ for work in works], indent=4))

with open("works.json", "w") as file:
    json.dump([work.__dict__ for work in works], file, indent=4)

# Word count: `li.work > dl.stats > dd.words` (must parse to int)
# author: `li.work > div.header.module > h4.heading > a[rel="author"]` (str, optionally ensure href does not have gift)
# fic name: `li.work > div.header.module > h4.heading > a[href^="/works/"]` (str)
# giftee(s?): `li.work > div.header.module > h4.heading > a[href$="/gifts"]` (str)
# my first page loop and second page loop are almost identical. revise 1st page loop to actually loop over work elements, not hardcoded 1...20
# rating: `li.work > div.header.module > ul.required-tags > li:first-child > a > span.rating`
# rating: `li.work > div.header.module > ul.required-tags span.rating`
# chapters: `li.work > dl.stats > dd.chapters` (can contain link)
