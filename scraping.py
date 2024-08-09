import pandas as pd
from bs4 import BeautifulSoup
import urllib.robotparser
from seleniumwire import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import datetime
from logging import getLogger, INFO, StreamHandler, Formatter

# ロガーの設定
logger = getLogger(__name__)
logger.setLevel(INFO)

# コンソールハンドラーの設定
s_handler = StreamHandler()
s_handler.setLevel(INFO)

# ログフォーマットの設定
formatter = Formatter(
    "%(asctime)s - %(levelname)s : %(name)s : " "%(message)s (%(filename)s:%(lineno)d)"
)
s_handler.setFormatter(formatter)
logger.addHandler(s_handler)


class Scraping:
    def __init__(self, page_choice):
        self.URI = {
            "公開中": "https://filmarks.com/list/now",
            "公開予定": "https://filmarks.com/list/coming",
        }
        self.movie_info = []
        self.today = datetime.datetime.now().strftime("%Y.%m.%d")
        # 全件取得したかどうかのフラグ
        self.is_done = False
        self.PROXY = "http://localhost:8080"
        # 公開中または公開予定、どちらかを選ぶ
        self.page_choice = page_choice
        self.movie_numbers_of_filmarks = None
        self.diver = None
        self.is_elem_available = True
        self.retry_count = 0

    # ヘッダーをconfigureするためのリクエストインターセプタを定義
    def interceptor(self, request):
        request.headers["Accept-Language"] = "en-US,en;q=0.9,ja;q=0.8"
        request.headers["Referer"] = "https://www.google.com/"

        del request.headers["User-Agent"]
        del request.headers["Sec-Ch-Ua"]
        del request.headers["Sec-Fetch-Site"]
        del request.headers["Accept-Encoding"]

        request.headers["User-Agent"] = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        )
        request.headers["Sec-Ch-Ua"] = (
            '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"'
        )
        request.headers["Sec-Fetch-Site"] = "cross-site"
        request.headers["Accept-Encoding"] = "gzip, deflate, br, zstd"

    def initialize_driver(self):
        logger.info("ドライバ初期化開始")
        # プロキシ設定
        webdriver.DesiredCapabilities.CHROME["proxy"] = {
            "proxyType": "MANUAL",
            "httpProxy": self.PROXY,
            "sslProxy": self.PROXY,
            "http2": False,
        }

        # オプション設定
        chrome_options = webdriver.ChromeOptions()
        chrome_options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
        prefs = {
            "profile.managed_default_content_settings.images": 2,
            "profile.managed_default_content_settings.stylesheets": 2,  # スタイルシートを読み込まない
            "profile.managed_default_content_settings.cookies": 2,  # クッキーを無効にする
            "profile.managed_default_content_settings.plugins": 2,  # プラグインを無効にする
            "profile.managed_default_content_settings.popups": 2,  # ポップアップを無効にする
            "profile.managed_default_content_settings.geolocation": 2,  # 位置情報を無効にする
            "profile.managed_default_content_settings.notifications": 2,  # 通知を無効にする
            "profile.managed_default_content_settings.automatic_downloads": 2,  # 自動ダウンロードを無効にする
        }
        chrome_options.add_experimental_option("prefs", prefs)
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-cache")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--remote-debugging-port=9222")
        chrome_options.add_argument("--disable-proxy-certificate-handler")
        chrome_options.add_argument("--log-level=3")

        # DOMにはアクセスできる状態まで待つ
        chrome_options.page_load_strategy = "eager"

        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.request_interceptor = self.interceptor

        logger.info("ドライバ初期化終了")

    # ページからhtmlを抜き出す
    def get_page(self, url):
        self.driver.implicitly_wait(10)
        self.driver.get(url)
        try:
            self.is_elem_available = True
            element = self.driver.find_element(
                By.CSS_SELECTOR, ".p-content-cassette__info"
            )
        except NoSuchElementException:
            if self.movie_numbers_of_filmarks == len(self.movie_info):
                self.is_done = True
                logger.info("映画データを全件分取得しました")
            elif self.retry_count <= 3:
                self.retry_count += 1
                self.is_elem_available = False
                logger.info(f"リトライ{self.retry_count}回目")
            else:
                self.is_done = True
                logger.error("申し訳ありません、映画データを全件分取得できませんでした")
        except Exception:
            logger.exception("ページ読み込みの際にエラーが発生しました")
            self.is_done = True
        finally:
            if self.is_done:
                self.driver.quit()

    # 映画の情報を辞書として格納
    def get_info(self, element, link, length):
        movie_info = {
            "title": element.select_one(".p-content-cassette__title").getText(),
            "rating": element.select_one(
                ".p-content-cassette__rate .c-rating__score"
            ).getText(),
            "clips": element.select_one(
                ".p-content-cassette__action--clips a span"
            ).getText(),
            "release_date": element.select_one(
                ".up-screen_and_country span:first-of-type"
            ).getText(),
            "countries": [
                country.getText()
                for country in element.select(".up-screen_and_country ul li")
            ],
            "length": length,
            "genres": [genre.getText() for genre in element.select(".genres li")],
            "link": link,
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
        url_to_check = self.URI[self.page_choice]
        is_scraping_ok = rp.can_fetch(user_agent, url_to_check)
        return is_scraping_ok

    def get_movie_data(self, is_scraping_ok):
        # スクレイピングOKなら映画ランキングをスクレイピング
        if is_scraping_ok:
            page = 1
            while True:
                try:
                    logger.info(f"{page}ページ目取得中")
                    url = self.URI[self.page_choice] + "?page=" + str(page)
                    self.get_page(url)
                    if self.is_done:
                        break
                    if not self.is_elem_available:
                        continue

                    else:

                        soup = BeautifulSoup(self.driver.page_source, "html.parser")

                        # 映画の全件数取得
                        self.movie_numbers_of_filmarks = int(
                            soup.select_one(".c-heading-1 span")
                            .getText()
                            .split()[1]
                            .split("作品")[0]
                        )

                        for element in soup.select(".p-content-cassette__info"):
                            # 作品詳細のリンクがない映画の対策
                            link_element = element.select_one(
                                ".p-content-cassette__people__readmore a"
                            )
                            if link_element:
                                link = "https://filmarks.com" + link_element.get("href")
                            else:
                                link = None
                            # 上映時間がない映画の対策
                            length_element = element.select_one(
                                ".up-screen_and_country span:nth-of-type(2)"
                            )
                            if length_element:
                                length = length_element.getText()
                            else:
                                length = None

                            self.movie_info.append(self.get_info(element, link, length))

                except Exception:
                    self.driver.quit()
                    logger.exception("映画データ取得中にエラーが発生しました")
                    break

                page += 1
                self.retry_count = 0

    def make_csv(self):
        # csvを出力
        df = pd.DataFrame(self.movie_info)
        df.index = df.index + 1
        df.to_csv(
            f"{self.page_choice}Filmarksランキング{self.today}.csv",
            encoding="utf-8_sig",
        )

    def make_dataframe(self):
        # dfを作成
        df = pd.DataFrame(self.movie_info)
        return df

    def scrape_filmarks_movies(self):
        """
        Filmarksから映画データを取得する処理をまとめた関数
        """
        is_scraping_ok = self.check_scraping_ok()
        self.initialize_driver()
        self.get_movie_data(is_scraping_ok)
