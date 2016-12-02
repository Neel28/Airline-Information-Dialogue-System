import codecs, json, random
from collections import Counter
from operator import itemgetter

import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib import gridspec

from system import Pipeline
from dialogue.manager import Manager
from nlu.ResolveAirport import find_matches

CITIES = [
    "Los Angeles",
    "Brussels",
    "Dubai",
    "New York",
    "Berlin",
    "Amsterdam",
    "Bangalore",
    "London",
    "Hong Kong",
    "Tokyo",
    "Beijing",
    "San Francisco",
    "Atlanta",
    "Houston",
    "Paris",
    "Madrid",
    "Oslo",
    "Stockholm",
    "Copenhagen",
    "Dublin",
    "Melbourne",
    "Singapore",
    "Vienna"
]

FROM_TO = [["Houston", "Oslo"], ["New York", "Dubai"], ["Amsterdam", "Los Angeles"], ["Melbourne", "Copenhagen"], ["Amsterdam", "Singapore"], ["Bangalore", "Brussels"], ["New York", "Tokyo"], ["Atlanta", "London"], ["Beijing", "Atlanta"], ["New York", "Atlanta"], ["Dubai", "Berlin"], ["Los Angeles", "Bangalore"], ["Berlin", "Dublin"], ["Los Angeles", "Atlanta"], ["New York", "Singapore"], ["Bangalore", "Oslo"], ["Vienna", "Dublin"], ["Dublin", "Tokyo"], ["Berlin", "Vienna"], ["Los Angeles", "Brussels"], ["Madrid", "Berlin"], ["San Francisco", "Madrid"], ["Singapore", "Melbourne"], ["New York", "Tokyo"], ["Copenhagen", "Dublin"], ["Tokyo", "Madrid"], ["Brussels", "Amsterdam"], ["Singapore", "Bangalore"], ["Dublin", "Tokyo"], ["Singapore", "Houston"], ["Amsterdam", "Hong Kong"], ["Bangalore", "Tokyo"], ["Houston", "Stockholm"], ["Amsterdam", "Dubai"], ["Atlanta", "Hong Kong"], ["Tokyo", "Singapore"], ["Beijing", "Tokyo"], ["Tokyo", "Beijing"], ["Amsterdam", "Stockholm"], ["Berlin", "New York"], ["Madrid", "Oslo"], ["Dubai", "Brussels"], ["Los Angeles", "Brussels"], ["Houston", "Dubai"], ["Hong Kong", "Dubai"], ["Melbourne", "Dubai"], ["Melbourne", "Madrid"], ["Bangalore", "Vienna"], ["San Francisco", "Beijing"], ["Copenhagen", "Vienna"], ["Los Angeles", "San Francisco"], ["Brussels", "Amsterdam"], ["Melbourne", "Singapore"], ["Los Angeles", "Brussels"], ["Singapore", "Dubai"], ["New York", "Stockholm"], ["Paris", "San Francisco"], ["Madrid", "Brussels"], ["Dubai", "Paris"], ["Oslo", "Amsterdam"], ["Copenhagen", "Berlin"], ["Dublin", "Singapore"], ["Melbourne", "Amsterdam"], ["Brussels", "Copenhagen"], ["Hong Kong", "Dublin"], ["Bangalore", "Paris"], ["Amsterdam", "Houston"], ["San Francisco", "Brussels"], ["Dubai", "Melbourne"], ["San Francisco", "Dubai"], ["Paris", "San Francisco"], ["Dubai", "Madrid"], ["Amsterdam", "Paris"], ["Beijing", "Dubai"], ["Oslo", "Houston"], ["Singapore", "Berlin"], ["Madrid", "Bangalore"], ["Brussels", "New York"], ["Amsterdam", "Melbourne"], ["San Francisco", "Dublin"], ["New York", "Singapore"], ["Beijing", "Melbourne"], ["Hong Kong", "Berlin"], ["Hong Kong", "Bangalore"], ["Madrid", "Bangalore"], ["Tokyo", "Dublin"], ["Madrid", "Los Angeles"], ["Vienna", "San Francisco"], ["Stockholm", "Copenhagen"], ["Beijing", "San Francisco"], ["Houston", "Bangalore"], ["Madrid", "Hong Kong"], ["Copenhagen", "London"], ["San Francisco", "Dubai"], ["New York", "Singapore"], ["Los Angeles", "Berlin"], ["Madrid", "Dubai"], ["Berlin", "London"], ["Houston", "Paris"], ["Atlanta", "Houston"]]


