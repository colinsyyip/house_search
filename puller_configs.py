ROOM_DOMAIN = "https://www.room.nl"
ROOM_RESULT_METADATA_DOMAIN = "https://roomapi.hexia.io/api/v1/actueel-aanbod?"
ROOM_SEARCH_PARAMS = "limit=%s&locale=en_GB&page=0&sort=-publicationDate"
ROOM_L1_TARGET_RENTAL_KEYS = [
    'ID', 'postalcode', 'street', 'houseNumber', 'houseNumberAddition',
    'gemeenteGeoLocatieNaam', 'rentBuy', 'availableFromDate', 'areaDwelling',
    'totalRent', 'netRent', 'calculationRent', 'serviceCosts', 'heatingCosts',
    'additionalCosts', 'numberOfReactions', 'publicationDate', 'closingDate', 
    'isWoningruil', 'urlKey', 'infoveld', 'specifiekeVoorzieningen'
]
ROOM_Ln_TARGET_RENTAL_KEYS = [
    ['quarter', 'name'], ['corporation', 'name'], ['dwellingType', 'localizedName'],
    ['sleepingRoom', 'amountOfRooms'], ['sleepingRoom', 'naam'], ['kitchen', 'localizedName'],
    ['floor', 'verdieping'], ['woningsoort', 'localizedNaam']
]
ROOM_DB_KEY_MAP_PATH = "db_mappings/room_mapping.json"

KAMERNET_DOMAIN = "https://kamernet.nl"
KAMERNET_SEARCH_DOMAIN = "https://kamernet.nl/services/api/listing/findlistings"
KAMERNET_SEARCH_PL = {"location":{"name":"Leiden","cityName":"Leiden"},
                      "radiusId":4,
                      "listingTypeIds":[],
                      "maxRentalPriceId":33,
                      "surfaceMinimumId":2,
                      "listingSortOptionId":1,
                      "pageNo": "%.0f",
                      "suitableForGenderIds":[],
                      "furnishings":[],
                      "availabilityPeriods":[],
                      "availableFromDate":None,
                      "isBathroomPrivate":None,
                      "isToiletPrivate":None,
                      "isKitchenPrivate":None,
                      "hasInternet":None,
                      "suitableForNumberOfPersonsId":None,
                      "candidateAge":None,
                      "suitableForStatusIds":[],
                      "isSmokingInsideAllowed":None,
                      "isPetsInsideAllowed":None,
                      "roommateMaxNumberId":None,
                      "roommateGenderIds":[],
                      "ownerTypeIds":[],
                      "variant":None,
                      "searchview":1,
                      "rowsPerPage":18,
                      "OpResponse":{"Code":1000,"Message":"Operation successful.","HttpStatusCode":200},
                      "LogEntryId":None
                      }
KAMERNET_L1_KEYS = ['listingId', 'furnishingId', 'availabilityStartDate', 'availabilityEndDate',
                    'street', 'city', 'surfaceArea', 'listingType', 'totalRentalPrice',
                    'utilitiesIncluded', 'isNewAdvert']
KAMERNET_FURNISHING_MAP = {1: 'uncarpeted',
                           2: 'unfurnished',
                           3: '',
                           4: 'furnished'}

KAMERNET_LISTING_TYPE_MAP = {1: 'room',
                             2: 'apartment',
                             3: '',
                             4: 'studio'}
KAMERNET_DB_KEY_MAP_PATH = "db_mappings/kamernet_mapping.json"

PARARIUS_DOMAIN = "https://www.pararius.com"
PARARIUS_SEARCH_URL = "https://www.pararius.com/apartments/leiden/page-%.0f"

FUNDA_DOMAIN = "https://www.funda.nl"
FUNDA_SEARCH_URL = "https://www.funda.nl/en/zoeken/huur?selected_area=%%5B%%22leiden%%22%%5D&search_result=%.0f"