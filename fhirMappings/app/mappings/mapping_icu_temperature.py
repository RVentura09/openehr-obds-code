import logging
from datetime import datetime
from hashlib import sha224
from fhir.resources.R4B.observation import Observation
from .helper_functions import has_consent, get_encounter
import pytz
import os

logger = logging.getLogger(__name__)


def get_profile(field_name):
    match(field_name):
        case 'CO_Vital_Temp1':
            return 'https://gematik.de/fhir/isik/StructureDefinition/sd-mii-icu-koerpertemperatur-harnblase|4.0.1'
        case 'CO_Vital_Temp2':
            return 'https://gematik.de/fhir/isik/StructureDefinition/sd-mii-icu-koerpertemperatur-blut|4.0.1'
        case 'CO_Vital_Temp3':
            return 'https://gematik.de/fhir/isik/StructureDefinition/sd-mii-icu-koerpertemperatur-nasal|4.0.1'
        case 'CO_Vital_Temp4':
            return 'https://gematik.de/fhir/isik/StructureDefinition/sd-mii-icu-koerpertemperatur-rektal|4.0.1'
        case _:
            return None

def get_codes(field_name):
    match(field_name):
        case 'CO_Vital_Temp1':
            return [
                {
                    'system': 'http://loinc.org',
                    'code': '8334-5',
                    'display': 'Body temperature - Urinary bladder'
                },
                {
                    'system': 'http://snomed.info/sct',
                    'code': '698832009',
                    'display': 'Core body temperature measured at urinary bladder (observable entity)'
                },
            ]
        case 'CO_Vital_Temp2':
            return [
                {
                    'system': 'http://loinc.org',
                    'code': '60834-9',
                    'display': 'Blood temperature'
                },
                {
                    'system': 'http://snomed.info/sct',
                    'code': '1222808002',
                    'display': 'Core body temperature measured in blood (observable entity)'
                },
                {
                    'system': 'urn:iso:std:iso:11073:10101',
                    'code': '188436',
                    'display': 'Blood temperature'
                }
            ]
        case 'CO_Vital_Temp3':
            return [
                {
                    'system': 'http://loinc.org',
                    'code': '76010-8',
                    'display': 'Nasal temperature'
                },
                {
                    'system': 'urn:iso:std:iso:11073:10101',
                    'code': '188504',
                    'display': 'Nasal temperature'
                }
            ]
        case 'CO_Vital_Temp4':
            return [
                {
                    'system': 'http://loinc.org',
                    'code': '8332-9',
                    'display': 'Rectal temperature'
                },
                {
                    'system': 'http://snomed.info/sct',
                    'code': '307047009',
                    'display': 'Core body temperature measured in rectum (observable entity)'
                },
                {
                    'system': 'urn:iso:std:iso:11073:10101',
                    'code': '188420',
                    'display': 'Rectal temperature'
                }
            ]
        case _:
            return None


def get_body_site(field_name):
    match(field_name):
        case 'CO_Vital_Temp1':
            return {
                "coding":  [
                    {
                        "system": "http://snomed.info/sct",
                        "code": "89837001",
                        "display": "Urinary bladder structure (body structure)"
                    }
                ]
            }
        case 'CO_Vital_Temp3':
            return {
                "coding":  [
                    {
                        "system": "http://snomed.info/sct",
                        "code": "45206002",
                        "display": "Nasal structure (body structure)"
                    }
                ]
            }
        case 'CO_Vital_Temp4':
            return {
                "coding":  [
                    {
                        "system": "http://snomed.info/sct",
                        "code": "34402009",
                        "display": "Rectum structure (body structure)"
                    }
                ]
            }
        case _:
            return None


def map_ressource(input_json):

    patientId = f'PID-{sha224(input_json["mpi"].encode("utf-8")).hexdigest()}'

    if os.environ["CHECK_CONSENT"] == 'True':
        if not has_consent(patientId):
            logger.info(f'Patient with Id {patientId} has no consent. Returning without mapping.')
            return []
        else:
            logger.info(f'Patient with Id {patientId} has consent. Proceed with mapping...')

    observationId = f'IU-TEMP-{sha224(input_json["measurement_id"].encode("utf-8")).hexdigest()}'

    observationMeta = {
        'profile': [
            'https://gematik.de/fhir/isik/StructureDefinition/sd-mii-icu-koerpertemperatur-generisch|4.0.1',
            'https://gematik.de/fhir/isik/StructureDefinition/sd-mii-icu-monitoring-und-vitaldaten|4.0.1'
        ]
    }
    specific_profile = get_profile(input_json['field_name'])
    if specific_profile != None:
        observationMeta['profile'].append(specific_profile)

    categoryCoding = {
        'coding': [
            {
                'system': 'http://terminology.hl7.org/CodeSystem/observation-category',
                'code': 'vital-signs',
            }
        ]
    }

    coding_loinc = {
        'system': 'http://loinc.org',
        'code': '8310-5',
        'display': 'Body temperature'
    }

    code = {
        'coding': [coding_loinc]
    }
    specific_codes = get_codes(input_json['field_name'])
    if specific_codes != None:
        code['coding'] += specific_codes

    subject = {
        'reference': f'Patient/{patientId}'
    }

    localZone = pytz.timezone('Europe/Berlin')
    dateTime = localZone.localize(datetime.fromisoformat(input_json["date_created"]))
    dateTimeFhir = dateTime.isoformat()

    value = {
        'value': float(input_json["value"]),
        'unit': 'degree Celsius',
        'system': 'http://unitsofmeasure.org',
        'code': 'Cel'
    }

    observation = Observation.construct(
        id = observationId,
        meta = observationMeta,
        status = 'final',
        category = [categoryCoding],
        code = code,
        subject = subject,
        effectiveDateTime = dateTimeFhir,
        valueQuantity = value
    )

    body_site = get_body_site(input_json['field_name'])
    if body_site != None:
        observation.bodySite = body_site

    encounter_id = get_encounter(patientId, dateTime)
    if encounter_id != None:
        encounter = {
            'reference': f'Encounter/{encounter_id}'
        }
        observation.encounter = encounter

    logger.debug(observation.json())

    return [observation]

