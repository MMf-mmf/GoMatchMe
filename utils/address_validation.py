from django.conf import settings

import googlemaps
gmaps = googlemaps.Client(key=settings.GOOGLE_MAPS_API_KEY)

# this function takes in a address and city and passes it to googles address validation api and returns a long dict response
# which we unpack to return a suggested correct format for the address
def validate_address(address, city):
    addressvalidation_result =  gmaps.addressvalidation([address], 
                                                        locality=city, 
                                                        # regionCode='US', # omit since there are country that are not sported
                                                        # enableUspsCass=True
                                                        )

    if 'error' in addressvalidation_result:
        # if the response contains a message: "Unsupported region code:" ignore the entire response
        if 'Unsupported region code:' in addressvalidation_result['error']['message']:
            results = {'error': addressvalidation_result['error']['message'], 'result': None}
            return results
        else:
            results = {'error': addressvalidation_result['error']['message'], 'result': None}
            return results
    else:
        try:
            address_data = addressvalidation_result["result"]["address"]['postalAddress']
            validation_granularity = addressvalidation_result["result"]["verdict"]["validationGranularity"]
            hasInferredComponents = addressvalidation_result["result"]["verdict"]["hasInferredComponents"]
            if addressvalidation_result["result"]["verdict"]["validationGranularity"]:
                address = address_data["addressLines"][0]
                city = address_data["locality"]
                zip = address_data["postalCode"]
                country = address_data["regionCode"]
                state = address_data["administrativeArea"]

                results = {'error': None, 'result': {'address': address, 'city': city, 'zip': zip, 'country': country, 'state': state}}
                return results
            else:
                results = {'error': 'Address not found', 'result': None}
                return results
        except KeyError:
            results = {'error': 'Address not found', 'result': None}
            return results