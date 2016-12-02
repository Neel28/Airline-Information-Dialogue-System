from collections import namedtuple
from typing import Union, Generator, Tuple
from datetime import datetime

import sys

# from database import Database
# from field import Field
from dialogue.database import Database
from dialogue.field import Field

MAX_DATA = 2500


DialogueTurn = namedtuple("DialogueTurn", ["type", "data", "time"])


class Manager:
    # constructs dialogue manager using all available attributes and names of
    # the minimal attributes to generate a query to the knowledge base
    def __init__(self, available_fields: [Field], minimal_fields: [str], database: Database):
        self.available_fields = {}
        for field in available_fields:
            self.available_fields[field.name] = field

        self.minimal_fields = minimal_fields
        self.user_state = {}  # {str: [(Union[str,int,float], float)]}
        self.database = database

        self.possible_data = []  # [object]
        self.asked_questions = set()  # set of field names

        self.interaction_sequence = []

    # determines whether the minimal fields have been completed
    def sufficient(self) -> bool:
        for f in self.minimal_fields:
            if f not in self.user_state:
                return False
        return True

    # returns attribute name + expected values
    def next_question(self) -> (Field, {str: int}):
        # first complete the minimal fields (if they haven't been filled)
        for name in self.minimal_fields:
            if name not in self.user_state:
                self.interaction_sequence.append(
                    DialogueTurn("question", name, datetime.now())
                )
                return self.available_fields[name], None

        # if we have data, choose best question based on scored entropy
        fields = list(self.available_fields.values())
        best_field = None
        best_entropy = sys.maxsize
        for field in fields[1:]:
            if field.name in self.asked_questions:
                continue
            entropy = field.entropy(self.possible_data)
            if 1e-10 < entropy < best_entropy:
                best_entropy = entropy
                best_field = field

        if best_field is None:
            return None, None

        self.asked_questions.add(best_field.name)
        self.interaction_sequence.append(
            DialogueTurn("question", best_field.name, datetime.now())
        )
        return best_field, best_field.category_count(self.possible_data)

    # provides information via attribute name + values with confidence scores
    # returns False, error message if something went wrong
    # otherwise True, number of possible flights
    def inform(self, attribute: Union[str, Field], values: [(str, float)]) -> Generator[str, None, Tuple[bool, Union[str, int]]]:
        self.interaction_sequence.append(
            DialogueTurn("answer", (attribute, values), datetime.now())
        )
        if len(values) == 0:
            return False, 'no attribute values provided'
        if not isinstance(attribute, str):
            attribute = attribute.name
        if len(values) > 1:
            pruned = self.available_fields[attribute].prune(values)
            print('Pruned %i values to %i.' % (len(values), len(pruned)))
            values = pruned
        self.user_state[attribute] = values

        yield "Updating data..."
        updated = yield from self.update()
        return True, updated

    # provides feedback to a question which updates the attribute's score
    def feedback(self, attribute: str, positive: bool):
        self.interaction_sequence.append(
            DialogueTurn("feedback", (attribute, positive), datetime.now())
        )
        self.available_fields[attribute].score *= 1.1 if positive else 0.9
        pass

    def filter_possible(self, raw_data: [object]) -> [object]:
        filtered = []
        for data_entry in raw_data:
            state_agrees = True
            for key, values in self.user_state.items():
                categories, _ = self.available_fields[key].filter(data_entry)
                found_matching_value = False
                for value, _ in values:
                    for cat in categories:
                        if str(value).lower() == str(cat).lower():
                            found_matching_value = True
                            break
                if not found_matching_value:
                    state_agrees = False
                    break
            if state_agrees:
                filtered.append(data_entry)
        return filtered

    # updates and returns number of possible flights
    # returns None if the minimal set of attributes has not been filled so far
    def update(self) -> Generator[str, None, Union[None, int]]:
        if not self.sufficient():
            return None

        self.possible_data.clear()

        query_items = self.user_state.items()
        # keeps track of current index of value to query per attribute
        open_queries = [(attribute, len(values)-1) for attribute, values in query_items]
        while all(index >= 0 for _, index in open_queries):
            query = {}
            for attribute, index in open_queries:
                query[attribute] = self.user_state[attribute][index][0]
            results = self.database.query(query)
            if results is not None:
                self.possible_data += self.filter_possible(results)

            if len(self.possible_data) > MAX_DATA:
                break
            updated = False
            for i, (attribute, index) in enumerate(open_queries):
                if not updated and index > 0:
                    yield "Querying database with %s = %s..." % (attribute, self.user_state[attribute][index-1][0])
                    open_queries[i] = attribute, index-1
                    updated = True
                    break
            if not updated:
                break

        yield "Updating user state with new flights data..."
        self.update_user_state()

        return len(self.possible_data)

    # remove values from user state that do not appear in the available flights data
    def update_user_state(self):
        if len(self.possible_data) == 0:
            return
        for key, values in self.user_state.items():
            existing_values = set()
            for data_entry in self.possible_data:
                categories, _ = self.available_fields[key].filter(data_entry)
                for cat in categories:
                    existing_values.add(cat)
            nvalues = []
            for existing in existing_values:
                for value, score in values:
                    if str(existing).lower() == str(value).lower():
                        nvalues.append((value, score))
            self.user_state[key] = nvalues
