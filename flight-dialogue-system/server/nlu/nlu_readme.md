# Resources

* Python 3.5
* Java
* spaCy Python library (https://pypi.python.org/pypi/spacy/1.2.0)
* Python SUTime (https://github.com/FraBle/python-sutime)
* NLTK

# Usage

* extract_info(utterance:str) function in nlu.py returns a dict with whatever of the following information it can determine
* run nlu.py directly to repeatedly give input and see output

# Data

### Named entities tagged as locations or with a name that sounds like an airport
* **o_location (str)** origin location
* **d_location (str)** destination location
* **u_location (list of str)** unknown/unclassified locations

### Tokens tagged by NER not listed above or in airlines
* **o_entity (str)** entity associated with a word indicating origin
* **d_entity (str)** entity associated with a word indicating destination
* **u_entity (list of str)** other entities

### Dates and times
* **out_date (datetime.date)** date of outbound flight
* **out_time_earliest (datetime.time)** earliest allowed time of outbound flight
* **out_time_latest (datetime.time)** latest allowed time of outbound flight
* **in_date (datetime.date)** date of inbound flight
* **in_time_earliest (datetime.time)** earliest allowed time of inbound flight
* **in_time_earliest (datetime.time)** latest allowed time of inbound flight
* **u_date (datetime.date)** date
* **u_time_earliest (datetime.time)** earliest allowed time
* **u_time_earliest (datetime.time)** latest allowed time

morning = 00:00 - 12:00
afternoon = 12:00 - 18:00
evening/night = 18:00 - 23:59
specific time = +/= 1 hour of the given time

Does not handle date ranges.

### Other
* **dialog_act (str)** statement, question, yes, no, other
* **airlines (list of str)**
* **cabin_class (str)**
* **qualifiers (set of str)** direct, earlier, earliest, later, latest, cheapest
* **numbers (list of int)**
* **flight codes (list of str)**

# Classifer Notes

## Weka Settings

* FilteredClassifier
    * classifier: J48
    * filter: StringToWordVector
        * IDFTransform: True
        * TFTransform: True
        * lowerCaseTokens: True
        * outputWordCounts: True
        * stemmer: IteratedLovinsStemmer
        * stopwordsHandler: WordsFromFile (file includes um, uh)
        * tokenizer: NGramTokenizer
        * wordsToKeep: 50

Values not listed were defaults.