from qpx import qpx
from dialogue.field import Field, NumField, NumCategory
import json, sys, re

# request = {
#         "request": {
#             "passengers": {
#                 "adultCount": 1
#             },
#             "slice": [
#                 {
#                     "date": "2016-12-09",
#                     "origin": "LAX",
#                     "destination": "LAS"
#                 }
#             ]
#         }
#     }
# flights = qpx.extract_flights(qpx.get_flights(request))
# json.dump(flights, open("flights.json", "w"), indent=4)
#
# price = NumField("Price",
#                  ["price"],
#                  [NumCategory("cheap", 0, 150),
#                   NumCategory("moderate", 150, 800),
#                   NumCategory("expensive", 800, sys.maxsize)],
#                  # parse price from string, e.g. "USD83.10"
#                  lambda raw: float(re.match(".*?([0-9\.]+)", raw).group(1)))
#
# # for flight in flights:
# #     print(price.filter(flight))
#
# price.print_stats(flights)
#
#
# legs = Field("Legs", ["legs"])
# legs.print_stats(flights)
# duration = Field("Duration", ["totalDuration"])
# duration.print_stats(flights)
# #print(duration.entropy(flights))
#
# destination = Field("Destination", ["destination"])
# destination.print_stats(flights)
# carrier = Field("Carrier", ["carriers"])
# carrier.print_stats(flights)
# cabin = Field("Cabin Class", ["cabins"])
# cabin.print_stats(flights)
# arrivalDate = Field("Arrival Date", ["arrivalDate"])
# arrivalDate.print_stats(flights)
# passengers = Field("Passengers", ["passengers"])
# passengers.print_stats(flights)

from system import Pipeline
from nlg.nlg import Speaker
#from nlu.nlu import extract_info

pipeline = Pipeline()

print(list(pipeline.manager.inform("Destination", [("AMS", 1)])))
print(list(pipeline.manager.inform("Origin", [("LAX", 1)])))
print(list(pipeline.manager.inform("Departure Date", [("2016-12-09", 1)])))
print(len(pipeline.manager.possible_data))
print(list(pipeline.manager.inform("Price", [("moderate", 1)])))
print(len(pipeline.manager.possible_data))

q, expected = pipeline.manager.next_question()
print((q, expected))

# extracted = extract_info("I want to fly from Los Angeles to London on next Tuesday")
# print(extracted)
# print(extract_info("I would prefer to fly premium coach class"))
# print(extract_info("I want to fly with American Airlines"))
# print(extract_info("AMS"))
# print(extract_info("LAX"))
# print(extract_info("yes"))
# print(extract_info("no"))
# print(extract_info("next wednesday"))