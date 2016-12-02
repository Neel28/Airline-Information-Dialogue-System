# nlu.py

import csv
import datetime
import os
import glob
import re
import json
import spacy
import sutime as sutime
from nlu import act_classifier


##################
# INITIALIZATION #
##################

# spacy parser

nlp = spacy.load('en')

# sutime tagger
jars = os.path.join(os.path.dirname('__file__'), 'nlu/python_sutime/jars')
time_tagger = sutime.SUTime(jars, mark_time_ranges=True)

# airline list
# airline_names_path = glob.glob('**/airline_names.csv', recursive=True)[0]
with open('nlu/airline_names.csv', 'r') as csvfile:
    airline_reader = csv.reader(csvfile, delimiter=',', quotechar='"')
    AIRLINES = {row[1].upper(): row[3].upper() or row[4].upper() for row in airline_reader}

###################
# IMPORTANT WORDS #
###################


PUNCTUATION = ',.?!'

TIME_OF_DAY_INDICATORS = {'MO', 'AF', 'EV', 'NI'}

RELATED_WORDS = {
    'destination': {'arrive', 'to', 'for', 'at', 'go', 'fly', 'travel'},
    'origin': {'depart', 'leave', 'from', 'come', 'back', 'return'},
    'invert_to_from': {'return', 'come'},
    'inbound': {'return', 'come', 'back', 'from'},
    'outbound': {'leave', 'depart', 'to', 'go', 'fly', 'travel'},
}

CABIN_CLASS_WORDS = {
    'coach': 'COACH',
    'economy': 'COACH',
    'deluxe': 'PREMIUM_COACH',
    'premium': 'PREMIUM_COACH',
    'business': 'BUSINESS',
    'first': 'FIRST'
}


def indicates(token, topic):
    return True if token.lemma_ in RELATED_WORDS[topic] else False


##################
# NAMED ENTITIES #
##################


def is_iata(word):
    return True if re.search(r'^[A-Z]{3}\W?$', word) else False


def is_numeral(word):
    return True if re.search(r'^\d+\W?$', word) else False


def seems_like_airport(name):
    if re.search('(AIRPORT|AIRFIELD|INTERNATIONAL|MUNICIPAL|REGIONAL)',
                 name.upper()):
        return True
    else:
        return False


def determine_entity_o_d(token):
    o_d = None
    for ancestor in token.ancestors:
        if ancestor.tag_[0] == 'V':
            if o_d is not None and ancestor.lemma_ in RELATED_WORDS['invert_to_from']:
                o_d = 'origin' if o_d == 'destination' else 'destination'
            elif ancestor.lemma_ == 'depart' or ancestor.lemma_ == 'leave':
                o_d = 'origin'
            elif ancestor.lemma_ == 'arrive':
                o_d = 'destination'
            return o_d
        else:
            if ancestor.lemma_ == 'to':
                o_d = 'destination'
            elif ancestor.lemma_ == 'from':
                o_d = 'origin'
    return o_d


def detect_entities(doc):
    '''
	Populates and returns a dict with:
	'x_location' for named entities tagged as locations or that sound like an airport name
	'x_entity' for other named entities
	'airlines'
	'''
    keywords = {}
    for ent in doc.ents:
        o_d = determine_entity_o_d(ent.root)
        if ent.label_ == 'GPE' or seems_like_airport(ent.orth_):
            if o_d == 'origin':
                keywords.update({'o_location': ent.orth_})
            elif o_d == 'destination':
                keywords.update({'d_location': ent.orth_})
            else:
                if 'u_location' not in keywords:
                    keywords['u_location'] = []
                keywords['u_location'].append(ent.orth_)
        elif ent.orth_.upper() in AIRLINES:
            if 'airlines' not in keywords:
                keywords['airlines'] = []
            keywords['airlines'].append(AIRLINES[ent.orth_.upper()])
        elif ent.label_ != 'DATE' and not is_iata(ent.orth_) and not is_numeral(ent.orth_):
            if o_d == 'origin':
                keywords.update({'o_entity': ent.orth_.strip(PUNCTUATION)})
            elif o_d == 'origin':
                keywords.update({'d_entity': ent.orth_.strip(PUNCTUATION)})
            else:
                if 'u_entity' not in keywords:
                    keywords['u_entity'] = []
                keywords['u_entity'].append(ent.orth_.strip(PUNCTUATION))
    return keywords


