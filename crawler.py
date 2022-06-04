from crawl_utils import Crawler
import argparse
import json as js

arg_parser = argparse.ArgumentParser(description="Crawls for Steam reviews from a given app ID.")
arg_parser.add_argument('appid', type=int, default=220,
                        help="the chosen Steam App ID")
arg_parser.add_argument('--num_reviews', type=int, default=5000,
                        help="number of reviews to retrieve")
arg_parser.add_argument('--filter_from', '--from', metavar='YYYY-MM-DD', type=str, default=None,
                        help="start filtering from this date")
arg_parser.add_argument('--filter_to', '--to', type=str, metavar='YYYY-MM-DD', default=None,
                        help="filter up to this date")
arg_parser.add_argument('--no-json', action='store_false',
                        help="flag for disabling json file output, prints to std_out instead")

args = arg_parser.parse_args()
c = Crawler().crawl_reviews(args.appid, args.num_reviews, args.filter_from, args.filter_to, args.no_json)

if not args.no_json:
    print(js.dumps(c, indent=4))

