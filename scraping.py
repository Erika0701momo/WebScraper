import datetime
import requests
import pandas as pd
from bs4 import BeautifulSoup
import urllib.robotparser

class Scraping:
    URI = {"公開中": "https://filmarks.com/list/now", "公開予定":"https://filmarks.com/list/coming"}
    movie_info = []
    today = datetime.datetime.now().strftime("%Y.%m.%d")
    headers = {
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

    def get_pace_choice(self):
        page_choice = input(
            "公開中の映画ランキングを取得するには「公開中」、公開予定の映画ランキングを取得するには「公開予定」とタイプしてください>>")
        while page_choice not in ["公開中", "公開予定"]:
            page_choice = input("公開中か公開予定かをタイプしてください>>")
            if page_choice in ["公開中", "公開予定"]:
                break
        return page_choice

    # ページからhtmlを抜き出す
    def get_page(self,url):
        response = requests.get(url=url, headers=self.headers)
        ranking_page = response.text
        soup = BeautifulSoup(ranking_page, "html.parser")
        return soup

    # 映画の情報を辞書として格納
    def get_info(self, element, link):
        movie_info = {
            "title": element.select_one(".p-content-cassette__title").getText(),
            "rating": element.select_one(".p-content-cassette__rate .c-rating__score").getText(),
            "release_date": element.select_one(".up-screen_and_country span:first-of-type").getText(),
            "countries": [country.getText() for country in element.select(".up-screen_and_country ul li")],
            "length": element.select_one(".up-screen_and_country span:nth-of-type(2)").get_text(),
            "genres": [genre.getText() for genre in element.select(".genres li")],
            "link": link
        }
        return movie_info

    def check_scraping_ok(self):
        # robots.txtの読み取り
        robots_text_url = "https://filmarks.com/robots.txt"
        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(robots_text_url)
        rp.read()

        # robots.txtの情報から調査したいURL、User-Agentでクローク可能か調べる
        user_agent = "*"
        url_to_check = "https://filmarks.com/list/now"
        is_scraping_ok = rp.can_fetch(user_agent, url_to_check)
        return is_scraping_ok

    def get_movie_data(self, is_scraping_ok, page_choice):
        # スクレイピングOKなら映画ランキングをスクレイピング
        if is_scraping_ok:
            for n in range(1, 3):
                url = self.URI[page_choice] + "?page=" + str(n)
                soup = self.get_page(url)
                for element in soup.select(".p-content-cassette__info"):
                    # 作品詳細のリンクがない映画の対策
                    link_element = element.select_one(".p-content-cassette__people__readmore a")
                    if link_element:
                        link = "https://filmarks.com" + link_element.get("href")
                    else:
                        link = None

                    self.movie_info.append(self.get_info(element, link))

    def make_csv(self, page_choice):
         # csvを出力
        df = pd.DataFrame(self.movie_info)
        df.index = df.index + 1
        df.to_csv(f"{page_choice}Filmarksランキング{self.today}.csv", encoding="utf-8_sig")






