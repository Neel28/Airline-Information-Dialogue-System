import json, copy
from datetime import datetime
from enum import Enum
from typing import Union, Generator, Tuple

import sys, re

from nlu.ResolveAirport import find_matches
# from nlu.nlu import extract_info
from dialogue.manager import Manager, DialogueTurn
from dialogue.field import Field, NumField, NumCategory
from nlg.nlg import Speaker
from nlg.results_verbalizer import verbalize
from qpx_database import QPXDatabase

OutputType = Enum('OutputType', 'greeting progress error feedback question finish review')


class Output:
    def __init__(self,
                 lines: [str] = [],
                 output_type: Enum = OutputType.greeting,
                 question: str = "",
                 extra_data: {str: str} = {}):
        self.lines = lines
        self.output_type = output_type
        self.question = question
        self.extra_data = extra_data


class Pipeline:
    def __init__(self):
        Destination = Field("Destination", ["destination"])
        Origin = Field("Origin", ["origin"])
        DepartureDate = Field("Departure Date", ["departureDate"])
        ArrivalDate = Field("Arrival Date", ["arrivalDate"])
        NonStop = Field("NonStop", ["nonstop"])
        Price = NumField("Price",
                         ["price"],
                         [NumCategory("cheap", 0, 250),
                          NumCategory("moderate", 250, 1400),
                          NumCategory("expensive", 1400, sys.maxsize)],
                         # parse price from string, e.g. "USD83.10"
                         lambda raw: float(re.match(".*?([0-9\.]+)", raw).group(1)))
        Carrier = Field("Carrier", ["carriers"])
        Cabin = Field("Cabin Class", ["cabins"])
        self.manager = Manager(
            available_fields=[
                Destination,
                Origin,
                DepartureDate,
                ArrivalDate,
                NonStop,
                Price,
                Carrier,
                Cabin
            ],
            minimal_fields=[
                Destination.name, Origin.name, DepartureDate.name
            ],
            database=QPXDatabase())
        self.speaker = Speaker(self.manager)
        self.last_question = None
        self.expected_answer = None
        self.question_counter = 0

    def user_state(self) -> {str: [(Union[str, int, float], float)]}:
        return self.manager.user_state

    def generate_question(self):
        self.last_question, self.expected_answer = self.manager.next_question()
        self.question_counter += 1

    def show_status(self, status: Tuple[bool, Union[str, int]]) -> Generator[Output, None, None]:
        if status[1] is not None and status[1] == 1:
            yield Output(lines=["I found the perfect flight for you!"]
                               + verbalize(self.manager.possible_data, 2),
                         output_type=OutputType.finish,
                         extra_data={"status": status})
        else:
            feedback = self.speaker.inform(status)
            yield Output(lines=feedback, output_type=OutputType.feedback, extra_data={"status": status})

    def interpret_statement(self, statement: {str: str}) -> Generator[Output, None, bool]:
        status = None
        direct_nlu_matches = {
            "out_date": "Departure Date",
            "in_date": "Arrival Date",
            "cabin_class": "Cabin Class",
        }
        for key, value in statement.items():
            if key == 'o_location' or key == 'o_entity':
                yield Output(lines=["Resolving origin airport code..."], output_type=OutputType.progress)
                airports = find_matches(value)
                status = yield from self.manager.inform("Origin", airports)
            elif key == 'd_location' or key == 'd_entity':
                yield Output(lines=["Resolving destination airport code..."], output_type=OutputType.progress)
                airports = find_matches(value)
                status = yield from self.manager.inform("Destination", airports)
            elif (key == 'u_location' or key == 'u_entity') and self.last_question.name in ["Origin", "Destination"]:
                which = self.last_question.name
                yield Output(lines=["Resolving %s airport code..." % which.lower()],
                             output_type=OutputType.progress)
                airports = find_matches(value[0])
                status = yield from self.manager.inform(which, airports)
            elif key in direct_nlu_matches:
                status = yield from self.manager.inform(direct_nlu_matches[key], [(value, 1)])
            elif key == "u_date" and self.last_question.name in ["Departure Date", "Arrival Date"]:
                status = yield from self.manager.inform(self.last_question.name, [(value, 1)])
            elif key == "airlines":
                airlines = []
                for airline in value:
                    airlines.append((airline, 1))
                status = yield from self.manager.inform("Carrier", airlines)
            elif key == "qualifiers":
                price_qualifiers = ["cheap", "moderate", "expensive"]
                price_settings = []
                for qualifier in value:
                    if qualifier in price_qualifiers:
                        price_settings.append((qualifier, 1))
                if len(price_settings) > 0:
                    status = yield from self.manager.inform("Price", price_settings)
                else:
                    print("Could not interpret qualifiers", value)

        if status is not None:
            yield from self.show_status(status)
            return True
        return False

    # show review data for airports / airlines, if available
    def interpret_question(self, question: {str: str}) -> Generator[Output, None, bool]:
        from nlu.airport import find_airport_by_code, find_airport_wordcloud
        from nlu.airline import find_airline_by_code, find_airline_wordcloud

        print("Interpreting question", question)
        for key, value in question.items():
            if key == 'u_location' or key == 'u_entity':
                for v in value:
                    for code, _ in find_matches(v):
                        airport = find_airport_by_code(code)
                        if airport is None:
                            print("Could not extract airport from", code)
                            continue
                        wordcloud = find_airport_wordcloud(airport)
                        if wordcloud is None:
                            print("Could not find wordcloud for airport", airport["Name"])
                            continue
                        print("Found airport", airport, wordcloud)
                        yield Output(lines=[], output_type=OutputType.review, question="", extra_data={
                            "type": "airport-review",
                            "airport": "%s (%s)" % (airport["Name"], airport["Code"]),
                            "image": wordcloud
                        })
                        return True
            elif key == "airlines":
                for v in value:
                    airline = find_airline_by_code(v)
                    if airline is None:
                        print("Could not extract airline from", v)
                        continue
                    wordcloud = find_airline_wordcloud(airline)
                    if wordcloud is None:
                        print("Could not find wordcloud for airline", airline["Name"])
                        continue
                    print("Found airline", airline, wordcloud)
                    yield Output(lines=[], output_type=OutputType.review, question="", extra_data={
                        "type": "airline-review",
                        "airline": airline['Name'],
                        "image": wordcloud
                    })
                    return True

        return False

    # matches utterance to expected values using fuzzy string matching
    def match_expected(self, utterance: str) -> [Tuple[str, float]]:
        from difflib import SequenceMatcher

        def score(a: str, b: str) -> float:
            return SequenceMatcher(None, a.lower(), b.lower()).ratio()

        return list(map(lambda x: (x, score(utterance, x)), self.expected_answer.keys()))

    def input(self, utterance: str) -> Generator[Output, None, None]:
        if self.last_question is None:
            yield from self.output()

        yield Output(lines=["Loading NLU libraries..."],
                     output_type=OutputType.progress)
        from nlu.nlu import extract_info
        extracted = extract_info(utterance)
        utterance = utterance.lower()
        print('Utterance:', utterance)
        print('Extracted:', extracted)
        self.manager.interaction_sequence.append(
            DialogueTurn("input",
                         {
                             "utterance": utterance,
                             "extracted": copy.deepcopy(extracted)
                         },
                         datetime.now()))
        status = None

        if extracted["dialog_act"] == "statement":
            del extracted["dialog_act"]
            succeeded = yield from self.interpret_statement(extracted)
            if not succeeded:
                print('Failed to extract statement information from utterance. '
                      'Trying to recover by inferring context from last question.')
                if self.last_question is not None:
                    if self.last_question.name in ["Origin", "Destination"]:
                        which = self.last_question.name
                        yield Output(lines=["Resolving %s airport code..." % which.lower()],
                                     output_type=OutputType.progress)
                        airports = find_matches(utterance)
                        status = yield from self.manager.inform(which, airports)
                    else:
                        try:
                            matches = self.match_expected(utterance)
                            status = yield from self.manager.inform(self.last_question, matches)
                        except Exception as e:
                            print("Could not match to expected values.", e)
                            yield Output(lines=["Sorry, I didn't get that."],
                                         output_type=OutputType.error)

        elif extracted["dialog_act"] == "question":
            del extracted["dialog_act"]
            question_interpreted = yield from self.interpret_question(extracted)
            if not question_interpreted:
                yield Output(lines=["Sorry, I didn't understand your question."],
                             output_type=OutputType.error)
            yield from self.output()
            return

        elif self.last_question is not None:
            if extracted["dialog_act"] in ["yes", "no"]:
                print("YESNO")
                print(extracted)
                status = yield from self.manager.inform(self.last_question,
                                                        [(str(extracted["dialog_act"] == "yes"), 1)])

        if status is not None:
            yield from self.show_status(status)
            if status[1] == 0 and status[0]:
                print("Found no flights.")
                return

        # if self.last_question.name == 'Origin' or self.last_question.name == 'Destination':
        #     yield Output(lines=["Resolving %s airport code..." % self.last_question.name], output_type=OutputType.progress)
        #     answer = find_matches(utterance)
        # else:
        #     answer = [(utterance, 1)]

        # did we find the perfect flight?
        if status is not None and status[1] is not None and status[1] == 1:
            self.show_status(status)
            return

        print("Asking question despite status =", json.dumps(status))
        self.generate_question()
        if self.last_question is None and len(self.manager.possible_data) > 0:
            # no problem, we have some flights but just ran out of questions
            json.dump({"data": self.manager.possible_data}, open("possible_data.json", "w"), indent=4)
            # yield Output(
            #     lines=verbalize(self.manager.possible_data, 5),
            #     output_type=OutputType.finish)  # TODO finish is not quite right
        else:
            yield Output(
                lines=[self.speaker.ask(self.last_question, self.expected_answer)],
                output_type=OutputType.question)

    # Conversational output with no user input, and repeating last question
    def output(self) -> Generator[Output, None, None]:
        if self.question_counter == 0:
            self.generate_question()
            yield Output([
                "Hello!",
                "I'm your personal assistant for helping you find the best flight 😊"
            ])
        yield Output(
            lines=[self.speaker.ask(self.last_question, self.expected_answer)],
            output_type=OutputType.question)
