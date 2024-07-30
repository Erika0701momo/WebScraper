from scraping import Scraping

if __name__ == "__main__":
    # 公開中または公開予定の映画ランキングを取得して、csvに保存
    scraping = Scraping()
    print("scrapingインスタンス化完了")
    page_choice = scraping.get_pace_choice()
    print("pagechoice取得完了")
    is_scraping_ok = scraping.check_scraping_ok()
    scraping.initialize_driver()
    print("driver初期化完了")
    scraping.get_movie_data(is_scraping_ok, page_choice)
    scraping.make_csv(page_choice)




