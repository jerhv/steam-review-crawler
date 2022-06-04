import json as js
import re
import uuid
import zlib
from datetime import datetime
from math import floor

import requests
from bs4 import BeautifulSoup


# STILL NEEDS:
# - Tests to ensure spec is aligned
# - General refactor to make this more obj oriented, access functions to private variables n shit
#   - Maybe even split some stuff up into more classes...
# - Docstrings?

class Crawler:

    def __init__(self):
        # self.appid = self.__id_check(appid)
        self.appid = 220
        self.source = "steam"
        self.__update()

    def __update(self):
        scrape = Scraper(self.appid)
        self.franchise = scrape.retrieve_franchise()
        self.game_name = scrape.retrieve_appname()

    def retrieve_reviews_json(self, params=None):
        if params is None:
            params = {'json': 1}
        return requests.get(url=f"https://store.steampowered.com/appreviews/{self.appid}`",
                            params=params
                            ).json()

    def conform_review(self, review):
        ref_uuid = uuid.UUID('2E3E41A45BF3F2F009D73F28E04DA548')
        n_json = {
            "id": zlib.crc32(bytes(str(review), 'utf-8')),
            "author": str(uuid.uuid3(ref_uuid, str(review['author']))),
            "date": datetime.fromtimestamp(review['timestamp_created']).strftime("%Y-%m-%d"),
            "hours": floor(review['author']['playtime_forever'] / 60),
            "content": review['review'],
            "comments": review['comment_count'],
            "source": self.source,
            "helpful": review['votes_up'],
            "funny": review['votes_funny'],
            "recommended": review['voted_up'],
            "franchise": self.franchise,
            "gameName": self.game_name
        }
        return n_json

    # messy, should be a try catch, idk why im so stupid
    @staticmethod
    def __id_check(arg):  # ids are seven digit ints
        if isinstance(arg, int) and len(str(arg)) <= 7:
            return arg
        raise ValueError("ID provided is not correct - it should be an integer <= 7 digits long")

    # too many local variables, too many branches
    def crawl_reviews(self, appid=None, num_reviews=5000, filter_from=None, filter_to=None, json=True):

        def __filter_check(arg):
            try:
                if arg:
                    return datetime.strptime(arg, date_format)
                return None
            except ValueError:
                print("Filter(s) not in format YYYY-MM-DD.")
                return None

        if self.appid != appid and appid is not None:
            appid = self.__id_check(appid)
            self.appid = appid
            self.__update()

        date_format = "%Y-%m-%d"
        date_format_trunc = "%Y%m%d"
        filter_from = __filter_check(filter_from)
        filter_to = __filter_check(filter_to)
        filename = f'{self.appid}_reviews'
        if filter_from:
            filename += f'_from_{datetime.strftime(filter_from, date_format_trunc)}'
        if filter_to:
            filename += f'_to_{datetime.strftime(filter_to, date_format_trunc)}'
        filename += '.json'

        def __filter(review):
            date_val = datetime.strptime(review['date'], date_format)
            return bool(filter_from <= date_val <= filter_to)

        cursor = '*'
        parameters = {'json': 1, 'filters': 'all', 'purchase_type': 'all',
                      # 'day_range': '9223372036854775807'}   #gets everything but is slow
                      'day_range': '365'}  # only gets a years worth but is fast!
        # day_range of 365 is apparently the highest range the argument goes according to the docs
        # so I'm assuming the other one is just breaking the api to do this?

        reviews_list = []
        while num_reviews > 0:
            parameters['cursor'] = cursor.encode()
            parameters['num_per_page'] = min(100, num_reviews)
            num_reviews -= 100

            api_r = self.retrieve_reviews_json(params=parameters)
            cursor = api_r['cursor']
            rev100 = [self.conform_review(x) for x in api_r['reviews']]

            # FILTER STUFF BELOW - This is janky but all works at least. Use a lambda instead mayb
            if filter_from or filter_to:
                if not filter_to:  # just does this every time (bad)
                    filter_to = datetime.now()
                if not filter_from:
                    filter_from = datetime.min

                for n in rev100:
                    if __filter(n):
                        reviews_list.append(n)
                    else:
                        num_reviews += 1
            else:
                for n in rev100:
                    reviews_list.append(n)
                # reviews_list = [x for n in reviews_list for x in n]

            if len(api_r['reviews']) < 100:
                break

        reviews_list.sort(key=lambda x: (datetime.strptime(x['date'], date_format), x['id']))

        print(f"{len(reviews_list)} reviews for {self.game_name} retrieved successfully.")

        if json:
            with open(filename, 'w+', encoding='utf-8') as outf:
                js.dump(reviews_list, outf, ensure_ascii=False)
                print(f"Committed review list to {filename}.")

        return reviews_list


class Scraper:
    def __init__(self, appid=220):
        self.appid = appid
        self.__update()

    def __update(self):
        store_page = requests.get(f"https://store.steampowered.com/app/{self.appid}/").text
        self.parser = BeautifulSoup(store_page, 'html.parser')

    def __retrieve_storepage_data(self, class_name):
        divs = self.parser.find_all("div", {"class": class_name})
        return [x.text for x in divs][:1][0] if divs else None  # these look ugly so fix them

    def retrieve_franchise(self):
        pattern = 'entire (.*?) [Ff]ranchise'
        storepage_divs = self.__retrieve_storepage_data(class_name="franchise_name")
        return re.search(pattern, storepage_divs).group(1) if storepage_divs else None

    def retrieve_appname(self):
        return self.__retrieve_storepage_data(class_name="apphub_AppName")

    def set_appid(self, n_appid):
        self.appid = n_appid
        self.__update()

    def get_appid(self):
        return self.appid
