import sys, csv, json

regions = {}
for region in csv.DictReader(open("regions.csv")):
    regions[region["code"]] = region

countries = {}
for country in csv.DictReader(open("countries.csv")):
    countries[country["code"]] = country

airports = []
airport_types = ["small_airport", "medium_airport", "large_airport"]
for airport in csv.DictReader(open("airports.csv")):
    if airport["type"] not in airport_types:
        continue
    airports.append({
        "Name": airport["name"],
        "Region": regions[airport["iso_region"]]["name"],
        "Country": countries[airport["iso_country"]]["name"],
        "City": airport["municipality"],
        "Code": airport["iata_code"] or airport["local_code"],
        "GPS_Code": airport["gps_code"],
        "Size": airport_types.index(airport["type"])+1
    })

json.dump(airports, open("airports2.json", "w"), indent=4)
