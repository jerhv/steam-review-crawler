## crawler.py

A Python script for crawling for reviews of a given Steam application and exporting salient information to a JSON file.

### Instructions:
Install python packages with pip using requirements.txt (in commandline, pip3 install -r requirements.txt)

Crawler script can then be run using Python. The code has been written and tested in Python 3 only. (in commandline, python crawler.py)

The script will require a Steam AppID as a parameter. (e.g. python crawler.py 1382330)

Optional date filters can be added with the "--filter_from" and "--filter_to flags", in the YYYY-MM-DD format (e.g. python crawler.py 1382330 --filter_from="2021-02-02")

The optional flag "--no-json" will make the script not save the list of reviews into a json file, and will instead print the list to standard output.

All of this information is also available using the "-h" or "--help" flags.

The unit tests can also be run with the commandline - python -m unittest test_crawler.py
