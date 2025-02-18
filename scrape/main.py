import json
import time

from tqdm import tqdm

import requests
from bs4 import BeautifulSoup

from os import environ

import getpass

AO3STATS_STOP_AFTER = environ.get('AO3STATS_STOP_AFTER')
if AO3STATS_STOP_AFTER is not None:
    print(f"Stopping once a date matches {AO3STATS_STOP_AFTER}")

VERBOSE = 'VERBOSE' in environ.keys()
def verbose(*args) -> None:
    """Print the specified args only if $VERBOSE is set."""

    if VERBOSE:
        print("verbose:", *args)

USERNAME = environ['USERNAME'] if 'USERNAME' in environ.keys() else input("Username? ")
PASSWORD = environ['PASSWORD'] if 'PASSWORD' in environ.keys() else getpass.getpass("Password? ")

verbose("Logging in to AO3")

s = requests.Session()
s.headers['User-Agent'] = "historybot/0.1.0"  # AO3 requests that we include this string in our user agent

def retry_after(r, *args, **kwargs):
    if r.status_code == 429:
        verbose("HTTP 429 Too Many Requests")
        delay = int(r.headers['Retry-After'])
        verbose(f"Sleeping {delay} seconds")
        time.sleep(delay)
        verbose("Retrying request")
        return s.send(r.request)
    elif r.status_code == 502:
        verbose("HTTP 502 Bad Gateway")
        if hasattr(r.request, 'fivezerotwo_backoff'):
            verbose(f"Request has `fivezerotwo_backoff` property with value {r.request.fivezerotwo_backoff}")
            verbose("Doubling backoff")
            r.request.fivezerotwo_backoff *= 2
            if r.request.fivezerotwo_backoff > 65:
                verbose(f"Backoff is {r.request.fivezerotwo_backoff}, which is too long; failing")
                return
            verbose(f"Sleeping for {r.request.fivezerotwo_backoff}")
            time.sleep(r.request.fivezerotwo_backoff)
            verbose("Retrying request")
            return s.send(r.request)
        else:
            verbose("Request does not have `fivezerotwo_backoff` property")
            r.request.fivezerotwo_backoff = 1
            verbose(f"Setting backoff to {r.request.fivezerotwo_backoff}s and sleeping")
            time.sleep(r.request.fivezerotwo_backoff)
            verbose("Retrying request")
            return s.send(r.request)

s.hooks['response'].append(retry_after)

# -- STOLEN FROM https://github.com/JimmXinu/FanFicFare/blob/5c703122ec9d9e028b47582b32c1c384222e0978/fanficfare/adapters/base_otw_adapter.py#L103-L130
params = {}
params['user[login]'] = USERNAME
params['user[password]'] = PASSWORD
params['user[remember_me]'] = '1'
params['commit'] = 'Log in'
params['utf8'] = u'\x2713'  # utf8 *is* required now.  hex code works better than actual character for some reason. u'✓'

# authenticity_token now comes from a completely separate json call.
token_json = json.loads(s.get("https://archiveofourown.org/token_dispenser.json").text)
params['authenticity_token'] = token_json['token']

resp = s.post('https://archiveofourown.org/users/login', params=params)

if 'href="/users/logout"' not in resp.text:
    print("Failed to log in. Check your username/password")
    exit(1)
# --- end of stolen code

verbose(f"Fetching history page for {USERNAME}")

resp = s.get(f"https://archiveofourown.org/users/{USERNAME}/readings")
soup = BeautifulSoup(resp.text, features='html.parser')

# last_page = soup.find(id='main').
last_page = soup.select_one("#main > ol.pagination > li:nth-last-child(2) > a")
last_page = int(last_page.text)

verbose(f"Detected {last_page} pages in history")

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

def process_page(page) -> bool:
    global deleted_works
    page_works = soup.select("#main > ol.reading > li.work")
    for work in page_works:
        w = process_work(work)
        if w is None:
            deleted_works += 1
        else:
            if AO3STATS_STOP_AFTER is not None:
                if AO3STATS_STOP_AFTER in w.last_visit:
                    verbose("Hit stop date; stopping page")
                    return True
            works.append(w)
    return False

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
    # should look like ['Last visited: 24 Oct 2024', '(Latest version.)', 'Visited once']
    visit_info_lines = [x for x in (y.strip() for y in visit_info.text.split('\n')) if x != '']
    match len(visit_info_lines):
        case 1:
            if '(Deleted work,' in visit_info_lines[0]:
                # This is a deleted work
                return None
            else:
                breakpoint()
        case 3:
            # normal
            pass
        case 4:
            if visit_info_lines[3] == "(Marked for Later.)":
                marked_for_later = True
            else:
                breakpoint()
        case _:
            breakpoint()

    visits = visit_info_lines[2]  # should look like "Visited 2 times"

    if "once" in visits:
        view_count = 1
    else:
        try:
            view_count = int(visits.split(' ')[1])
        except ValueError:
            # should never happen
            breakpoint()

    last_visit = visit_info_lines[0][14:]
    changes_since_last_view = visit_info_lines[1][1:-1]

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

verbose("Processing page 1")
if not process_page(soup):
    if VERBOSE:
        for i in range(2, last_page + 1):
            verbose(f"Processing page {i}")
            resp = s.get(f"https://archiveofourown.org/users/{USERNAME}/readings?page={i}")
            soup = BeautifulSoup(resp.text, features='html.parser')
            if process_page(soup):
                verbose("page stopped; breaking out of loop")
                break
    else:
        for i in tqdm(range(2, last_page + 1), desc="Processing pages"):
            resp = s.get(f"https://archiveofourown.org/users/{USERNAME}/readings?page={i}")
            soup = BeautifulSoup(resp.text, features='html.parser')
            if process_page(soup):
                verbose("page stopped; breaking out of loop")
                break

print(f"{deleted_works} deleted work(s)")

# while True:
#     eval(input("> "))

# print(json.dumps([work.__dict__ for work in works], indent=4))

with open("works.json", "w") as file:
    json.dump([work.__dict__ for work in works], file, indent=4)
with open("deleted-works.txt", "w") as file:
    file.write(f"{deleted_works} deleted work(s)\n")

# Word count: `li.work > dl.stats > dd.words` (must parse to int)
# author: `li.work > div.header.module > h4.heading > a[rel="author"]` (str, optionally ensure href does not have gift)
# fic name: `li.work > div.header.module > h4.heading > a[href^="/works/"]` (str)
# giftee(s?): `li.work > div.header.module > h4.heading > a[href$="/gifts"]` (str)
# my first page loop and second page loop are almost identical. revise 1st page loop to actually loop over work elements, not hardcoded 1...20
# rating: `li.work > div.header.module > ul.required-tags > li:first-child > a > span.rating`
# rating: `li.work > div.header.module > ul.required-tags span.rating`
# chapters: `li.work > dl.stats > dd.chapters` (can contain link)
