from peewee import *
import getpass

user = input("Username [%s]: " % getpass.getuser())
if not user:
    user = getpass.getuser()

password = getpass.getpass()

database = MySQLDatabase('fis', **{'host': 'localhost', 'user': user, 'password': password, 'port': 3306})
try:
    print("Available tables:", database.get_tables())
except Exception as e:
    print("ERROR while accessing database:")
    print(e)

class UnknownField(object):
    def __init__(self, *_, **__): pass

class BaseModel(Model):
    class Meta:
        database = database

class Airlines(BaseModel):
    active = CharField(db_column='Active', null=True)
    alias = CharField(db_column='Alias', null=True)
    callsign = CharField(db_column='Callsign', null=True)
    country = CharField(db_column='Country', null=True)
    iata = CharField(db_column='IATA', null=True)
    icao = CharField(db_column='ICAO', null=True)
    id = PrimaryKeyField(db_column='Id')
    name = CharField(db_column='Name')

    class Meta:
        db_table = 'Airlines'
        schema = 'fis'

class Airports(BaseModel):
    altitude = IntegerField(db_column='Altitude')
    city = CharField(db_column='City')
    country = CharField(db_column='Country')
    dst = CharField(db_column='DST')
    iata_faa = CharField(db_column='IATA_FAA', primary_key=True)
    icao = CharField(db_column='ICAO', null=True)
    id = IntegerField(db_column='Id')
    latitude = DecimalField(db_column='Latitude')
    longitude = DecimalField(db_column='Longitude')
    name = CharField(db_column='Name')
    tz = CharField(db_column='TZ', null=True)
    timezone = IntegerField(db_column='Timezone')

    class Meta:
        db_table = 'Airports'
        schema = 'fis'

