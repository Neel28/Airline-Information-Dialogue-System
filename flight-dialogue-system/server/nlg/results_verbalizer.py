# results_verbalizer.py

import random
import re
import pickle
import csv
import datetime
import json

############################
# TEMPLATES/STORED PHRASES #
############################

# NO = none
# SG = singular
# PL = plural


NO_FLIGHTS = [
    "There doesn't seem to be any flights that match the criteria.",
    "Unfortunatley, I don't see any matching flights.",
    "I can't seem to find a flight that has what you're looking for.",
]

# SUM_NUM_OF_ITINERARIES
# <A> number of itineraries
SUM_NUM_ITINERARIES_SG = [
    "There is only one itinerary matching your criteria.",
    "I've found one possible trip that meets your specifications.",
]
SUM_NUM_ITINERARIES_PL = [
    "There are <A> itineraries matching your criteria.",
    "I've found <A> possible trips that meet your specifications.",
]

# <A> number of non-stop itineraries
SUM_NUM_NONSTOP_ITINERARIES_SG = [
    "Of all the matching trips, only one is direct both ways."
]
SUM_NUM_NONSTOP_ITINERARIES_PL = [
    "Of all the matching trips, <A> are non-stop.",
    "<A> of the flights I've found are direct.",
]

# <A> cheapest, <B> costliest, <C> average
SUM_PRICE = [
    "The flights range in price from <A> to <B>, with <C> being the average.",
    "The cheapest airfare I could find is <A>, though it can get as expensive as <B>. The average trip costs <C>.",
]

# <A> list of carriers
SUM_CARRIERS = [
    "As far as airlines go, here are your options: <A>.",
    "The possible carriers include <A>.",
]

# <A> earliest, <B> latest
SUM_TIMES = {
    'outbound_departure_time': 'The earliest one is at <A>, while the latest is at <B>.',
    'outbound_arrival_time': 'The one that will get you there the soonest arrives at <A>, with the latest arriving at <B>.',
    'inbound_departure_time': 'The earliest will depart at <A> and the latest will depart at <B>.',
    'inbound_arrival_time': 'You could return as early as <A> or as late as <B>.',
    'outbound_introduction': 'For your flight out,',
    'inbound_introduction': 'For your flight coming back,',
}

# <A> airline, <B> outbound departure, <C> outbound arrival, <D> inbound departure, <E> inbound arrival, <F> cost
FIRST_ITINERARY_INTRODUCTION = [
    "There's a flight",
    "I've found a flight",
]
ADDITIONAL_ITINERARY_INTRODUCTION = [
    "Another option would be one",
    "You could also fly",
    "I've found yet another flight, this time",
]
ITINERARY_RT = [
    "on <A> at <B> which gets in at <C>. The return flight is at <D> and departs at <E>. The airfare for this itinerary is <F>.",
    "with <A>, departing at <B> and arriving at your destination at <C>. You'd leave from there at <D> and get in at <E>. This would set you back <F>.",
    "on <A>. It leaves at <B> and gets in at <C>, with the return flight leaving at <D> and arriving back at <E>. The cost for this would be <F>.",
]
ITINERARY = [
    "on <A> at <B> which gets in at <C> costing <F>.",
    "with <A>, departing at <B> and arriving at your destination at <C>. This would set you back <F>.",
    "on <A>. It leaves at <B> and gets in at <C>. The airfare for this one is <F>.",
    "taking <A> at <B>, arriving at <C>, for <F>.",
]


########################
# GENERATION FUNCTIONS #
########################


def sum_num_itineraries(results):
    template = random.choice(SUM_NUM_ITINERARIES_PL)
    num_itineraries = str(len(results))
    return re.sub('<A>', num_itineraries, template)


def sum_num_nonstop_itineraries(results):
    nonstop = 0
    for flight in results:
        if flight['legs'] < 3:  # assumes two-city itineraries
            nonstop += 1
    if nonstop == 1:
        template = random.choice(SUM_NUM_NONSTOP_ITINERARIES_SG)
        return template
    elif nonstop > 1:
        template = random.choice(SUM_NUM_NONSTOP_ITINERARIES_PL)
        return re.sub('<A>', str(nonstop), template)
    else:
        return None


