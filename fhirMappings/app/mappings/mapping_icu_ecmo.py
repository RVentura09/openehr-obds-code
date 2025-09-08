import logging
from datetime import datetime
from hashlib import sha224
from fhir.resources.R4B.procedure import Procedure
from .helper_functions import has_consent, get_encounter
import pytz
import os

logger = logging.getLogger(__name__)

def map_modus(modus):
    match modus:
        case 'VV peripher':
            return create_code('786453001')
        case 'VA peripher':
            return create_code('786451004')
        case 'VVA peripher':
            return create_code('786451004')
        case 'VV zentral':
            return create_code('786453001')
        case 'VA zentral':
            return create_code('786451004')
        case 'VVA zentral':
            return create_code('786451004')
    return None

def create_code(code):
    return {
        'coding':  [
            {
                'system': 'http://snomed.info/sct',
                'code': code,
            }
        ]
    }

def map_ressource(input_json):

    patientId = f'PID-{sha224(input_json["mpi"].encode("utf-8")).hexdigest()}'

    if os.environ["CHECK_CONSENT"] == 'True':
        if not has_consent(patientId):
            logger.info(f'Patient with Id {patientId} has no consent. Returning without mapping.')
            return []
        else:
            logger.info(f'Patient with Id {patientId} has consent. Proceed with mapping...')

    procedureId = f'IU-ECMO-{sha224(input_json["measurement_id"].encode("utf-8")).hexdigest()}'

    procedureMeta = {
        'profile': [
            'https://www.medizininformatik-initiative.de/fhir/ext/modul-icu/StructureDefinition/extrakorporales-verfahren|2025.0.2'
        ]
    }

    procedureStatus = 'in-progress'

    categoryCoding = {
        'coding': [
            {
                'system': 'http://snomed.info/sct',
                'code': '182744004',
            }
        ]
    }

    code = map_modus(input_json['modus'])

    subject = {
        'reference': f'Patient/{patientId}'
    }

    localZone = pytz.timezone('Europe/Berlin')
    start_date = localZone.localize(datetime.fromisoformat(input_json["date_created"]))
    
    period = {
        'start': start_date.isoformat()
    }

    if input_json['end_time'] != '':
        procedureStatus = 'completed'
        period['end'] = localZone.localize(datetime.fromisoformat(input_json['end_time'])).isoformat()

    procedure = Procedure.construct(
        id = procedureId,
        meta = procedureMeta,
        status = procedureStatus,
        category = categoryCoding,
        code = code,
        subject = subject,
        performedPeriod = period
    )

    encounter_id = get_encounter(patientId, start_date)
    if encounter_id != None:
        encounter = {
            'reference': f'Encounter/{encounter_id}'
        }
        procedure.encounter = encounter

    logger.debug(procedure.json())

    return [procedure]
