import datetime
import requests
import pandas as pd
from bs4 import BeautifulSoup
import urllib.robotparser
from seleniumwire import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
# from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException
import datetime

class Scraping:
    def __init__(self):
        self.URI = {"公開中": "https://filmarks.com/list/now", "公開予定":"https://filmarks.com/list/coming"}
        self.movie_info = []
        self.today = datetime.datetime.now().strftime("%Y.%m.%d")
        self.done = False
        self.PROXY = "<http://localhost:8080>"
    # ヘッダーをconfigureするためのリクエストインターセプタを定義
    def interceptor(self, request):
        # request.headers["Accept-Language"] = "en-US,en;q=0.9,ja;q=0.8"
        # request.headers["Referer"] = "https://www.google.com/"

        del request.headers["User-Agent"]
        # del request.headers["Sec-Ch-Ua"]
        # del request.headers["Sec-Fetch-Site"]
        # del request.headers["Accept-Encoding"]

        request.headers[
            "User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        # request.headers["Sec-Ch-Ua"] = "\"Not/A)Brand\";v=\"8\", \"Chromium\";v=\"126\", \"Google Chrome\";v=\"126\""
        # request.headers["Sec-Fetch-Site"] = "cross-site"
        # request.headers["Accept-Encoding"] = "gzip, deflate, br, zstd"

    def get_pace_choice(self):
        page_choice = input(
            "公開中の映画ランキングを取得するには「公開中」、公開予定の映画ランキングを取得するには「公開予定」とタイプしてください>>")
        while page_choice not in ["公開中", "公開予定"]:
            page_choice = input("公開中か公開予定かをタイプしてください>>")
            if page_choice in ["公開中", "公開予定"]:
                break
        return page_choice

    def initialize_driver(self):
        # プロキシ設定
        webdriver.DesiredCapabilities.EDGE["proxy"] = {
            'proxyType': 'MANUAL',
            'httpProxy': self.PROXY,
            'sslProxy': self.PROXY,
            'http2': False
        }

        edge_options = webdriver.EdgeOptions()
        # edge_options.add_argument("--headless")
        edge_options.add_argument("--no-sandbox")
        edge_options.add_argument("--disable-dev-shm-usage")
        edge_options.add_argument("--disable-gpu")
        edge_options.add_argument("--window-size=1920,1080")
        self.driver = webdriver.Edge(options=edge_options)
        self.driver.request_interceptor = self.interceptor


    # ページからhtmlを抜き出す
    def get_page(self,url):
        self.driver.implicitly_wait(30)
        print(f"get開始前{datetime.datetime.now()}")
        self.driver.get(url)
        try:
            print(f"element取得前{datetime.datetime.now()}")
            elements = self.driver.find_elements(By.CSS_SELECTOR, ".p-content-cassette__info")
            print(f"element取得後{datetime.datetime.now()}")
            if len(elements) == 0:
                self.driver.quit()
                self.done = True
                print("elementが0だったのでquitしました")
        except NoSuchElementException:
            print("エレメントがありません")
            self.driver.quit()
            print("quitしました")
            self.done = True
        print(f"get後{datetime.datetime.now()}")

    # 映画の情報を辞書として格納
    def get_info(self, element, link, length):
        movie_info = {
            "title": element.select_one(".p-content-cassette__title").getText(),
            "rating": element.select_one(".p-content-cassette__rate .c-rating__score").getText(),
            "clips": element.select_one(".p-content-cassette__action--clips a span").getText(),
            "release_date": element.select_one(".up-screen_and_country span:first-of-type").getText(),
            "countries": [country.getText() for country in element.select(".up-screen_and_country ul li")],
            "length": length,
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
            page = 1
            while True:
                try:
                    url = self.URI[page_choice] + "?page=" + str(page)
                    self.get_page(url)
                    if self.done:
                        break
                    soup = BeautifulSoup(self.driver.page_source, "html.parser")
                    print(page)
                    for element in soup.select(".p-content-cassette__info"):
                        # 作品詳細のリンクがない映画の対策
                        link_element = element.select_one(".p-content-cassette__people__readmore a")
                        if link_element:
                            link = "https://filmarks.com" + link_element.get("href")
                        else:
                            link = None
                        # 上映時間がない映画の対策
                        length_element = element.select_one(".up-screen_and_country span:nth-of-type(2)")
                        if length_element:
                            length = length_element.getText()
                        else:
                            length = None
                        movie = self.get_info(element, link, length)
                        print(movie["title"])
                        self.movie_info.append(self.get_info(element, link, length))
                except Exception as e:
                    print(e)
                    self.driver.quit()

                page += 1


    def make_csv(self, page_choice):
         # csvを出力
        df = pd.DataFrame(self.movie_info)
        df.index = df.index + 1
        df.to_csv(f"{page_choice}Filmarksランキング{self.today}.csv", encoding="utf-8_sig")