def test_dialogue(manager: Manager, origin, destination):
    global CITIES
    random.shuffle(CITIES)
    print("\tFlying from %s to %s" % (CITIES[0], CITIES[1]))
    question = "Departure Date"
    answer = [("2016-12-09", 1)]
    yield from manager.inform(question, answer)
    yield {
        "question": question,
        "answer": answer,
        "available": [],
        "flights": 0
    }

    question = "Origin"
    answer = find_matches(origin)
    yield from manager.inform(question, answer)
    yield {
        "question": question,
        "answer": answer,
        "available": [],
        "flights": 0
    }

    question = "Destination"
    answer = find_matches(destination)
    _, flights = yield from manager.inform(question, answer)
    yield {
        "question": question,
        "answer": answer,
        "available": [],
        "flights": flights
    }

    while True:
        question, available = manager.next_question()
        print("Question:", question)
        if question is None:
            break
        # choose random answer
        answer = [(random.choice(list(available.keys())), 1)]
        success, flights = yield from manager.inform(question, answer)
        print("\tAnswering %s with %s: %i flights." % (question, answer, flights))
        if not success:
            break
        yield {
            "question": str(question),
            "answer": answer[0][0],
            "available": available,
            "flights": flights
        }


def plot():
    results = json.load(codecs.open("test_dialog_questions.json", "r", encoding="utf-8"))

    plt.figure("Dialogue Options Discrimination")

    plt.subplot(1, 2, 1)
    plt.title("Evolution of Flight Options")
    plt.ylabel("Flight options")
    plt.xlabel("Question")
    for dialogue in results["dialogues"]:
        x = range(1, len(dialogue)+1)
        y = list(map(lambda d: d["flights"], dialogue))[2:]
        plt.plot(x[2:], y)

    plt.subplot(1, 2, 2)
    plt.title("Evolution of Flight Options")
    plt.ylabel("Dialogs")
    plt.xlabel("Question")
    axes = plt.gca()
    axes.set_ylim([0, len(results["dialogues"])])
    N = 8
    x = range(N)
    plt.bar(x[3:], ([len(results["dialogues"])]*N)[3:], color="grey")
    y3 = [0] * N
    for q in range(N):
        y3[q] = len(list(filter(lambda d: (len(d)<=q and d[-1]["flights"] <= 5) or (len(d)>q and d[q]["flights"] <= 5), results["dialogues"])))
    plt.bar(x[3:], y3[3:], color="blue", label="<= 5 options")
    y2 = [0] * N
    for q in range(N):
        y2[q] = len(list(filter(lambda d: (len(d)<=q and d[-1]["flights"] <= 2) or (len(d)>q and d[q]["flights"] <= 2), results["dialogues"])))
    plt.bar(x[3:], y2[3:], color="orange", label="<= 2 options")
    y1 = [0] * N
    for q in range(N):
        y1[q] = len(list(filter(lambda d: (len(d)<=q and d[-1]["flights"] <= 1) or (len(d)>q and d[q]["flights"] <= 1), results["dialogues"])))
    plt.bar(x[3:], y1[3:], color="red", label="1 option")
    plt.legend(loc=4)
    plt.show()


def main():
    # experiment = {
    #     "dialogues": []
    # }
    # for i in range(33):
    #     print("Dialogue", i)
    #     pipeline = Pipeline()
    #     turns = list(filter(lambda x: "question" in x, test_dialogue(pipeline.manager, FROM_TO[i][0], FROM_TO[i][1])))
    #     print(turns)
    #     experiment["dialogues"].append(turns)
    #
    # json.dump(experiment, codecs.open("test_dialog_questions.json", "w", encoding="utf-8"), indent=4)

    plot()
