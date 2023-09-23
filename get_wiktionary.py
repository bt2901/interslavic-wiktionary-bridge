# encoding=utf8
import requests
from bs4 import BeautifulSoup
from time import sleep
from urllib.parse import quote

import os
import pickle
import argparse

import unicodedata

WIKI_POS_TAGS = "adjective adverb conjunction determiner interjection morpheme multiword term noun numeral particle phrase postposition preposition pronoun verb".split()


# remove accent marks
def clean_extra_diacritics(w):
    w = w.strip()
    w = [c 
         for c in unicodedata.normalize("NFKC", w)
         if not unicodedata.combining(c)
    ]
    return "".join(w).replace("ȉ", "i")


def write_descendants(soup, words_data):
    the_list = soup.find(attrs={"id": "Descendants"})
    
    if not the_list:
        return
    ul = the_list.find_next("ul")
    try:
        if ul.next_sibling.next_sibling.name == "ul":
            nonslavic = ul.next_sibling.next_sibling
            ul.append(nonslavic)
    except AttributeError:
        pass
    the_list = ul

    for e in the_list.find_all(attrs={"class": "tr Latn"}):
        ok_to_delete = True
        for e_sib in [e.find_next(), e.find_previous()]:
            if e_sib.attrs.get('class', []) != ['mention-gloss-paren', 'annotation-paren']:
                ok_to_delete = False
        if ok_to_delete:
            for e_sib in [e.find_next(), e.find_previous()]:
                e_sib.decompose()
        e.decompose()

    # for e in the_list.find_all(attrs={"class": "ib-content qualifier-content"}):
    for e in the_list.find_all(attrs={"class": "ib-comma qualifier-comma"}):
        e.string = " &"

    for elem in the_list.find_all("li"):
        if any(e.name == "dl" for e in elem.children):
            #splitted = elem.text.split("\n")
            #par_content = splitted[1].partition(":")
            #elem_text = [splitted[0], par_content[-1] or par_content[0]]
            
            name = elem.text.partition(":")[0]
            splitted = [e.text.strip() for e in elem.find_all("dd")]
            par_content = splitted[0].partition(":")
            elem_text = [name, par_content[-1] or par_content[0]]
            
        else:
            elem_text = []
            for sub_elem in elem.children:
                if sub_elem.name not in ["ul", "style"]:# "dl", "dd"]:
                    elem_text.append(sub_elem.text)

        elem_text = "".join(elem_text).replace("(tonal orthography)", "").replace("(see there for further descendants)", "")

        arr = elem_text.strip().split(":")
        if len(arr) == 2:
            lang, words = arr
            if words:
                words = arr[1].replace(" ()", "").replace(";", ",").split(",")
                words = [clean_extra_diacritics(w) for w in words]
                words_data[lang] = words

def write_related_links(soup, words_data):
    for elem in soup.find_all(attrs={'class': "inflection-table"}):
        elem.decompose()
    
    words_data["Related_Slavic"] = []
    words_data["Related_NonSlavic"] = []
    for link in soup.find_all("a"):
        if link.text and link.text[0] == "*" and 'href' in link.attrs:
            href = link.attrs['href']
            if ("Reconstruction:Proto-Slavic" in href):
                words_data["Related_Slavic"].append((href, link.text))
            else:
                words_data["Related_NonSlavic"].append((href, link.text))

def write_meaning(soup, words_data):
    words_data["POS"] = []
    for elem in soup.find_all(attrs={'class': "mw-headline"}):
        if elem.text.lower() in WIKI_POS_TAGS:
            pos = elem.text
            words_data["POS"].append(pos)
            if elem.find_next("ol"):
                meaning = elem.find_next("ol").text.split("\n")
                words_data[pos] = meaning

def extract_etymology_section(soup, section_id):
    found = []
    for h in soup.find_all("h3"):
        section = h.find_all("span", attrs={'id': section_id})
        if section:
            found.append(section[0].text)
            
            elem = section[0].parent.next_sibling
            while elem.name not in {"h1", "h2", "h3", "h4"}:
                found.append(str(elem))
                elem = elem.next_sibling
                if len(found) > 20:
                    print("ERROR", url)
                    raise KeyError
                    break
    return found



def gather_wikidict_urls():
    cur_url = "https://en.wiktionary.org/wiki/Category:Proto-Slavic_lemmas"
    wikidict_urls = set()

    while cur_url:
        # print(cur_url)
        r = requests.get(cur_url)
        cat_soup = BeautifulSoup(r.text)

        cur_url = None
        for e in cat_soup.find_all("a", attrs={"title":"Category:Proto-Slavic lemmas"}):
            if e.text == "next page":
                print(e)
                cur_url = "https://en.wiktionary.org" + e.attrs["href"]

        for e in cat_soup.find_all("a"):
            if "Reconstruction:Proto-Slavic" in e.text:
                wikidict_urls.add(e.attrs["href"])
        sleep(0.1)
    return wikidict_urls 


def download_urls(words_data, wikidict_urls):
    for url in tqdm.tqdm(wikidict_urls):
        if url in words_data:
            continue
        r = requests.get("https://en.wiktionary.org" + url)

        soup = BeautifulSoup(r.text)
        lemma = soup.title.text.partition("/")[-1].partition(" - ")[0]
        soup = soup.find(attrs={"class":"mw-body-content"})
    
        words_data[url] = {}
        words_data[url]["*"] = lemma
    
        words_data[url]["Etymology"] = extract_etymology_section(soup, "Etymology")
        if soup.find_all("span", attrs={'id': "Reconstruction"}):
            print(lemma)
            words_data[url]["Etymology"] += extract_etymology_section(soup, "Reconstruction")
        write_related_links(soup, words_data[url])
        write_descendants(soup, words_data[url])
        write_meaning(soup, words_data[url])
    
        sleep(0.01 + len(url) % 2)
    return words_data


if __name__ == "__main__":
    # parser = argparse.ArgumentParser()
    # parser.add_argument("mode", choices=['range', 'download'], default="download")
    # parsed_args = parser.parse_args()

    if os.path.isfile("wiktionary_extended.json"):
        with open("wiktionary_extended.json", "r", encoding="utf8") as f:
            wikidict_urls = set(json.load(f).keys())
        wikidict_urls |= {quote("/wiki/Reconstruction:Proto-Slavic/" + s, safe=":/") for s in "čęti gořestь věverъka orzsvětъ".split()}
    else:
        wikidict_urls = gather_wikidict_urls()

    words_data = {}
    download_urls(words_data, wikidict_urls)