from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

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
print(last_page)

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

rl = WebDriverWait(driver, timeout=3).until(lambda d: d.find_element(By.CSS_SELECTOR, "#main ol.reading"))
for work_number in range(1,21):
    #work = rl.find_element(By.CSS_SELECTOR, f":nth-child({work_number})")
    work = driver.find_element(By.CSS_SELECTOR, f"#main ol.reading li.work:nth-of-type({work_number})")
    #print(work.text)
    lines = work.text.split('\n')
    if len(lines) == 1 and "Deleted work" in lines[0]:
        deleted_works += 1
        continue
    stats = lines[-2]
    visits = lines[-1]
    #print(stats)
    #print(visits)
    if "(Marked for Later.)" in visits:
        marked_for_later += 1
        continue
    if visits[-4:] == "once":
        vc = 1
    else:
        words = visits.split(' ')
        vc = int(words[-2])
    #print(vc)
    idx = stats.find("Words: ")
    if idx == -1:
        continue
    chopped = stats[idx + 7:].split(' ')
    _wc = chopped[0]
    wc = int(_wc.replace(",", ""))
    #print(wc)
    uniq_fic_count += 1
    fic_count += vc
    uniq_word_count += wc
    word_count += vc * wc

    if vc > most_reads:
        most_reads = vc
        most_read_fic = lines[0]
    if wc > longest_length:
        longest_length = wc
        longest_fic = lines[0]

for i in range(2, last_page + 1):
    print(f"processing page {i}")
    driver.get(f"https://archiveofourown.org/users/{usr}/readings?page={i}")
    WebDriverWait(driver, timeout=3).until(lambda d: d.find_element(By.CSS_SELECTOR, "#main ol.reading"))
    works = driver.find_elements(By.CSS_SELECTOR, f"#main > ol.reading > li.work")
    for work in works:
        #print(work.text)
        lines = work.text.split('\n')
        if len(lines) == 1 and "Deleted work" in lines[0]:
            deleted_works += 1
            continue
        stats = lines[-2]
        visits = lines[-1]
        #print(stats)
        #print(visits)
        if "(Marked for Later.)" in visits:
            marked_for_later += 1
            continue
        if visits[-4:] == "once":
            vc = 1
        else:
            words = visits.split(' ')
            vc = int(words[-2])
        #print(vc)
        idx = stats.find("Words: ")
        if idx == -1:
            continue
        chopped = stats[idx + 7:].split(' ')
        _wc = chopped[0]
        wc = int(_wc.replace(",", ""))
        #print(wc)
        uniq_fic_count += 1
        fic_count += vc
        uniq_word_count += wc
        word_count += vc * wc

        if vc > most_reads:
            most_reads = vc
            most_read_fic = lines[0]
        if wc > longest_length:
            longest_length = wc
            longest_fic = lines[0]


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

driver.quit()
