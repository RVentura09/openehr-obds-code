'''
This file is inteded to host the mapping it self. The method map_ressource(..) ist called
in the kafka_consumer.py file within the start_consumer() method.
'''

import json
from hashlib import sha224

from fhir.resources.R4B.specimen import Specimen
from datetime import datetime
import pytz

def map_ressource(input_json):
    """
        Args:
            input_json (json): A json object
        Returns:
            str:    A str that must be valid json. Since we are mapping with fhir.resources 
                    this should be ensured id <ressource>.json() ist used for returning.
    """

    specimenId = f'SPE-{sha224(input_json["specimenId"].encode("utf-8")).hexdigest()}'
    
    specimenMeta = {
        'profile': [
            'https://www.medizininformatik-initiative.de/fhir/ext/modul-biobank/StructureDefinition/Specimen|2025.0.4'
        ]
    }

    specimenIdentifier = [
        {
            'system': f'http://medic.uksh.de/fhir/{input_json["organization"]}/Specimen',
            'value': sha224(input_json['specimenId'].encode('utf-8')).hexdigest(),
        }
    ]

    specimenStatus = input_json['specimenStatus']

    specimenType = {
        'coding':  [
            {
                'code': input_json['specimenTypeCode'],
                'system': input_json['specimenTypeSystem']
            }
        ]
    }

    specimenSubject = {
        'reference': f'Patient/PID-{sha224(input_json["mpiId"].encode("utf-8")).hexdigest()}'
    }
    
    localZone = pytz.timezone('Europe/Berlin')
    specimenCollection = {
        'collectedDateTime': input_json['collectedDateTime'],
    }
    
    specimen = Specimen.construct(
        id = specimenId,
        meta = specimenMeta,
        identifier = specimenIdentifier,
        status = specimenStatus,
        type = specimenType,
        subject = specimenSubject,
        collection = specimenCollection
    )

    return [specimen]
