from typing import Union

from qpx import qpx
from dialogue.database import Database


class QPXDatabase(Database):
    # converts query from dialogue management to valid QPX query
    def build_request(self, query: {str: Union[str, int, float]}) -> object:
        request = {
            "request": {
                "passengers": {
                    "adultCount": 1
                },
                "slice": [
                    {
                        "date": query["Departure Date"],
                        "origin": query["Origin"],
                        "destination": query["Destination"]
                    }
                ]
            }
        }
        return request

    def query(self, query: {str: Union[str, int, float]}):
        return qpx.extract_flights(qpx.get_flights(self.build_request(query)))
