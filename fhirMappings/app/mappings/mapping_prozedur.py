'''
This file is inteded to host the mapping it self. The method map_ressource(..) ist called
in the kafka_consumer.py file within the start_consumer() method.
'''

import json
from hashlib import sha224
from fhir.resources.R4B.procedure import Procedure
from datetime import datetime
import pytz

def mapSnomed(displayString):
    match displayString:
        case 'Diagnostic assessment':
            return '165197003'
        case 'Diagnostic procedure':
            return '165197003'
        case 'Imaging':
            return '363679005'
        case 'Surgical procedure':
            return '387713003'
        case 'Administration of drug or medicament':
            return '18629005'
        case 'Administration of medicine':
            return '18629005'
        case 'Therapeutic procedure':
            return '277132007'
        case 'Other category':
            return '394841004'

def map_ressource(input_json):
    """
        Args:
            input_json (json): A json object
        Returns:
            str:    A str that must be valid json. Since we are mapping with fhir.resources 
                    this should be ensured id <ressource>.json() ist used for returning.
    """

    procedureId = f'PR-{sha224(input_json["compositionId"].encode("utf-8")).hexdigest()}'
    
    procedureMeta = {
        'profile': [
            'https://www.medizininformatik-initiative.de/fhir/core/modul-prozedur/StructureDefinition/Procedure|2025.0.0'
        ]
    }
    
    procedureStatus = 'completed'
    
    if input_json['categorySystem'] is None:
        procedureCategory = {
            'coding': [
                {
                    'system': 'http://snomed.info/sct',
                    'code': mapSnomed(input_json['categoryNoncoded'])
                }
            ]
        }
    else:
        procedureCategory = {
            'coding': [
                {
                    'system': 'http://snomed.info/sct' if input_json['categorySystem'] == 'SNOMED Clinical Terms' else input_json['categorySystem'],
                    'code': input_json['category']
                }
            ]
        }
    
    codeSystem = input_json['codeSystem'].replace('OPS', 'ops')
    procedureCode = {
        'coding': [
            {
                'system': codeSystem.split('|')[0] if '|' in codeSystem else codeSystem,
                'code': input_json['code'],
                'version': codeSystem.split('|')[1] if '|' in codeSystem else None
            }
        ]
    }
    
    procedureSubject = {
        'reference': f'Patient/PID-{sha224(input_json["mpiId"].encode("utf-8")).hexdigest()}'
    }

    procedureEncounter = {
        'reference': f'Encounter/PV-{sha224(input_json["encounterId"].encode("utf-8")).hexdigest()}'
    }
    
    localZone = pytz.timezone('Europe/Berlin')
    procedurePerformedDateTime = localZone.localize(datetime.fromisoformat(input_json["performedDate"])).isoformat()

    procedure = Procedure.construct(
        id = procedureId,
        meta = procedureMeta,
        status = procedureStatus,
        category = procedureCategory,
        code = procedureCode,
        subject = procedureSubject,
        encounter = procedureEncounter,
        performedDateTime = procedurePerformedDateTime
    )

    return [procedure]
