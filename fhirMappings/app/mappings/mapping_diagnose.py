'''
This file is inteded to host the mapping it self. The method map_ressource(..) ist called
in the kafka_consumer.py file within the start_consumer() method.
'''

import json
from hashlib import sha224
from fhir.resources.R4B.condition import Condition
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

    conditionId = f'CON-{sha224(input_json["compositionId"].encode("utf-8")).hexdigest()}'
    
    conditionMeta = {
        'profile': [
            'https://www.medizininformatik-initiative.de/fhir/core/modul-diagnose/StructureDefinition/Diagnose|2025.0.0'
        ]
    }
    
    codeSystem = input_json['codeSystem']
    conditionCode = {
        'coding': [
            {
                'system': 'http://fhir.de/CodeSystem/bfarm/icd-10-gm',
                'code': input_json['code'],
                'version': codeSystem.split('|')[1] if '|' in codeSystem else None
            }
        ]
    }
    
    conditionSubject = {
        'reference': f'Patient/PID-{sha224(input_json["mpiId"].encode("utf-8")).hexdigest()}'
    }

    conditionEncounter = {
        'reference': f'Encounter/PV-{sha224(input_json["encounterId"].encode("utf-8")).hexdigest()}'
    }
    
    localZone = pytz.timezone('Europe/Berlin')
    conditionRecordedDate = localZone.localize(datetime.fromisoformat(input_json["recordedDate"])).isoformat()

    
    condition = Condition.construct(
        id = conditionId,
        meta = conditionMeta,
        code = conditionCode,
        subject = conditionSubject,
        encounter = conditionEncounter,
        recordedDate = conditionRecordedDate
    )

    return [condition]
