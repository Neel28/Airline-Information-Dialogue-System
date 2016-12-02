import codecs, json
from collections import Counter
from operator import itemgetter

import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib import gridspec

from server.nlu.airport import available_airports
from server.nlu.ResolveAirport import find_matches
import random


def test_country_city(airports, remove_characters=1):
    avg_position = 0
    for airport in airports:
        found = False
        query = "{City:s}, {Country:s}".format(**airport)
        for i in range(remove_characters):
            remove = random.randint(0, len(query))
            query = query[:remove] + query[remove+1:]
        print("Query: \"%s\"" % query)
        for position, (code, score) in enumerate(find_matches(query)):
            if code == airport["Code"]:
                print("Found airport %s at position %i." % (code, position))
                yield position
                found = True
                break
        if not found:
            print("Could not find airport %s." % airport["Code"])
            yield -1
    avg_position /= len(airports)
    return avg_position


def test_city(airports, remove_characters=1):
    avg_position = 0
    for airport in airports:
        found = False
        query = airport["City"]
        for i in range(remove_characters):
            remove = random.randint(0, len(query))
            query = query[:remove] + query[remove+1:]
        print("Query: \"%s\"" % query)
        for position, (code, score) in enumerate(find_matches(query)):
            if code == airport["Code"]:
                print("Found airport %s at position %i." % (code, position))
                yield position
                found = True
                break
        if not found:
            print("Could not find airport %s." % airport["Code"])
            yield -1
    avg_position /= len(airports)
    return avg_position


def test_name(airports, remove_characters=1):
    avg_position = 0
    for airport in airports:
        found = False
        query = airport["Name"]
        for i in range(remove_characters):
            remove = random.randint(0, len(query))
            query = query[:remove] + query[remove+1:]
        print("Query: \"%s\"" % query)
        for position, (code, score) in enumerate(find_matches(query)):
            if code == airport["Code"]:
                print("Found airport %s at position %i." % (code, position))
                yield position
                found = True
                break
        if not found:
            print("Could not find airport %s." % airport["Code"])
            yield -1
    avg_position /= len(airports)
    return avg_position


def plot():
    results = json.load(codecs.open("test_resolve_airports.json", "r", encoding="utf-8"))
    airport_sizes = set(map(lambda ex: ex["airport_size"], results["experiments"]))
    remove_chars = set(map(lambda ex: ex["remove_characters"], results["experiments"]))
    num_plots = len(airport_sizes) * len(remove_chars)
    print("Plots:", num_plots)

    fig = plt.figure("Resolve Airports Results", figsize=(20, 5))
    gs = gridspec.GridSpec(len(airport_sizes), len(remove_chars)*3)
    #main_ax = fig.gca()
    n = 0
    for ai, airport_size in enumerate(sorted(airport_sizes)):
        for ri, remove_char in enumerate(sorted(remove_chars)):
            experiment = list(filter(lambda ex: ex["airport_size"] == airport_size
                                                and ex["remove_characters"] == remove_char,
                                     results["experiments"]))[0]

            ax = fig.add_subplot(gs[n])
            ax.set_aspect('equal')

            explode = [0]
            values = [0]
            labels = [0]
            ax.set_title("%s\nairport size: %i\nremove chars: %i" % ("name", airport_size, remove_char))
            for position, frequency in sorted(list(experiment["name"].items()), key=lambda x: x[0]):
                if position == "0":
                    explode[0] = 0.1
                    values[0] = frequency
                else:
                    explode.append(0)
                    values.append(frequency)
                    labels.append("N/A" if position == "-1" else position)
            ax.pie(values, labels=labels, explode=explode, startangle=0)
            n += 1

            ax = fig.add_subplot(gs[n])
            ax.set_aspect('equal')

            explode = [0]
            values = [0]
            labels = [0]
            ax.set_title("%s\nairport size: %i\nremove chars: %i" % ("city", airport_size, remove_char))
            for position, frequency in sorted(list(experiment["city"].items()), key=lambda x: x[0]):
                if position == "0":
                    explode[0] = 0.1
                    values[0] = frequency
                else:
                    explode.append(0)
                    values.append(frequency)
                    labels.append("N/A" if position == "-1" else position)
            ax.pie(values, labels=labels, explode=explode, startangle=0)
            n += 1

            ax = fig.add_subplot(gs[n])
            ax.set_aspect('equal')

            explode = [0]
            values = [0]
            labels = [0]
            ax.set_title("%s\nairport size: %i\nremove chars: %i" % ("country_city", airport_size, remove_char))
            for position, frequency in sorted(list(experiment["country_city"].items()), key=lambda x: x[0]):
                if position == "0":
                    explode[0] = 0.1
                    values[0] = frequency
                else:
                    explode.append(0)
                    values.append(frequency)
                    labels.append("N/A" if position == "-1" else position)
            ax.pie(values, labels=labels, explode=explode, startangle=0)
            n += 1

    fig.tight_layout()
    plt.show()


if __name__ == '__main__':
    results = {
        "experiments": []
    }
    random.shuffle(available_airports)
    sample_size = 20
    for size in range(1, 4):
        for remove_characters in range(3):
            experiment = {
                "airport_size": size,
                "remove_characters": remove_characters,
                "sample_size": sample_size
            }
            print(json.dumps(experiment, indent=4))

            selection = list(filter(lambda ap: ap["Size"] == size
                                               and len(ap["Code"]) == 3
                                               and len(ap["City"]) > 3 + remove_characters,
                                    available_airports))

            airports = selection[:sample_size]

            counts = dict(Counter(test_name(airports, remove_characters)))
            experiment["name"] = counts
            print(counts)
            counts = dict(Counter(test_country_city(airports, remove_characters)))
            experiment["country_city"] = counts
            print(counts)
            counts = dict(Counter(test_city(airports, remove_characters)))
            experiment["city"] = counts
            print(counts)
            results["experiments"].append(experiment)
            json.dump(results, codecs.open("test_resolve_airports.json", "w", encoding="utf-8"), indent=4)

    json.dump(results, codecs.open("test_resolve_airports.json", "w", encoding="utf-8"), indent=4)

    plot()
