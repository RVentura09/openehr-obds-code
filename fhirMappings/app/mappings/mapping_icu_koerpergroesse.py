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

    observationId = f'IU-KGRO-{sha224(input_json["measurement_id"].encode("utf-8")).hexdigest()}'

    observationMeta = {
        'profile': [
            'https://gematik.de/fhir/isik/StructureDefinition/sd-mii-icu-monitoring-und-vitaldaten|4.0.1',
            'https://www.medizininformatik-initiative.de/fhir/ext/modul-icu/StructureDefinition/koerpergroesse|2025.0.2'
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
        'code': '1153637007',
        'display': 'Body height (observable entity)'
    }

    coding_loinc = {
        'system': 'http://loinc.org',
        'code': '8302-2',
        'display': 'Body height'
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

    value = {
        'value': float(input_json["value"]),
        'unit': 'centimeter',
        'system': 'http://unitsofmeasure.org',
        'code': 'cm'
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

    encounter_id = get_encounter(patientId, dateTime)
    if encounter_id != None:
        encounter = {
            'reference': f'Encounter/{encounter_id}'
        }
        observation.encounter = encounter

    logger.debug(observation.json())

    return [observation]
