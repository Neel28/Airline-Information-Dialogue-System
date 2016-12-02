import sys, json, numbers, os
from difflib import SequenceMatcher
from colorama import Fore

FUZZ_RATIO = 1.

resolved = False

available_options = json.load(open(os.path.dirname(__file__) + "/airports2.json", "r", encoding="utf8"))

column_scores = {
    "Name": 1.0,
    "Region": 0.4,
    "Country": 0.3,
    "City": 1.8,
    "Code": 1.4,
    "GPS_Code": 0.3
}


# similarity score between 0 and 1
def score(a, b):
    # fuzz.partial_ratio(a, b) / 100. #
    return SequenceMatcher(None, a, b).ratio()


# resolves airport codes from eny string and returns list of matching
# airport codes with confidence scores
def find_matches(query: str) -> [(str, float)]:
    query = query.lower()
    if len(query) == 3:
        for row in available_options:
            if row["Code"].lower() == query:
                print("Airport could be directly resolved from code %s." % row["Code"])
                return [(row["Code"], 1)]
    matches = []
    for row in available_options:
        row_score = 0
        row_multiplier = 1.  # higher weights for airports with IATA_FAA or ICAO number
        row_multiplier *= row["Size"]
        applicable_values = 0
        for key, value in row.items():
            if key == "Code" and (value is None or value == ""):
                row_multiplier *= 0.05
                break
            if key not in ["Name", "Region", "Country", "City", "Code"]:
                continue
            if value is None or isinstance(value, numbers.Number):
                continue
            value = value.lower()
            column_score = column_scores[key]
            row_score += score(value, query) * column_score
            # equivalent partial matches:
            for word in query.split():
                if word in value:
                    # print("Partial match between %s and %s" % (value, query))
                    row_score += len(word) / len(query.split()) * column_score

            for w1,w2 in zip(query.split(), query.split()[1:]):
                word = "%s %s" % (w1, w2)
                if word in value:
                    row_score += len(word) / len(query.split()) * column_score
            if query == value:
                print(Fore.LIGHTBLACK_EX + "Exact match for airport %s %s of %s." % (key, row[key], row["Name"]) + Fore.BLACK)
                row_score += 50 if key == "Code" else 20
            applicable_values += 1.
        if applicable_values > 0:
            row_score *= row_multiplier / applicable_values
            if row_score > FUZZ_RATIO:
                matches.append((row["Code"], row_score))
    return sorted(matches, key=lambda entry: entry[1], reverse=True)


def main(argv):
    global resolved

    while True:
        query = input("What fact do you know about the airport? ")
        matches = find_matches(query)
        if len(matches) == 0:
            print(Fore.RED + "Found no matches." + Fore.BLACK)
        else:
            print("Found %i matches." % len(matches))
            print("Top %i matches are:\n\t%s" % (min(10, len(matches)), "\n\t".join(
                ["%.3f %s (%s, %s)" % (row[0], row[1]["Name"], row[1]["Region"], row[1]["Country"]) for row in matches[:10]])))
        if len(matches) >= 2:
            # print most likely airport if the score is much better than the second best
            if matches[0][0] - matches[1][0] > 0.2:
                print(Fore.GREEN + "You probably mean %s (%s)." % (
                    matches[0][1]["Name"], matches[0][1]["Code"]) + Fore.BLACK)

                # while not resolved:


if __name__ == "__main__":
    main(sys.argv)
