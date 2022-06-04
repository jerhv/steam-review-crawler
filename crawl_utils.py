import json as js
import re
import uuid
import zlib
from datetime import datetime
from math import floor

import requests
from bs4 import BeautifulSoup


class Crawler:
    """
    Class for crawler handling. Stores appid, source and functions to assist crawler.
    """

    def __init__(self):
        """
        Initialises crawler with default appid and source.
        """
        # self.appid = self.__id_check(appid)
        self.appid = 220
        self.source = "steam"
        self.__update()

    def __update(self):
        """
        Updates the franchise and game name strings every time appID is updated.
        """
        scrape = Scraper(self.appid)
        self.franchise = scrape.retrieve_franchise()
        self.game_name = scrape.retrieve_appname()

    def retrieve_reviews_json(self, params=None):
        """
        Calls on Steam WebAPI to retrieve some reviews from given appID.
        :param params: Parameters of API request
        :return: JSON object containing all reviews given by API request
        """
        if params is None:
            params = {'json': 1}
        return requests.get(url=f"https://store.steampowered.com/appreviews/{self.appid}`",
                            params=params
                            ).json()

    def conform_review(self, review):
        """
        Conforms given review to a more readable structure.
        ID is generated from a CRC checksum encoding the string form of the entire review.
        Author ID is a generated UUID from all author information.
        :param review: Review in default Steam WebAPI format
        :return: Review in new JSON format
        """
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

    @staticmethod
    def __id_check(arg):
        """
        Checks given ID to ensure it's in the proper format."
        :param arg: Object to check
        :return: Same object if it is confirmed to be an ID string
        """
        if isinstance(arg, int) and len(str(arg)) <= 7:
            return arg
        raise ValueError("ID provided is not correct - it should be an integer <= 7 digits long")

    def crawl_reviews(self, appid=None, num_reviews=5000, filter_from=None, filter_to=None, json=True):
        """
        Retrieves num_review amount of reviews from the Steam WebAPI given the provided ID.
        :param appid: Steam App ID
        :param num_reviews: Number of reviews to retrieve
        :param filter_from: Optional filter start date
        :param filter_to: Optional filter end date
        :param json: Will print reviews to JSON file if true
        :return: list of reviews in JSON format
        """

        def __filter_check(arg, filter_format):
            """Checks given argument to determine if its the proper format (a date in the format YYYY-MM-DD)"""
            try:
                if arg:
                    return datetime.strptime(arg, filter_format)
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
        filter_from = __filter_check(filter_from, date_format)
        filter_to = __filter_check(filter_to, date_format)
        filename = f'{self.appid}_reviews'
        if filter_from:
            filename += f'_from_{datetime.strftime(filter_from, date_format_trunc)}'
        if filter_to:
            filename += f'_to_{datetime.strftime(filter_to, date_format_trunc)}'
        filename += '.json'

        def __filter(review, date_from, date_to, filter_format):
            """Returns true if review's date is within range of the filters."""
            date_val = datetime.strptime(review['date'], filter_format)
            return bool(date_from <= date_val <= date_to)

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

            if filter_from or filter_to:
                if not filter_to:
                    filter_to = datetime.now()
                if not filter_from:
                    filter_from = datetime.min

                for n in rev100:
                    if __filter(n, filter_from, filter_to, date_format):
                        reviews_list.append(n)
                    else:
                        num_reviews += 1
            else:
                for n in rev100:
                    reviews_list.append(n)

            if len(api_r['reviews']) < 100:
                break

        # Quick lambda sort - primarily by date, secondarily by ID
        reviews_list.sort(key=lambda x: (datetime.strptime(x['date'], date_format), x['id']))

        print(f"{len(reviews_list)} reviews for {self.game_name} retrieved successfully.")

        if json:
            with open(filename, 'w+', encoding='utf-8') as outf:
                js.dump(reviews_list, outf, ensure_ascii=False)
                print(f"Committed review list to {filename}.")

        return reviews_list


class Scraper:
    """Class for handling scraping information from the Steam store page directly."""

    def __init__(self, appid=220):
        self.appid = appid
        self.__update()

    def __update(self):
        """Updates HTML parser when appID is changed."""
        store_page = requests.get(f"https://store.steampowered.com/app/{self.appid}/").text
        self.parser = BeautifulSoup(store_page, 'html.parser')

    def __retrieve_storepage_data(self, class_name):
        """
        Retrieves information in a given HTML div class.
        :param class_name: name of HTML div class to retrieve data from
        :return: list of text in requested divs, unless none exist, then None
        """
        divs = self.parser.find_all("div", {"class": class_name})
        return [x.text for x in divs][:1][0] if divs else None  # these look ugly so fix them

    def retrieve_franchise(self):
        """
        Retrieves franchise name of Scraper's appid.
        :return: Franchise name in string format
        """
        pattern = 'entire (.*?) [Ff]ranchise'
        storepage_divs = self.__retrieve_storepage_data(class_name="franchise_name")
        return re.search(pattern, storepage_divs).group(1) if storepage_divs else None

    def retrieve_appname(self):
        """
        Retrieves app name of Scraper's appid.
        :return: App name in string format
        """
        return self.__retrieve_storepage_data(class_name="apphub_AppName")

    def set_appid(self, n_appid):
        """
        Sets new appid for Scraper object.
        :param n_appid: New appid
        """
        self.appid = int(n_appid)
        self.__update()

    def get_appid(self):
        """
        Returns appid for Scraper object.
        :return: App ID as int
        """
        return self.appid
