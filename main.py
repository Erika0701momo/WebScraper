from scraping import Scraping

scraping = Scraping()

page_choice = scraping.get_pace_choice()
is_scraping_ok = scraping.check_scraping_ok()
scraping.get_movie_data(is_scraping_ok, page_choice)
scraping.make_csv(page_choice)




