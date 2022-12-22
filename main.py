import json

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException

usr = input("Username? ")

driver = webdriver.Firefox()

driver.get("https://archiveofourown.org")

#cb = WebDriverWait(driver, timeout=10).until(lambda d: d.find_element(By.ID, "tos_agree"))
#cb.click()
#
#btn = WebDriverWait(driver, timeout=3).until(lambda d: d.find_element(By.CSS_SELECTOR, "#accept_tos:not([disabled])"))
#btn.click()

input("Please sign in")

driver.get(f"https://archiveofourown.org/users/{usr}/readings")

last_page = int(input("Number of pages? "))
# print(last_page)

works = []
deleted_works = 0

class Work:
    def __init__(self,
                 title: str,
                 authors: list[str],
                 giftees: list[str],
                 fandoms: list[str],
                 series: dict[str, int],
                 word_count: int,
                 view_count: int,
                 marked_for_later: bool):
        self.title = title
        self.authors = authors
        self.giftees = giftees
        self.fandoms = fandoms
        self.series = series
        self.word_count = word_count
        self.view_count = view_count
        self.marked_for_later = marked_for_later

def process_page():
    global deleted_works
    WebDriverWait(driver, timeout=3).until(lambda d: d.find_element(By.CSS_SELECTOR, "#main ol.reading"))
    page_works = driver.find_elements(By.CSS_SELECTOR, f"#main > ol.reading > li.work")
    for work in page_works:
        w = process_work(work)
        if w is None:
            deleted_works += 1
        else:
            works.append(w)

def process_work(work) -> Work | None:
    title = ""
    authors = []
    giftees = []
    fandoms = []
    word_count = 0
    view_count = 0
    marked_for_later = False

    lines = work.text.split('\n')
    # print(lines)
    if len(lines) == 1 and "Deleted work" in lines[0]:
        # deleted_works += 1
        return None
    visits = lines[-1]
    # print(visits)
    if "(Marked for Later.)" in visits:
        marked_for_later = True
    if "once" in visits:
        view_count = 1
    else:
        words = visits.split(' ')
        # print(words)
        view_count = int(words[-5 if marked_for_later else -2])

    _authors = work.find_elements(By.CSS_SELECTOR, "div.header.module > h4.heading > a[rel=\"author\"]")
    if len(_authors) == 0:
        authors = []
    else:
        authors = [aut.text for aut in _authors]

    try:
        title = work.find_element(By.CSS_SELECTOR, "div.header.module > h4.heading > a[href^=\"/works/\"]").text
    except NoSuchElementException:
        print("no fic name?")
        print(lines)
        return

    _giftees = work.find_elements(By.CSS_SELECTOR, "div.header.module > h4.heading > a[href$=\"/gifts\"]")
    giftees = [g.text for g in _giftees]

    _fandoms = work.find_elements(By.CSS_SELECTOR, "div.header.module > h5.fandoms.heading > a[href^=\"/tags/\"]")
    fandoms = [fd.text for fd in _fandoms]

    _wc = work.find_element(By.CSS_SELECTOR, "dl.stats > dd.words").text
    word_count = int(_wc.replace(",", ""))

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

    current_work = Work(title, authors, giftees, fandoms, series, word_count, view_count, marked_for_later)
    return current_work

process_page()

for i in range(2, last_page + 1):
    print(f"processing page {i}")
    driver.get(f"https://archiveofourown.org/users/{usr}/readings?page={i}")
    process_page()

print(f"{deleted_works} deleted work(s)")

# while True:
#     eval(input("> "))

print(json.dumps([work.__dict__ for work in works], indent=4))

with open("works.json", "w") as file:
    json.dump([work.__dict__ for work in works], file, indent=4)

driver.quit()

# Word count: `li.work > dl.stats > dd.words` (must parse to int)
# author: `li.work > div.header.module > h4.heading > a[rel="author"]` (str, optionally ensure href does not have gift)
# fic name: `li.work > div.header.module > h4.heading > a[href^="/works/"]` (str)
# giftee(s?): `li.work > div.header.module > h4.heading > a[href$="/gifts"]` (str)
# my first page loop and second page loop are almost identical. revise 1st page loop to actually loop over work elements, not hardcoded 1...20
