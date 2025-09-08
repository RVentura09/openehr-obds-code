'''
This file is inteded to host the mapping it self. The method map_ressource(..) ist called
in the kafka_consumer.py file within the start_consumer() method.
'''

import json
from fhir.resources.patient import Patient

def map_ressource(input_json):
    """
        Args:
            input_json (json): A json object
        Returns:
            str:    A str that must be valid json. Since we are mapping with fhir.resources 
                    this should be ensured id <ressource>.json() ist used for returning.
    """

    # The following code was just an example for testing stuff
    input_patient = input_json['Patient']

    patient = Patient.construct()
    
    patient.id = input_patient['PatId']


    given = input_patient['Vorname']
    family = input_patient['Nachname']

    patient.name = [{
        "given": [str(given)],
        "family": family
    }]


    line = input_patient['Adresse']['Straße']
    postal_code = input_patient['Adresse']['PLZ']
    city = input_patient['Adresse']['Stadt']

    patient.address = [{
        "line": [line],
        "postalCode": postal_code,
        "city": city
    }]

    return [patient]
