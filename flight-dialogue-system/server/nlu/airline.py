import csv, glob, os
from typing import Union


def find_airline_by_code(code: str) -> Union[None, object]:
    airline_reader = csv.reader(open('nlu/airline_names.csv', 'r'), delimiter=',', quotechar='"')
    code = code.upper()
    for airline in airline_reader:
        if airline[3].upper() == code:
            return {
                "Code": code,
                "Name": airline[1],
                "Country": airline[6],
                "Short": airline[5]
            }
    return None


def find_airline_wordcloud(airline: {str: str}) -> Union[None, str]:
    name = airline["Name"].replace(" ", "-").lower()
    for filename in glob.glob('static/airline_wordclouds/*.png'):
        base = os.path.splitext(os.path.basename(filename))[0]
        if base == name:
            return filename
    return None