def sum_price(results):
    total = 0.0
    cheapest = None
    costliest = None
    for flight in results:
        price = float(re.findall('([\d.]+)', flight['price'])[0])
        if cheapest is None or price < cheapest:
            cheapest = price
        if costliest is None or price > costliest:
            costliest = price
        total += price
    average = total / len(results)
    cheapest = '${:0.2f}'.format(cheapest)
    costliest = '${:0.2f}'.format(costliest)
    average = '${:0.2f}'.format(average)
    text = random.choice(SUM_PRICE)
    text = re.sub('<A>', cheapest, text)
    text = re.sub('<B>', costliest, text)
    text = re.sub('<C>', average, text)
    return text


def lookup_airline_name(carrier_designator):
    with open('../data/airline_names.csv', 'r') as f:
        csv_f = csv.reader(f)
        for row in csv_f:
            if carrier_designator == row[3]:
                return row[1]
    return 'Unknown'


def format_carriers(carriers):
    carriers = sorted([lookup_airline_name(c) for c in carriers])
    if len(carriers) > 2:
        carriers_text = '{}, and {}'.format(', '.join(carriers[:-1]), carriers[-1])
    elif len(carriers) == 2:
        carriers_text = ' and '.join(carriers)
    elif len(carriers) == 1:
        carriers_text = carriers[0]
    return carriers_text


def sum_carriers(results):
    carrier_designators = set()
    for flight in results:
        carrier_designators |= set(flight['carriers'])
    if len(carrier_designators) < 1:
        carriers_text = 'There seems to be no information about the airlines.'
    else:
        carriers_text = format_carriers(carrier_designators)
    template = random.choice(SUM_CARRIERS)
    return re.sub('<A>', carriers_text, template)


DATETIME_PATTERN = '^(\d{4}\-\d{2}-\d{2}T\d{2}:\d{2})'
DATETIME_STRPTIME_PATTERN = '%Y-%m-%dT%H:%M'


def get_datetime(flight, segment):
    if segment == 'outbound_departure_time':
        time_string = flight['slices'][0]['segments'][0]['legs'][0]['departureTime']
    elif segment == 'outbound_arrival_time':
        time_string = flight['slices'][0]['segments'][-1]['legs'][-1]['arrivalTime']
    elif segment == 'inbound_departure_time':
        time_string = flight['slices'][-1]['segments'][0]['legs'][0]['departureTime']
    elif segment == 'inbound_arrival_time':
        time_string = flight['slices'][-1]['segments'][-1]['legs'][-1]['arrivalTime']
    dt = re.search(DATETIME_PATTERN, time_string).group(0)
    dt = datetime.datetime.strptime(dt, DATETIME_STRPTIME_PATTERN)
    return dt


def sum_times(results, segment):
    '''
	@param segment: '<outbound/inbound>_<departure/arrival>'
	'''

    earliest = None
    latest = None

    for flight in results:
        dt = get_datetime(flight, segment)
        if earliest is None or dt < earliest:
            earliest = dt
        if latest is None or dt > latest:
            latest = dt

    earliest = earliest.strftime('%H:%M')
    latest = latest.strftime('%H:%M')

    template = SUM_TIMES[segment]
    text = re.sub('<A>', earliest, template)
    text = re.sub('<B>', latest, text)
    return text


def aggregate_times(options, text):
    if 'outbound_departure_time' in options:
        index = options.index('outbound_departure_time')
        old_text = text[index].lower()
        text[index] = '{} {}'.format(SUM_TIMES['outbound_introduction'], old_text)
    if 'outbound_arrival_time' in options and 'outbound_departure_time' not in options:
        index = options.index('outbound_departure_time')
        old_text = text[index].lower()
        text[index] = '{} {}'.format(SUM_TIMES['outbound_introduction'], old_text)
    if 'inbound_departure_time' in options:
        index = options.index('inbound_departure_time')
        old_text = text[index].lower()
        text[index] = '{} {}'.format(SUM_TIMES['inbound_introduction'], old_text)
    if 'inbound_arrival_time' in options and 'inbound_departure_time' not in options:
        index = options.index('inbound_departure_time')
        old_text = text[index].lower()
        text[index] = '{} {}'.format(SUM_TIMES['inbound_introduction'], old_text)


