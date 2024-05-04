import json
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException

from tqdm import tqdm
# import itertools

usr = input("Username? ")

driver = webdriver.Firefox()

driver.get("https://archiveofourown.org")

# cb = WebDriverWait(driver, timeout=10).until(lambda d: d.find_element(By.ID, "tos_agree"))
# cb.click()
#
# btn = WebDriverWait(driver, timeout=3).until(lambda d: d.find_element(By.CSS_SELECTOR, "#accept_tos:not([disabled])"))
# btn.click()

input("Please sign in, then press Enter")

driver.get(f"https://archiveofourown.org/users/{usr}/readings")

WebDriverWait(driver, timeout=3).until(lambda d: d.find_element(By.CSS_SELECTOR, "#main ol.pagination"))
last_page = driver.find_element(By.CSS_SELECTOR, f"#main > ol.pagination > li:nth-last-child(2) > a")

last_page = int(last_page.text)
# last_page = int(input("Number of pages in history? "))
# print(last_page)

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

def process_page():
    global deleted_works
    while True:
        try:
            WebDriverWait(driver, timeout=3).until(lambda d: d.find_element(By.CSS_SELECTOR, "#main ol.reading"))
            break
        except:
            # print("Could not fetch page; presumably we are rate-limited")
            # print("Sleeping for 5 minutes")
            time.sleep(5 * 60)
            driver.refresh()
            continue
    page_works = driver.find_elements(By.CSS_SELECTOR, f"#main > ol.reading > li.work")
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

    lines = work.text.split('\n')
    # print(lines)
    if len(lines) == 1 and "Deleted work" in lines[0]:
        # deleted_works += 1
        return None
    visits = lines[-1]
    # print(visits)
    if "(Marked for Later.)" in visits:
        marked_for_later = True
    words = visits.split(' ')
    if "once" in visits:
        view_count = 1
    else:
        view_count = int(words[-5 if marked_for_later else -2])

    last_visit = " ".join(words[2:5])
    changes_since_last_view = visits.split('(')[1].split(')')[0]

    work_id = work.get_attribute("id").split('_')[1]

    _authors = work.find_elements(By.CSS_SELECTOR, "div.header.module > h4.heading > a[rel=\"author\"]")
    if len(_authors) == 0:
        authors = []
    else:
        authors = [aut.text for aut in _authors]

    try:
        title = work.find_element(By.CSS_SELECTOR, "div.header.module > h4.heading > a[href^=\"/works/\"]").text
    except NoSuchElementException:
        # TODO: generally this means the fic has been moved to a hidden collection
        # print("no fic name?")
        # print(lines)
        return

    _giftees = work.find_elements(By.CSS_SELECTOR, "div.header.module > h4.heading > a[href$=\"/gifts\"]")
    giftees = [g.text for g in _giftees]

    _fandoms = work.find_elements(By.CSS_SELECTOR, "div.header.module > h5.fandoms.heading > a[href^=\"/tags/\"]")
    fandoms = [fd.text for fd in _fandoms]

    _rating = work.find_element(By.CSS_SELECTOR, "div.header.module > ul.required-tags span.rating")
    rating = _rating.get_attribute("title")

    complete = "complete-yes" in work.find_element(By.CSS_SELECTOR, "div.header.module > ul.required-tags span.iswip").get_attribute("class")

    relationships = [x.text for x in work.find_elements(By.CSS_SELECTOR, "ul.tags.commas > li.relationships")]
    characters = [x.text for x in work.find_elements(By.CSS_SELECTOR, "ul.tags.commas > li.characters")]
    tags = [x.text for x in work.find_elements(By.CSS_SELECTOR, "ul.tags.commas > li.freeforms")]

    _wc = work.find_element(By.CSS_SELECTOR, "dl.stats > dd.words").text
    if _wc == "":
        word_count = 0
        print(f"ERROR: no word count for fic '{title}'")
    else:
        word_count = int(_wc.replace(",", ""))

    chapters = work.find_element(By.CSS_SELECTOR, "dl.stats > dd.chapters").text

    series = {}
    series_elements = work.find_elements(By.CSS_SELECTOR, "ul.series > li")
    # print(series_elements)
    # print([x.text for x in series_elements])
    for series_element in series_elements:
        _number = series_element.find_element(By.CSS_SELECTOR, "strong").text
        number = int(_number.replace(",", ""))
        name = series_element.find_element(By.CSS_SELECTOR, "a").text
        series[name] = number
        # print(_number)
        # print(number)
        # print(name)

    # print(series)

    most_recent_update = work.find_element(By.CSS_SELECTOR, "div.header.module > p.datetime").text

    current_work = Work(work_id, title, authors, giftees, fandoms, series, word_count, view_count, marked_for_later, last_visit, most_recent_update, changes_since_last_view, rating, chapters, complete, relationships, characters, tags)
    return current_work

process_page()

for i in tqdm(range(2, last_page + 1), desc="Processing pages"):
    driver.get(f"https://archiveofourown.org/users/{usr}/readings?page={i}")
    process_page()

print(f"{deleted_works} deleted work(s)")

# while True:
#     eval(input("> "))

# print(json.dumps([work.__dict__ for work in works], indent=4))

with open("works.json", "w") as file:
    json.dump([work.__dict__ for work in works], file, indent=4)

driver.quit()

# Word count: `li.work > dl.stats > dd.words` (must parse to int)
# author: `li.work > div.header.module > h4.heading > a[rel="author"]` (str, optionally ensure href does not have gift)
# fic name: `li.work > div.header.module > h4.heading > a[href^="/works/"]` (str)
# giftee(s?): `li.work > div.header.module > h4.heading > a[href$="/gifts"]` (str)
# my first page loop and second page loop are almost identical. revise 1st page loop to actually loop over work elements, not hardcoded 1...20
# rating: `li.work > div.header.module > ul.required-tags > li:first-child > a > span.rating`
# rating: `li.work > div.header.module > ul.required-tags span.rating`
# chapters: `li.work > dl.stats > dd.chapters` (can contain link)
