import json, random
from collections import defaultdict
from typing import Union

from dialogue.field import Field
from dialogue.manager import Manager
from nlg.results_verbalizer import verbalize
from nlg.results_verbalizer import lookup_airline_name

generic_what_questions = [
    "Can you please tell me your desired %s?",
    "Please tell me your desired %s.",
    "What is your desired %s?"
]

thanks = [
    "thanks", "thank you", "awesome", "excellent", "great", "good choice"
]

error = [
    "Oh no! ☹", "I am inconsolable... ☹", "I'm so sorry! ☹"
]

CABIN_TERMS = {
    'FIRST': 'first class',
    'BUSINESS': 'business class',
    'PREMIUM_COACH': 'premium economy',
    'COACH': 'economy',
}


class Speaker:
    def __init__(self, manager: Manager):
        self.asked = defaultdict(int)  # counts how often a question has been asked before
        self.last_question = None  # Field
        self.manager = manager

    def generic(self, what: str, additions=[]) -> str:
        choices = list(map(lambda g: g % what, generic_what_questions)) + additions
        return random.choice(choices)

    def say_list(self, l: [str]) -> str:
        if len(l) == 0:
            return ''
        if len(l) == 1:
            return l[0]
        if len(l) == 2:
            return '{l[0]} and {l[1]}'.format(l=l)
        return ', '.join(l[:-2]) + ', ' + self.say_list(l[-2:])

    def results_for_field(self, field, e) -> str:
        output = []
        if field.name == "Destination":
            output.append(" {} flights go to {}".format(e[0][1], e[0][0]))
            if len(e) > 1:
                for i in range(1, len(e) - 1):
                    output.append(", {} to {}".format(e[i][1], e[i][0]))
                output.append(", and {} to {}".format(e[-1][1], e[-1][0]))
            output.append(".")
        elif field.name == "Origin":
            output.append(" {} flights leave from {}".format(e[0][1], e[0][0]))
            if len(e) > 1:
                for i in range(1, len(e) - 1):
                    output.append(", {} from {}".format(e[i][1], e[i][0]))
                output.append(", and {} from {}".format(e[-1][1], e[-1][0]))
            output.append(".")
        elif field.name == "Departure Date":
            output.append(" {} flights depart on {}".format(e[0][1], e[0][0]))
            if len(e) > 1:
                for i in range(1, len(e) - 1):
                    output.append(", {} on {}".format(e[i][1], e[i][0]))
                output.append(", and {} on {}".format(e[-1][1], e[-1][0]))
            output.append(".")
        elif field.name == "Arrival Date":
            output.append(" {} flights arrive on {}".format(e[0][1], e[0][0]))
            if len(e) > 1:
                for i in range(1, len(e) - 1):
                    output.append(", {} on {}".format(e[i][1], e[i][0]))
                output.append(", and {} on {}".format(e[-1][1], e[-1][0]))
            output.append(".")
        elif field.name == "Cabin Class":
            output.append(" There's {} flights with seating in {}".format(
                e[0][1], CABIN_TERMS[e[0][0]]))
            if len(e) > 1:
                for i in range(1, len(e) - 1):
                    output.append(", {} in {}".format(e[i][1], CABIN_TERMS[e[i][0]]))
                output.append(", and {} in {}".format(e[-1][1], CABIN_TERMS[e[-1][0]]))
            output.append(".")
        elif field.name == "Carrier":
            if len(e) > 1:
                output.append(" I found {} flights on {}".format(e[0][1], lookup_airline_name(e[0][0])))
                for i in range(1, len(e) - 1):
                    output.append(", {} on {}".format(e[i][1], lookup_airline_name(e[i][0])))
                output.append(", and {} on {}".format(e[-1][1], lookup_airline_name(e[-1][0])))
                output.append(".")
            else:
                output.append(" All available flights are on {}.".format(lookup_airline_name(e[0])))
        elif field.name == "NonStop":
            if len(e) > 1:
                non_stop = e[0][1] if e[0][0] == "True" else e[1][1]
                with_stop = e[0][1] if e[0][0] == "False" else e[1][1]
                output.append(" {} of the {} flights I've found are non-stop.".format(non_stop, non_stop + with_stop))
            elif e[0][0] == "True":
                output.append(" All of the flights I see are non-stop.")
            elif e[0][0] == "False":
                output.append(" None of the flights I found are direct.")
        elif field.name == "Price":
            if len(e) == 1:
                output.append(" I'd say all of them are {}".format(e[0][0]))
            if len(e) > 1:
                output.append(" I'd say {} of them are {}".format(e[0][1], e[0][0]))
                for i in range(1, len(e) - 1):
                    output.append(", {} are {}".format(e[i][1], e[i][0]))
                output.append(", and {} are {}".format(e[-1][1], e[-1][0]))
            output.append(".")
        else:
            return " I found " + self.say_list(
                list(map(lambda x: '%i flights with %s = %s' % (x[1], field.name, x[0]), e)))
        return "".join(output)

    def ask(self, field: Field, expected: {str: int}) -> str:
        if field is None:
            return random.choice(error) + " I couldn't come up with another question."

        self.asked[field.name] += 1
        self.last_question = field

        hint = ""
        if expected is not None and len(expected) > 0:
            #             hint = " I found " + self.say_list(list(map(lambda x: '%i flights with %s = %s' % (x[1], field.name, x[0]), expected.items())))
            hint = self.results_for_field(field, list(expected.items()))

        if field.name == "Origin":
            return self.generic("place of departure", [
                "Where do you want to fly from?",
                "From where do you want to fly?"
            ]) + hint
        if field.name == "Destination":
            return self.generic("destination", [
                "Where do you want to fly to?"
            ]) + hint
        if field.name == "DepartureDate":
            return self.generic("date of departure", [
                "When do you want to fly?"
            ]) + hint
        if field.name == "NonStop":
            return random.choice([
                "Do you want to fly non-stop?",
                "Do you want to avoid any intermediate stops?"
            ]) + hint
        return self.generic(field.name.lower()) + hint

    # give feedback for Manager.inform()
    def inform(self, feedback: (bool, Union[str, int])) -> [str]:
        success, data = feedback
        if success:
            json.dump({"data": self.manager.possible_data}, open("possible_data.json", "w"), indent=4)
            if data is None or data < 0:
                return [random.choice(thanks).capitalize() + "! " + random.choice([
                    "Now, before I can show you some flights I need more information.",
                    "Let me gather some more information until I can show you some flights."
                ])]
            elif data == 0:
                return [random.choice(error) + " I could not find any flights matching your preferences."]
            return verbalize(self.manager.possible_data, 4)
        else:
            return [random.choice(error) + " I got a problem from my manager. He said \"%s\"." % data]
