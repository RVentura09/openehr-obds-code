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
        case 'Maske':
            return create_code('428311008')
        case 'PSV':
            return create_code('1186731003')
        case 'APCV':
            return create_code('1259864003')
        case 'PC-PSV':
            return create_code('1186622005')
        case 'SPN-CPAP/PS':
            return create_code('1186681001')
        case 'NIV-PC-PSV':
            return create_code('447837008')
        case 'Beutel-Tubus':
            return create_code('243140006')
        case 'Dyn. Bilevel':
            return create_code('1186681001')
        case 'VCV':
            return create_code('1186749003')
        case 'Bilevel ST':
            return create_code('34291000175108')
        case 'BIPAP':
            return create_code('243142003')
        case 'High-Flow':
            return create_code('870533002')
        case 'Maskenbeatmung':
            return create_code('428311008')
        case 'HFOT':
            return create_code('870533002')
        case 'Brille':
            return create_code('371907003')
        case 'Reservoir-Maske':
            return create_code('243140006')
        case 'CPAP':
            return create_code('47545007')
        case 'PC-SIMV':
            return create_code('1186622005')
        case 'NIV-CPAP':
            return create_code('1186731003')
        case 'High-Flow O2-Therapie':
            return create_code('870533002')
        case 'Bilevel':
            return create_code('1186618000')
        case 'Sprechaufsatz':
            return create_code('1258985005')
        case 'ASB':
            return create_code('243141005')
        case 'SIMV':
            return create_code('59427005')
        case 'VF-AF':
            return create_code('1186674008')
    return create_code('40617009')

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

    procedureId = f'IU-VENT-{sha224(input_json["measurement_id"].encode("utf-8")).hexdigest()}'

    procedureMeta = {
        'profile': [
            'https://www.medizininformatik-initiative.de/fhir/ext/modul-icu/StructureDefinition/beatmung|2025.0.2'
        ]
    }

    procedureStatus = 'in-progress'

    categoryCoding = {
        'coding': [
            {
                'system': 'http://snomed.info/sct',
                'code': '40617009',
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
