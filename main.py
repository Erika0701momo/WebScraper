from scraping import Scraping

if __name__ == "__main__":
    # 公開中または公開予定の映画ランキングを取得して、csvに保存
    scraping = Scraping("公開予定")
    scraping.scrape_filmarks_movies()
    scraping.make_csv()

    # または、データフレームを作成
    # df = scraping.make_dataframe()