def summarize(results, options):
    headers = []
    text = []
    if 'count' in options:
        headers.append('count')
        text.append(sum_num_itineraries(results))
    if 'nonstop' in options:
        headers.append('nonstop')
        text.append(sum_num_nonstop_itineraries(results))
    if 'price' in options:
        headers.append('price')
        text.append(sum_price(results))
    if 'carriers' in options:
        headers.append('carriers')
        text.append(sum_carriers(results))
    if 'outbound_departure_time' in options:
        headers.append('outbound_departure_time')
        text.append(sum_times(results, 'outbound_departure_time'))
    if 'outbound_arrival_time' in options:
        headers.append('outbound_arrival_time')
        text.append(sum_times(results, 'outbound_arrival_time'))
    if 'inbound_departure_time' in options:
        headers.append('inbound_departure_time')
        text.append(sum_times(results, 'inbound_departure_time'))
    if 'inbound_arrival_time' in options:
        headers.append('inbound_arrival_time')
        text.append(sum_times(results, 'inbound_arrival_time'))
    aggregate_times(headers, text)
    text = [section for section in text if section is not None]
    return text


def tell_all(results):
    # <A> airline, <B> outbound departure, <C> outbound arrival, <D> inbound departure, <E> inbound arrival, <F> cost
    full_text = []
    first = True
    for flight in results:
        airline = format_carriers(flight['carriers'])
        outbound_departure = get_datetime(flight, 'outbound_departure_time')
        outbound_departure = outbound_departure.strftime('%H:%M on %A, %B %d')
        outbound_arrival = get_datetime(flight, 'outbound_arrival_time')
        outbound_arrival = outbound_arrival.strftime('%H:%M on %A, %B %d')
#         inbound_departure = get_datetime(flight, 'inbound_departure_time')
#         inbound_departure = inbound_departure.strftime('%H:%M on %A, %B %d')
#         inbound_arrival = get_datetime(flight, 'inbound_arrival_time')
#         inbound_arrival = inbound_arrival.strftime('%H:%M on %A, %B %d')
        price = '${:0.2f}'.format(float(re.findall('([\d.]+)', flight['price'])[0]))
        if first:
            first = False
            text = '{} {}'.format(
                random.choice(FIRST_ITINERARY_INTRODUCTION),
                random.choice(ITINERARY))
        else:
            text = '{} {}'.format(
                random.choice(ADDITIONAL_ITINERARY_INTRODUCTION),
                random.choice(ITINERARY))

        text = re.sub('<A>', airline, text)
        text = re.sub('<B>', outbound_departure, text)
        text = re.sub('<C>', outbound_arrival, text)
#         text = re.sub('<D>', inbound_departure, text)
#         text = re.sub('<E>', inbound_arrival, text)
        text = re.sub('<F>', price, text)
        full_text.append(text)
    return full_text


######################
# "PUBLIC" FUNCTIONS #
######################

def verbalize(results, summarize_when, options=['count', 'price', 'carriers', 'outbound_departure_time',
               'outbound_arrival_time']):
    '''
	@param: results -- from qpx.extract_flights
	@param: summarize_when -- number of results at which to start summarizing,
		otherwise give full details
	@param: options -- if summarized, what details should be given
		list/set of str, which can be [
			'count',
			'nonstop',
			'price',
			'carriers',
			'outbound_departure_time',
			'oubound_arrival_time',
			'inbound_departure_time',
			'inbound_arrival_time'
			]
	@return: list of str (so it can be sent in multiple messages if wanted)
	'''
    if len(results) < 1:
        return [random.choice(NO_FLIGHTS)]
    elif len(results) >= summarize_when:
        return summarize(results, options)
    else:
        return tell_all(results)


#########
# DEBUG #
#########

def main():
#     with open('nlg/sample_extracted_flight.pickle', 'rb') as f:
#         flight = pickle.load(f)
    options = ['count', 'price', 'carriers', 'outbound_departure_time',
               'outbound_arrival_time']
#     output = verbalize(flight, 4, options)
#     #  print(flight)
#     for line in output:
#         print(line)
    with open('nlg/system_output.json') as json_data:
        d = json.load(json_data)
        print(json.dumps(d, sort_keys=True, indent=4))
    output = verbalize(d['data'], 4, options)
    for line in output:
        print(line)


if __name__ == '__main__':
    main()
