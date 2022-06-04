from unittest import TestCase
from crawl_utils import Crawler, Scraper
import random
from datetime import datetime, timedelta
from itertools import groupby


class TestReviewCrawler(TestCase):

    def test_retrieve_json_success(self):
        c = Crawler()
        self.assertEqual(c.retrieve_reviews_json()['success'], 1)
        print("Crawler can successfully retrieve reviews from WebAPI!\n")

    def test_same_id(self):
        print("Testing if two of the same review will generate different IDs...")
        c = Crawler()
        reviews = c.retrieve_reviews_json()['reviews']
        randval = random.randint(0, len(reviews) - 1)
        rev_copy1 = c.conform_review(reviews[randval])
        print(f"Review 1:    Content: {rev_copy1['content']}, ID: {rev_copy1['id']}")
        rev_copy2 = c.conform_review(reviews[randval])
        print(f"Review 2:    Content: {rev_copy2['content']}, ID: {rev_copy2['id']}")
        self.assertEqual(rev_copy1['id'], rev_copy2['id'])
        print("Crawler can successfully generate the same ID for duplicate reviews!\n")

    def test_same_author(self):
        print("Testing if the same author will generate the same UUID...")
        c = Crawler()
        reviews = c.retrieve_reviews_json()['reviews']
        randvals = random.sample((0, len(reviews) - 1), 2)
        rev1 = reviews[randvals[0]]
        rev2 = reviews[randvals[1]]
        rev2['author'] = rev1['author']
        rev_copy1 = c.conform_review(rev1)
        print(f"Review 1:    "
              f"Content: {rev_copy1['content']}, Author: {rev1['author']['steamid']}, ID: {rev_copy1['author']}")
        rev_copy2 = c.conform_review(rev2)
        print(f"Review 2:    "
              f"Content: {rev_copy2['content']}, Author: {rev2['author']['steamid']}, ID: {rev_copy2['author']}")
        self.assertEqual(rev_copy1['author'], rev_copy2['author'])
        print(
            "Crawler can successfully generate the same UUID for the same author, even with different review content!\n")

    def test_scrape_name(self):
        print("Testing if the scraper can get the right app name...")
        s = Scraper(397740)
        real_name = "Hylics"
        self.assertEqual(s.retrieve_appname(), real_name)
        print("Scraper can retrieve the correct app name for given ID!\n")

    def test_scrape_franchise(self):
        print("Testing if the scraper can get the right franchise name...")
        s = Scraper(406550)
        real_franchise = "When They Cry"
        self.assertEqual(s.retrieve_franchise(), real_franchise)

        s.set_appid(1158310)
        real_franchise = "Crusader Kings Official"
        self.assertEqual(s.retrieve_franchise(), real_franchise)
        print("Scraper can retrieve the correct franchise name for given ID!\n")

    def test_filter(self):
        print("Testing if the reviews are can be filtered correctly by date...")
        def __gen_random_date(start_date, end_date):
            r_days = random.randrange((end_date - start_date).days)
            return start_date + timedelta(days=r_days)

        def __conv(dat):
            return datetime.strftime(dat, '%Y-%m-%d')

        def __conv_back(dat):
            return datetime.strptime(dat, '%Y-%m-%d')

        r_start = __gen_random_date((datetime.now() - timedelta(days=365)), datetime.now())
        r_end = __gen_random_date(r_start, datetime.now())

        r_start = __conv(r_start)
        r_end = __conv(r_end)

        c = Crawler().crawl_reviews(filter_from=r_start, filter_to=r_end, json=False)

        check = False
        for n in c:
            if __conv_back(r_start) <= __conv_back(n['date']) <= __conv_back(r_end):
                check = True
            else:
                check = False
                break
        self.assertTrue(check)
        print("All reviews are within filter parameters!\n")

        # generate random date for from filter - some day between today and last year
        # generate random date for to filter - some day between today and from filter
        # run crawler, check output

    def test_sorted_by_date(self):
        print("Testing if the reviews are sorted correctly by date...")
        c = Crawler()
        reviews = c.crawl_reviews(json=False)
        dates = [datetime.strptime(x['date'], '%Y-%m-%d') for x in reviews]
        dates2 = sorted(dates)
        self.assertTrue(dates2 == dates)
        print("All dates in reviews list are in order!\n")

    def test_secondary_sort(self):
        print("Testing if the reviews are sorted secondarily by id...")
        c = Crawler()
        reviews = c.crawl_reviews(json=False)

        groups = groupby(reviews, lambda x: x['date'])
        dates = []
        for k, v in groups:
            dates.append([k, sum(1 for _ in v)])

        for n in dates:
            if n[1] > 1:
                chosen = n[0]
                break
            else:
                chosen = None

        id_base = 0
        id_check = False
        for x in reviews:
            if x['date'] == chosen:
                if int(x['id']) >= id_base:
                    id_check = True
                    id_base = int(x['id'])
                else:
                    id_check = False
                    break
        self.assertTrue(id_check)
        print("Multiple reviews for given dates are sorted in list by ID!\n")
