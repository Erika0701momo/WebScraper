from scraping import Scraping

# 公開中または公開予定の映画ランキングを取得して、csvに保存
scraping = Scraping()
page_choice = scraping.get_pace_choice()
is_scraping_ok = scraping.check_scraping_ok()
scraping.initialize_driver()
scraping.get_movie_data(is_scraping_ok, page_choice)
scraping.make_csv(page_choice)




