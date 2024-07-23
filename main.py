import datetime

import pandas as pd
from bs4 import BeautifulSoup
import time
import urllib.request
import pandas as ps

URI = "https://www.amazon.co.jp/gp/bestsellers/books/492352/"

book_info = []

header = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "en-US,en;q=0.9,ja;q=0.8",
    "Priority": "u=0, i",
    "Sec-Ch-Ua": "\"Not/A)Brand\";v=\"8\", \"Chromium\";v=\"126\", \"Google Chrome\";v=\"126\"",
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": "\"Windows\"",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "cross-site",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
}

# ページからhtmlを抜き出す
def get_page(url):
    html = urllib.request.urlopen(url)
    soup = BeautifulSoup(html, "html.parser")
    time.sleep(2)
    return soup

# 本の情報を辞書として格納
def get_info(element):
    book_info = {
        "rank": element.select_one(".zg-bdg-text").getText(),
        "title": element.select_one("div div a span div").getText().replace("\u3000", ""),
        "author": element.select_one(".a-row .a-size-small div").getText().replace("\u3000", ""),
        "price": element.select_one(".p13n-sc-price").getText(),
        "link": "https://www.amazon.co.jp" + element.select_one(".a-link-normal").attrs["href"]
    }
    return book_info

for n in range(1, 3):
    url = URI + "?pg=" + str(n)
    soup = get_page(url)
    for element in soup.find_all(name="div", id="gridItemRoot"):
        book_info.append(get_info(element))

today = datetime.datetime.now().strftime("%Y.%m.%d")

# csvを出力
df = pd.DataFrame(book_info)
df.to_csv(f"AmazonITranking{today}.csv", encoding="utf-8_sig", index=False)





