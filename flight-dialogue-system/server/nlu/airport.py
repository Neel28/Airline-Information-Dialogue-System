import glob, json, os
from typing import Union

import sys

available_airports = json.load(open(os.path.dirname(__file__) + "/airports2.json", "r", encoding="utf8"))


def find_airport_by_code(code: str) -> Union[None, object]:
    code = code.upper()
    for airport in available_airports:
        if airport["Code"] == code:
            return airport
            # {
            #     "Country": "United States",
            #     "Code": "00AK",
            #     "Region": "Alaska",
            #     "GPS_Code": "00AK",
            #     "Name": "Lowell Field",
            #     "City": "Anchor Point",
            #     "Size": 1
            # }
    return None


def find_airport_wordcloud(airport: {str: str}) -> Union[None, str]:
    name = airport["Name"].replace(" ", "-").lower()
    code = airport["Code"].replace(" ", "-").lower()
    country = airport["Country"].replace(" ", "-").lower()
    city = airport["City"].replace(" ", "-").lower()
    print("Airport name", name)
    print("Airport code", code)
    print("Airport city", city)
    for filename in glob.glob('static/airport_wordclouds/*-airport.png'):
        base = os.path.splitext(os.path.basename(filename))[0]
        if base == name:
            return filename
        base_pure = base.replace("-airport", "")
        if base_pure == city:
            return filename
        if base_pure == "%s-%s" % (city, code):
            return filename
    return None
