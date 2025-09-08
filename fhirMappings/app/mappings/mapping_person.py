'''
This file is inteded to host the mapping it self. The method map_ressource(..) ist called
in the kafka_consumer.py file within the start_consumer() method.
'''

import json
import os
import requests
import logging
import jsonpath
from hashlib import sha224
from fhir.resources.R4B.patient import Patient
from datetime import datetime
import pytz

logger = logging.getLogger(__name__)

def mapGender(orbisString):
    match orbisString:
        case 'M':
            return 'male'
        case 'F':
            return 'female'
        case 'X':
            return 'unknown'
        
def mapCountryCode(orbisString):
    code = requests.get(f'{os.environ["ONTOSERVER_ADDRESS"]}/fhir/CodeSystem/$lookup?system=urn:iso:std:iso:3166&code={orbisString}&property=alpha-2')
    if code.status_code != 200:
        return 'DE'
    return jsonpath.findall('$.parameter.*.part[?@.name == "value"].valueCode', code.json())[0]

def map_ressource(input_json):
    """
        Args:
            input_json (json): A json object
        Returns:
            str:    A str that must be valid json. Since we are mapping with fhir.resources 
                    this should be ensured id <ressource>.json() ist used for returning.
    """
    
    patientId = f'PID-{sha224(input_json["mpiId"].encode("utf-8")).hexdigest()}'

    if os.environ["CHECK_CONSENT"] == 'True':
        # fetch consent of patient to check if consent still exists
        consent = requests.get(f'http://{os.environ["FHIR_SERVER_ADDRESS"]}/fhir/Consent?patient=Patient/{patientId}')

        if consent.status_code != 200 or int(consent.json()['total']) == 0:
            logger.info(f'No consent found for patient with id {patientId}. Returning without mapping.')
            return []

        logger.info(f'Found consent for patient with id {patientId}. Proceed with mapping...')
    
    patientMeta = {
        'profile': [
            'https://www.medizininformatik-initiative.de/fhir/core/modul-person/StructureDefinition/PatientPseudonymisiert|2025.0.1'
        ]
    }
    
    patientIdentifier = [
        {
            'use': 'usual',
            'type': {
                'coding':  [
                    {
                        'code': 'PSEUDED',
                        'system': 'http://terminology.hl7.org/CodeSystem/v3-ObservationValue'
                    }
                ]
            },
            'system': 'https://www.medizininformatik-initiative.de/fhir/sid/pseudonym',
            'value': sha224(input_json['mpiId'].encode('utf-8')).hexdigest()
        }
    ]
    
    patientGender = mapGender(input_json['gender'])
    
    patientBirthDate = input_json['birthDate'][:7]
    
    patientDeceasedBoolean = None
    patientDeceasedDateTime = None
    
    if input_json['deceased'] is not None:
        if input_json['deceasedDateTime'] is None or input_json['deceasedDateTime'] == '':
            patientDeceasedBoolean = True
        else:
            localZone = pytz.timezone('Europe/Berlin')
            patientDeceasedDateTime = localZone.localize(datetime.fromisoformat(input_json["deceasedDateTime"])).isoformat()
    
    patientAddress = None
    if input_json['addressPostalCode'] != '':
        patientAddress = [
            {
                'type': input_json['addressType'],
                'postalCode': input_json['addressPostalCode'][:3],
                'country': mapCountryCode(input_json['addressCountry'])
            }
        ]
    
    patient = Patient.construct(
        id = patientId,
        meta = patientMeta,
        identifier = patientIdentifier,
        gender = patientGender,
        birthDate = patientBirthDate,
        deceasedBoolean = patientDeceasedBoolean,
        deceasedDateTime = patientDeceasedDateTime,
        address = patientAddress
    )
    
    return [patient]