def detect_iata(doc):
    '''
	Populates and returns a dict with:
	'x_location' for IATA code
	'''
    keywords = {}
    for token in doc:
        if is_iata(token.orth_):
            if indicates(token.head, 'origin'):
                keywords.update({'o_location': token.orth_.strip(PUNCTUATION)})
            elif indicates(token.head, 'destination'):
                keywords.update({'d_location': token.orth_.strip(PUNCTUATION)})
            else:
                if 'u_location' not in keywords:
                    keywords['u_location'] = []
                keywords['u_location'].append(token.orth_.strip(PUNCTUATION))
    return keywords


###################
# DATES AND TIMES #
###################


def find_in_doc(doc, word):
    word = nlp(word)[0].orth_.strip(PUNCTUATION)
    for token in doc:
        if word == token.orth_.strip(PUNCTUATION):
            return token
    return None


def determine_outbound_inbound(doc, text):
    word = text.split()[0]
    token = find_in_doc(doc, word)
    for ancestor in token.ancestors:  # search for ancestor verbs
        if indicates(ancestor, 'inbound'):
            return 'inbound'
        elif indicates(ancestor, 'outbound'):
            return 'outbound'
    found_word = False
    for i in range(1, len(doc)):  # search for nearby prepositions
        if token == doc[-i]:
            found_word = True
        if found_word and indicates(doc[-i], 'inbound'):
            return 'inbound'
        elif found_word and indicates(doc[-i], 'outbound'):
            return 'outbound'
    else:
        return None


def parse_date(date):
    if len(date) < 1:
        return None
    try:
        dt = datetime.datetime.strptime(date, '%Y-%m-%d')
        date = datetime.date(dt.year, dt.month, dt.day)
        now = datetime.datetime.now()
        today = datetime.date(now.year, now.month, now.day)
        # correct for assumed earlier tag for day of week
        if date < today:
            date += datetime.timedelta(days=7)
        return str(date)
    except ValueError:
        return None


def parse_time(time):
    if len(time) < 1:
        return None
    if time in TIME_OF_DAY_INDICATORS:
        if time == 'MO':
            earliest = datetime.time(hour=0, minute=0)
            latest = datetime.time(hour=12, minute=0)
        elif time == 'AF':
            earliest = datetime.time(hour=12, minute=0)
            latest = datetime.time(hour=18, minute=0)
        else:
            earliest = datetime.time(hour=18, minute=0)
            latest = datetime.time(hour=23, minute=59)
    else:
        try:
            dt = datetime.datetime.strptime(time, '%H:%M')
            earliest = dt - datetime.timedelta(hours=1)
            latest = dt + datetime.timedelta(hours=1)
            return (earliest, latest)
        except ValueError:
            return (None, None)
    return (earliest, latest)


def parse_datetime_tag(tag, doc):
    # automatically assigns a date if time is also provided, so the date should be
    # ignored if only a time was expected
    keywords = {}
    outbound_inbound = determine_outbound_inbound(doc, tag['text'])
    date_time = tag['value'].split('T')
    date = parse_date(date_time[0])
    earliest, latest = None, None
    if len(date_time) > 1:
        earliest, latest = parse_time(date_time[1])
    if outbound_inbound == 'outbound':
        if earliest is not None and latest is not None:
            return {'out_date': date,
                    'out_time_earliest': earliest, 'out_time_latest': latest}
        else:
            return {'out_date': date}
    elif outbound_inbound == 'inbound':
        if earliest is not None and latest is not None:
            return {'in_date': date,
                    'in_time_earliest': earliest, 'in_time_latest': latest}
        else:
            return {'in_date': date}
    else:
        if earliest is not None and latest is not None:
            return {'u_date': date,
                    'u_time_earliest': earliest, 'u_time_latest': latest}
        else:
            return {'u_date': date}


def detect_datetimes(doc):
    keywords = {}
    indices = []
    tags = time_tagger.parse(doc.text)
    for tag in tags:
        indices.append((tag['start'], tag['end']))
        keywords.update(parse_datetime_tag(tag, doc))
    return indices, keywords


###########
# NUMBERS #
###########


def detect_numbers(utterance, exclude):
    candidate_numbers = {int(num) for num in re.findall('([\d,]+)', utterance)}
    non_excluded_numbers = set(candidate_numbers)
    for number in candidate_numbers:
        for start, end in exclude:
            if number >= start and number < end:
                non_excluded_numbers.remove(number)
    if non_excluded_numbers:
        return {'numbers': list(non_excluded_numbers)}
    else:
        return {}


#########
# CABIN #
#########


