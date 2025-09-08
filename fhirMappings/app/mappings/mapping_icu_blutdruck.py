import logging
from datetime import datetime
from hashlib import sha224
from fhir.resources.R4B.observation import Observation
from .helper_functions import has_consent, get_encounter
import pytz
import os

logger = logging.getLogger(__name__)


def map_ressource(input_json):

    patientId = f'PID-{sha224(input_json["mpi"].encode("utf-8")).hexdigest()}'

    if os.environ["CHECK_CONSENT"] == 'True':
        if not has_consent(patientId):
            logger.info(f'Patient with Id {patientId} has no consent. Returning without mapping.')
            return []
        else:
            logger.info(f'Patient with Id {patientId} has consent. Proceed with mapping...')

    observationId = f'IU-RRAR-{sha224(input_json["measurement_id"].encode("utf-8")).hexdigest()}'

    observationMeta = {
        'profile': [
            'https://gematik.de/fhir/isik/StructureDefinition/sd-mii-icu-monitoring-und-vitaldaten|4.0.1',
            'https://www.medizininformatik-initiative.de/fhir/ext/modul-icu/StructureDefinition/arterieller-blutdruck|2025.0.2'
        ]
    }

    categoryCoding = {
        'coding': [
            {
                'system': 'http://terminology.hl7.org/CodeSystem/observation-category',
                'code': 'vital-signs',
            }
        ]
    }

    coding_snomed = {
        'system': 'http://snomed.info/sct',
        'code': '364090009',
        "display": "Systemic arterial pressure (observable entity)"
    }

    coding_loinc = {
        'system': 'http://loinc.org',
        'code': '85354-9',
        'display': 'Blood pressure panel with all children optional'
    }

    code = {
        'coding': [coding_snomed, coding_loinc]
    }

    subject = {
        'reference': f'Patient/{patientId}'
    }

    localZone = pytz.timezone('Europe/Berlin')
    dateTime = localZone.localize(datetime.fromisoformat(input_json["date_created"]))
    dateTimeFhir = dateTime.isoformat()

    data_absent_nan = {
            "coding":  [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/data-absent-reason",
                    "code": "not-a-number",
                    "display": "Not a Number (NaN)"
                },
            ]
        }


    systolic_bp = {
        "code": {
            "coding":  [
                {
                    "system": "http://loinc.org",
                    "code": "8480-6",
                    "display": "Systolic blood pressure"
                },
                {
                    "system": "http://snomed.info/sct",
                    "code": "271649006",
                    "display": "Systolic blood pressure (observable entity)"
                },
                {
                    "system": "urn:iso:std:iso:11073:10101",
                    "code": "150017",
                    "display": "Systolic blood pressure"
                }
            ]
        }
    }

    if input_json['systolic'] != '':
        systolic_bp['valueQuantity'] = {
            "value": float(input_json["systolic"]),
            "unit": "millimeter Mercury column",
            "system": "http://unitsofmeasure.org",
            "code": "mm[Hg]"
        }
    else:
        logger.warning(f"Could not parse systolic blood pressure value: '{input_json['systolic']}'")
        systolic_bp['dataAbsentReason'] = data_absent_nan

    diastolic_bp = {
        "code": {
            "coding":  [
                {
                    "system": "http://loinc.org",
                    "code": "8462-4",
                    "display": "Diastolic blood pressure"
                },
                {
                    "system": "http://snomed.info/sct",
                    "code": "271650006",
                    "display": "Diastolic blood pressure (observable entity)"
                },
                {
                    "system": "urn:iso:std:iso:11073:10101",
                    "code": "150018",
                    "display": "Diastolic blood pressure"
                }
            ]
        }
    }
    if input_json['diastolic'] != '':
        diastolic_bp['valueQuantity'] = {
            "value": float(input_json["diastolic"]),
            "unit": "millimeter Mercury column",
            "system": "http://unitsofmeasure.org",
            "code": "mm[Hg]"
        }
    else:
        logger.warning(f"Could not parse diastolic blood pressure value: '{input_json['diastolic']}'")
        diastolic_bp['dataAbsentReason'] = data_absent_nan


    observation = Observation.construct(
        id = observationId,
        meta = observationMeta,
        status = 'final',
        category = [categoryCoding],
        code = code,
        subject = subject,
        effectiveDateTime = dateTimeFhir,
        component = [systolic_bp, diastolic_bp]
    )

    encounter_id = get_encounter(patientId, dateTime)
    if encounter_id != None:
        encounter = {
            'reference': f'Encounter/{encounter_id}'
        }
        observation.encounter = encounter

    logger.debug(observation.json())

    return [observation]
