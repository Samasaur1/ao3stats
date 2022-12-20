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

uniq_fic_count = 0
fic_count = 0
uniq_word_count = 0
word_count = 0

most_read_fic = ""
most_reads = 0
longest_fic = ""
longest_length = 0

marked_for_later = 0
deleted_works = 0

authors = {}

def process_page():
    WebDriverWait(driver, timeout=3).until(lambda d: d.find_element(By.CSS_SELECTOR, "#main ol.reading"))
    works = driver.find_elements(By.CSS_SELECTOR, f"#main > ol.reading > li.work")
    for work in works:
        process_work(work)

def process_work(work):
    global uniq_fic_count
    global fic_count
    global uniq_word_count
    global word_count
    global most_read_fic
    global most_reads
    global longest_fic
    global longest_length
    global marked_for_later
    global deleted_works
    global authors
    lines = work.text.split('\n')
    if len(lines) == 1 and "Deleted work" in lines[0]:
        deleted_works += 1
        return
    visits = lines[-1]
    if "(Marked for Later.)" in visits:
        marked_for_later += 1
        return
    if visits[-4:] == "once":
        vc = 1
    else:
        words = visits.split(' ')
        vc = int(words[-2])
    _authors = work.find_elements(By.CSS_SELECTOR, "div.header.module > h4.heading > a[rel=\"author\"]")
    if len(_authors) == 0:
        author = "Anonymous"
    else:
        author = " ".join([x.text for x in _authors])
    try:
        fic_name = work.find_element(By.CSS_SELECTOR, "div.header.module > h4.heading > a[href^=\"/works/\"]").text
    except NoSuchElementException:
        print("no fic name?")
        print(lines)
        return
    giftees = work.find_elements(By.CSS_SELECTOR, "div.header.module > h4.heading > a[href$=\"/gifts\"]")
    _fandoms = work.find_elements(By.CSS_SELECTOR, "div.header.module > h5.fandoms.heading > a[href^=\"/tags/\"]")
    fandoms = [fd.text for fd in _fandoms]
    print(lines[0])
    print(author)
    print(fic_name)
    print(giftees)
    print(fandoms)
    _wc = work.find_element(By.CSS_SELECTOR, "dl.stats > dd.words").text
    wc = int(_wc.replace(",", ""))
    uniq_fic_count += 1
    fic_count += vc
    uniq_word_count += wc
    word_count += vc * wc

    _fics, _uniq_fics, _words, _uniq_words, _most_read_fic, _times_read, _longest_fic, _longest_length = authors.get(author, (0,0,0,0,"",0,"",0))
    if vc > _times_read:
        _ntr = vc
        _nmrf = f"{fic_name} by {author}"
    else:
        _ntr = _times_read
        _nmrf = _most_read_fic
    if wc > _longest_length:
        _nll = wc
        _nlf = f"{fic_name} by {author}"
    else:
        _nll = _longest_length
        _nlf = _longest_fic
    authors[author] = (_fics + vc, _uniq_fics + 1, _words + vc * wc, _uniq_words + wc, _nmrf, _ntr, _nlf, _nll)

    if vc > most_reads:
        most_reads = vc
        most_read_fic = f"{fic_name} by {author}"
    if wc > longest_length:
        longest_length = wc
        longest_fic = f"{fic_name} by {author}"


process_page()

for i in range(2, last_page + 1):
    print(f"processing page {i}")
    driver.get(f"https://archiveofourown.org/users/{usr}/readings?page={i}")
    process_page()

    print(f"uniq_fic_count: {uniq_fic_count}")
    print(f"fic_count: {fic_count}")
    print(f"uniq_word_count: {uniq_word_count}")
    print(f"word_count: {word_count}")
    print(f"most_read_fic: {most_read_fic}")
    print(f"most_reads: {most_reads}")
    print(f"longest_fic: {longest_fic}")
    print(f"longest_length: {longest_length}")
    print(f"marked_for_later: {marked_for_later}")
    print(f"deleted_works: {deleted_works}")

print("\n\nTOTAL\n\n")

print(f"uniq_fic_count: {uniq_fic_count}")
print(f"fic_count: {fic_count}")
print(f"uniq_word_count: {uniq_word_count}")
print(f"word_count: {word_count}")
print(f"most_read_fic: {most_read_fic}")
print(f"most_reads: {most_reads}")
print(f"longest_fic: {longest_fic}")
print(f"longest_length: {longest_length}")
print(f"marked_for_later: {marked_for_later}")
print(f"deleted_works: {deleted_works}")

with open("authors.csv", "w") as file:
    file.write("author,fics,uniq_fics,words,uniq_words,most_read_fic,times_read,longest_fic,longest_length\n")
    for author, tup in authors.items():
        file.write(author)
        for el in tup:
            if type(el) == str:
                file.write(f",\"{el}\"")
            else:
                file.write(f",{el}")
        file.write("\n")
print(authors)

driver.quit()

# Word count: `li.work > dl.stats > dd.words` (must parse to int)
# author: `li.work > div.header.module > h4.heading > a[rel="author"]` (str, optionally ensure href does not have gift)
# fic name: `li.work > div.header.module > h4.heading > a[href^="/works/"]` (str)
# giftee(s?): `li.work > div.header.module > h4.heading > a[href$="/gifts"]` (str)
# my first page loop and second page loop are almost identical. revise 1st page loop to actually loop over work elements, not hardcoded 1...20