def detect_cabin_class(doc):
    '''Populates and returns a dict with:
	'cabin_class'
	'''
    keywords = {}
    text = doc.text.lower()
    if 'premium' in text or 'deluxe' in text:
        keywords.update({'cabin_class': 'PREMIUM_COACH'})
        return keywords
    for cabin_class in CABIN_CLASS_WORDS:
        if cabin_class in doc.text.lower():
            keywords.update({'cabin_class': CABIN_CLASS_WORDS[cabin_class]})
        if 'cabin_class' in keywords and \
                        keywords['cabin_class'] == 'FIRST' and \
                        'the first' in doc.text.lower():
            del keywords['cabin_class']
    return keywords


##############
# QUALIFIERS #
##############


COMPARATIVE_AND_SUPERLATIVE_POS = {'JJR', 'JJS', 'RBR', 'RBS'}
OTHER_FEATURES = {'direct', 'non-stop', 'nonstop', 'the first', 'least expensive', 'least costly', 'cheap', 'moderate', 'expensive'}
STANDARDIZED_FEATURES = {
    'direct': {'direct', 'non-stop', 'nonstop'},
    'earlier': {'earlier', 'before'},
    'later': {'later', 'after'},
    'earliest': {'the first', 'earliest'},
    'latest': {'last', 'latest'},
    'cheapest': {'cheapest', 'inexpensive', 'least expensive', 'least costly'},
    'cheap': {'cheap'},
    'moderate': {'moderate'},
    'expensive': {'expensive'},
}


def detect_comparatives_and_superlatives(doc):
    return {token.orth_.lower() for token in doc
            if token.tag_ in COMPARATIVE_AND_SUPERLATIVE_POS}


def detect_flight_features(doc):
    features = set()
    for feature in OTHER_FEATURES:
        if feature in doc.text:
            features.add(feature)
    return features


def standardize_qualifiers(qualifiers):
    standardized_qualifiers = set()
    for feature in STANDARDIZED_FEATURES:
        for synonym in STANDARDIZED_FEATURES[feature]:
            if synonym in qualifiers:
                standardized_qualifiers.add(feature)
    return standardized_qualifiers


def detect_qualifiers(doc):
    qualifiers = detect_comparatives_and_superlatives(doc)
    qualifiers |= detect_flight_features(doc)
    qualifiers = standardize_qualifiers(qualifiers)
    if qualifiers:
        return {'qualifiers': list(qualifiers)}
    else:
        return {}


def assume_origin_destination(data):
    if 'u_location' in data:
        if data and 'o_location' in data and 'd_location' not in data:
            data['d_location'] = data['u_location'][0]
            data['u_location'].remove(data['d_location'])
        elif 'o_location' not in data and 'd_location' in data:
            data['o_location'] = data['u_location'][0]
            data['u_location'].remove(data['o_location'])


def assume_inbound_outbound(data):
    if 'u_date' in data:
        if 'out_date' in data and 'in_date' not in data:
            data['in_date'] = data['u_date']
            del data['u_date']
        elif 'out_date' not in data and 'in_date' in data:
            data['out_date'] = data['u_date']
            del data['u_date']
    if 'u_time_earliest' in data:
        if 'out_time_earliest' in data and 'in_time_earliest' not in data:
            data['in_time_earliest'] = data['u_time_earliest']
            data['in_time_latest'] = data['u_time_latest']
            del data['u_time_earliest']
            del data['u_time_latest']
        elif 'out_time_earliest' not in data and 'in_time_earliest' in data:
            data['out_time_earliest'] = data['u_time_earliest']
            data['out_time_latest'] = data['u_time_latest']
            del data['u_time_earliest']
            del data['u_time_latest']


######################
# "PUBLIC" FUNCTIONS #
######################


# TODO: make origin vs. destination distinguisher more robust? (e.g. "returning to X" assumes X is destination)


def extract_info(utterance):
    doc = nlp(utterance)
    data = {'dialog_act': act_classifier.classify(doc)}
    data.update(detect_entities(doc))
    data.update(detect_iata(doc))
    data.update(detect_cabin_class(doc))
    data.update(detect_qualifiers(doc))
    indices, datetimes = detect_datetimes(doc)
    data.update(datetimes)
    assume_origin_destination(data)
    assume_inbound_outbound(data)
    data.update(detect_numbers(utterance, indices))
    return data


##############
# MAIN DEBUG #
##############


def main():
    while True:
        utterance = input('Enter a sentence: ')
        info = extract_info(utterance)
        for key in sorted(info.keys()):
            print('{:>20} = {:}'.format(key, info[key]))


if __name__ == '__main__':
    main()
