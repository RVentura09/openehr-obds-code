'''
This file is inteded to host the mapping it self. The method map_ressource(..) ist called
in the kafka_consumer.py file within the start_consumer() method.
'''

import json
import os
import requests
import logging
from hashlib import sha224
from fhir.resources.R4B.encounter import Encounter
from fhir.resources.R4B.observation import Observation
import pytz
from datetime import datetime
from calendar import monthrange
from math import ceil

logger = logging.getLogger(__name__)

def map_vitalstatus(patientId, identifier, effective, vitalStatus):
    observationId = f'VIT-{sha224(identifier.encode("utf-8")).hexdigest()}'

    observationMeta = {
        'profile': [
            'https://www.medizininformatik-initiative.de/fhir/core/modul-person/StructureDefinition/Vitalstatus|2025.0.1'
        ]
    }

    observationStatus = 'final'

    observationCategory = [
        {
            'coding': [
                {
                    'system': 'http://terminology.hl7.org/CodeSystem/observation-category',
                    'code': 'survey'
                }
            ]
        }
    ]

    observationCode = {
        'coding':  [
            {
                'code': '67162-8',
                'system': 'http://loinc.org'
            }
        ]
    }

    observationSubject = {
        'reference': f'Patient/{patientId}'
    }

    observationEffective = effective

    observationValueCodeableConcept = {
        'coding':  [
            {
                'code': vitalStatus,
                'system': 'https://www.medizininformatik-initiative.de/fhir/core/modul-person/CodeSystem/Vitalstatus'
            }
        ]
    }

    observation = Observation.construct(
        id = observationId,
        meta = observationMeta,
        status = observationStatus,
        category = observationCategory,
        code = observationCode,
        subject = observationSubject,
        effectiveDateTime = observationEffective,
        valueCodeableConcept = observationValueCodeableConcept
    )

    return observation

def map_class(encounter_type):
    match encounter_type.lower():
        case 'ambulant':
            return 'AMB'
        case 'stationär':
            return 'IMP'
        case 'vorstationär':
            return 'PRENC'
        case 'nachstationär':
            return 'IMP'
        case 'notfall':
            return 'IMP'
        case 'teilstationär':
            return 'IMP'
    return None

def cleanWardName(ward):
    if ward is None:
        return None
    ward = ward.replace("_", "-")
    ward = ward.replace(" ", "")
    ward = ward.replace("Ä", "AE")
    ward = ward.replace("Ö", "OE")
    ward = ward.replace("Ü", "UE")
    ward = ward.replace("??", "-")
    return ward

def calculateEnd(start):
    startDate = datetime.fromisoformat(start)
    localZone = pytz.timezone('Europe/Berlin')
    end = startDate.replace(month = ceil(startDate.month / 3) * 3, day = monthrange(startDate.year, ceil(startDate.month / 3) * 3)[1], hour = 23, minute = 59, second = 59).isoformat()[:19]
    return localZone.localize(datetime.fromisoformat(end)).isoformat()

def map_from_fhir(encounterId):
    departmentLocations = []

    req = requests.get(f'http://{os.environ["FHIR_SERVER_ADDRESS"]}/fhir/Encounter?part-of=Encounter/{encounterId}')
    if req.status_code == 200:
        oldEncounters = req.json()
        if oldEncounters['total'] == 0:
            return departmentLocations

        oldEncounters['entry'] = sorted(oldEncounters['entry'], key=lambda item: datetime.fromisoformat(item['resource']['period']['start']), reverse=False)

        for e in oldEncounters['entry']:
            oldEncounter = e['resource']
            if 'location' not in oldEncounter:
                continue
            for location in oldEncounter['location']:
                departmentLocation = {
                    'periodEnd': None,
                    'periodStart': location['period']['start'][:19],
                    'status': location['status'],
                    'ward': None,
                    'department': None,
                    'encounter_type': '',
                    'lid': None
                }

                if 'end' in location['period']:
                    departmentLocation['periodEnd'] = location['period']['end'][:19]

                for identifier in oldEncounter['identifier']:
                    if identifier['use'] == 'secondary':
                        departmentLocation['department'] = identifier['value'].split('.')[0]
                if location['location']['reference'].replace('Location/', '') == departmentLocation['department']:
                    departmentLocation['ward'] = departmentLocation['department']
                    departmentLocation['department'] = None
                else:
                    departmentLocation['ward'] = location['location']['reference'].replace(f'Location/{departmentLocation["department"]}-', '')

                departmentLocations.append(departmentLocation)

    return departmentLocations

def merge_locations(fhir_locations, json_locations):
    localZone = pytz.timezone('Europe/Berlin')
    merged_locations = []
    i = 0
    if len(fhir_locations) == 0:
        return json_locations
    for jl in json_locations:
        # add locations obtained from fhir if they started earlier than the ones from input_json
        while i < len(fhir_locations) and localZone.localize(datetime.fromisoformat(fhir_locations[i]['periodStart'])) < localZone.localize(datetime.fromisoformat(jl['periodStart'])):
            merged_locations.append(fhir_locations[i])
            i += 1
        # if the start date is the same, the data is already present in the server
        # assuming update, so don't add fhir one
        if i < len(fhir_locations) and jl['periodStart'] == fhir_locations[i]['periodStart']:
            i += 1
        merged_locations.append(jl)
    return merged_locations

def map_ressource(input_json):
    """
        Args:
            input_json (json): A json object
        Returns:
            str:    A str that must be valid json. Since we are mapping with fhir.resources
                    this should be ensured id <ressource>.json() ist used for returning.
    """

    fall = []

    patientId = f'PID-{sha224(input_json["mpiId"].encode("utf-8")).hexdigest()}'

    if os.environ["CHECK_CONSENT"] == 'True':
        # fetch consent of patient to check if consent still exists
        consent = requests.get(f'http://{os.environ["FHIR_SERVER_ADDRESS"]}/fhir/Consent?patient=Patient/{patientId}')

        if consent.status_code != 200 or int(consent.json()['total']) == 0:
            logger.info(f'No consent found for patient with id {patientId}. Returning without mapping.')
            return []

        logger.info(f'Found consent for patient with id {patientId}. Proceed with mapping...')

    # Einrichtungskontakt

    encounterId = f'PV-{sha224(input_json["encounterId"].encode("utf-8")).hexdigest()}'

    encounterMeta = {
        'profile': [
            'https://www.medizininformatik-initiative.de/fhir/core/modul-fall/StructureDefinition/KontaktGesundheitseinrichtung|2025.0.0'
        ]
    }

    encounterIdentifier = [
        {
            'use': 'official',
            'type': {
                'coding': [
                    {
                        'system': 'http://terminology.hl7.org/CodeSystem/v2-0203',
                        'code': 'VN'
                    }
                ]
            },
            'system': 'http://medic.uksh.de/fhir/Encounter',
            'value': sha224(input_json['encounterId'].encode('utf-8')).hexdigest()
        }
    ]

    if 'live' in input_json and input_json['live'] is True:
        encounterMeta['source'] = 'http://medic.uksh.de/source/orbis/adt'
    else:
        encounterMeta['source'] = 'http://medic.uksh.de/source/orbis/legacy'

    encounterStatus = input_json['statusCode']

    encounterClass = None
    type = None

    encounterType = [
        {
            'coding':  [
                {
                    'system': 'http://fhir.de/CodeSystem/Kontaktebene',
                    'code': 'einrichtungskontakt',
                }
            ]
        }
    ]

    encounterSubject = {
        'reference': f'Patient/{patientId}'
    }

    localZone = pytz.timezone('Europe/Berlin')
    encounterPeriod = None
    if input_json['periodStart'] is not None:
        encounterPeriod = {
            'start': localZone.localize(datetime.fromisoformat(input_json["periodStart"])).isoformat()
        }
    if encounterPeriod is not None and input_json['periodEnd'] is not None:
        encounterPeriod['end'] = localZone.localize(datetime.fromisoformat(input_json["periodEnd"])).isoformat()

    encounterHospitalization = None

    # merge locations if two subsequent entries are same location
    departmentLocations = []

    if input_json['statusCode'] == 'finished' and input_json['locations'][-1]['periodEnd'] is None:
        input_json['locations'][-1]['periodEnd'] = input_json['periodEnd']
    fhirLocations = map_from_fhir(encounterId)
    input_json['locations'] = merge_locations(fhirLocations, input_json['locations'])

    for location in input_json['locations']:

        type = map_class(location['encounter_type'])
        if type is not None:
            encounterClass = {
                'code': type,
                'system': 'http://terminology.hl7.org/CodeSystem/v3-ActCode',
            }
            if input_json['live'] is True and type == 'AMB':
                encounterPeriod['end'] = calculateEnd(encounterPeriod['start'])
                if datetime.fromisoformat(encounterPeriod['end']) < localZone.localize(datetime.now()):
                    encounterStatus = 'finished'

        if location['lid'] is not None:
            encounterHospitalization = {
                'admitSource': {
                    'coding':  [
                        {
                            'code': location['lid'],
                            'system': 'http://fhir.de/CodeSystem/dgkev/Aufnahmeanlass'
                        }
                    ]
                }
            }

        location['department'] = cleanWardName(location['department'])
        location['ward'] = cleanWardName(location['ward'])

        if location['department'] is None and location['ward'] is None:
            continue

        if len(departmentLocations) > 0:
            if departmentLocations[-1]['department'] == location['department']:
                departmentPeriodStart = departmentLocations[-1]['periodStart']
                departmentWardLocations = departmentLocations[-1]['wardLocations']
                departmentLocations[-1] = location.copy()
                departmentLocations[-1]['periodStart'] = departmentPeriodStart
                departmentLocations[-1]['wardLocations'] = departmentWardLocations
                if len(departmentLocations[-1]['wardLocations']) == 0:
                    departmentLocations[-1]['wardLocations'].append(location)
                elif departmentLocations[-1]['wardLocations'][-1]['ward'] == location['ward']:
                    wardPeriodStart = departmentLocations[-1]['wardLocations'][-1]['periodStart']
                    departmentLocations[-1]['wardLocations'][-1] = location.copy()
                    departmentLocations[-1]['wardLocations'][-1]['periodStart'] = wardPeriodStart
                else:
                    departmentLocations[-1]['wardLocations'][-1]['status'] = 'completed'
                    if departmentLocations[-1]['wardLocations'][-1]['periodEnd'] is None:
                        departmentLocations[-1]['wardLocations'][-1]['periodEnd'] = location['periodStart']
                    departmentLocations[-1]['wardLocations'].append(location)
            else:
                departmentLocations[-1]['status'] = 'completed'
                if len(departmentLocations[-1]['wardLocations']) > 0:
                    departmentLocations[-1]['wardLocations'][-1]['status'] = 'completed'
                    departmentLocations[-1]['wardLocations'][-1]['periodEnd'] = location['periodStart']
                if departmentLocations[-1]['periodEnd'] is None:
                    departmentLocations[-1]['periodEnd'] = location['periodStart']
                location['wardLocations'] = []
                if location['ward'] is not None:
                    location['wardLocations'].append(location.copy())
                departmentLocations.append(location)
        else:
            location['wardLocations'] = []
            if location['ward'] is not None:
                location['wardLocations'].append(location.copy())
            departmentLocations.append(location)


    if input_json['discharge_type'] == "Tod":
        if encounterHospitalization is None:
            encounterHospitalization = {}
        encounterHospitalization['dischargeDisposition'] = {
            'extension':  [
                {
                    'url': 'http://fhir.de/StructureDefinition/Entlassungsgrund',
                    'extension':  [
                        {
                            'url': 'ErsteUndZweiteStelle',
                            'valueCoding': {
                                'code': '07',
                                'system': 'http://fhir.de/CodeSystem/dkgev/EntlassungsgrundErsteUndZweiteStelle',
                                'display': 'Tod'
                            }
                        },
                        {
                            'url': 'DritteStelle',
                            'valueCoding': {
                                'code': '9',
                                'system': 'http://fhir.de/CodeSystem/dkgev/EntlassungsgrundDritteStelle',
                                'display': 'keine Angabe'
                            }
                        }
                    ]
                }
            ]
        }

    encounter = Encounter.construct(
        id = encounterId,
        identifier = encounterIdentifier,
        meta = encounterMeta,
        status = encounterStatus,
        class_fhir = encounterClass,
        type = encounterType,
        subject = encounterSubject,
        period = encounterPeriod,
        hospitalization = encounterHospitalization,
    )

    # Do not map Vorstationär!
    if type == "PRENC":
        return []

    fall.append(encounter)

    # set Vitalstatus to "L" for the start of every encounter
    fall.append(map_vitalstatus(patientId, f'{input_json["encounterId"]}_start', encounterPeriod['start'], 'L'))
    if encounterStatus == 'finished':
        if input_json['discharge_type'] == "Tod":
            fall.append(map_vitalstatus(patientId, f'{input_json["encounterId"]}_end', encounterPeriod['end'], 'T'))
        elif input_json['discharge_type'] != "":
            fall.append(map_vitalstatus(patientId, f'{input_json["encounterId"]}_end', encounterPeriod['end'], 'L'))

    if type == 'AMB':
        return fall

    # Abteilungskontakt
    for location in departmentLocations:

        key = f'{input_json["encounterId"]}.{location["department"]}.{location["periodStart"]}'
        depEncounterId = f'PV-AK-{sha224(key.encode("utf-8")).hexdigest()}'

        depEncounterIdentifier = [
            {
                'use': 'official',
                'type': {
                    'coding': [
                        {
                            'system': 'http://terminology.hl7.org/CodeSystem/v2-0203',
                            'code': 'VN'
                        }
                    ]
                },
                'system': 'http://medic.uksh.de/fhir/Encounter',
                'value': sha224(input_json['encounterId'].encode('utf-8')).hexdigest()
            },
            {
                'use': 'secondary',
                'type': {
                    'coding': [
                        {
                            'system': 'http://terminology.hl7.org/CodeSystem/v2-0203',
                            'code': 'U'
                        }
                    ]
                },
                'system': 'http://medic.uksh.de.de/fhir/Encounter/department',
                'value': f'{location["ward"] if location["department"] is None else location["department"]}.{location["periodStart"]}'
            }
        ]

        depEncounterPartOf = {
            'reference': f'Encounter/{encounterId}'
        }

        depEncounterType = [
            {
                'coding':  [
                    {
                        'system': 'http://fhir.de/CodeSystem/Kontaktebene',
                        'code': 'abteilungskontakt',
                    }
                ]
            }
        ]

        depEncounterPeriod = {}
        if location['periodStart'] is not None:
            depEncounterPeriod['start'] = localZone.localize(datetime.fromisoformat(location['periodStart'])).isoformat()
        if location['periodEnd'] is not None:
            depEncounterPeriod['end'] = localZone.localize(datetime.fromisoformat(location['periodEnd'])).isoformat()

        depEncounterLocations = []

        for wardLocation in location['wardLocations']:

            if wardLocation["ward"] is None:
                continue
            department = f'{wardLocation["department"]}-'
            if department == 'None-':
                department = ''

            depEncounterLocation = {
                'location': {
                    'reference': f'Location/{department}{wardLocation["ward"]}'
                },
                'status': wardLocation['status'],
                'physicalType': {
                    'coding':  [
                        {
                            'code': 'wa',
                            'system': 'http://terminology.hl7.org/CodeSystem/location-physical-type'
                        }
                    ]
                },
                'period': {
                    'start': localZone.localize(datetime.fromisoformat(wardLocation['periodStart'])).isoformat()
                }
            }
            if wardLocation['periodEnd'] is not None:
                depEncounterLocation['period']['end'] = localZone.localize(datetime.fromisoformat(wardLocation['periodEnd'])).isoformat()

            depEncounterLocations.append(depEncounterLocation)

            # Versorgungsstellenkontakt
            key = f'{input_json["encounterId"]}.{wardLocation["department"]}.{wardLocation["ward"]}.{wardLocation["periodStart"]}'
            wardEncounterId = f'PV-VK-{sha224(key.encode("utf-8")).hexdigest()}'

            wardEncounterIdentifier = [
                {
                    'use': 'official',
                    'type': {
                        'coding': [
                            {
                                'system': 'http://terminology.hl7.org/CodeSystem/v2-0203',
                                'code': 'VN'
                            }
                        ]
                    },
                    'system': 'http://medic.uksh.de/fhir/Encounter',
                    'value': sha224(input_json['encounterId'].encode('utf-8')).hexdigest()
                },
                {
                    'use': 'secondary',
                    'type': {
                        'coding': [
                            {
                                'system': 'http://terminology.hl7.org/CodeSystem/v2-0203',
                                'code': 'U'
                            }
                        ]
                    },
                    'system': 'http://medic.uksh.de.de/fhir/Encounter/department',
                    'value': f'{wardLocation["department"]}.{wardLocation["ward"]}.{wardLocation["periodStart"]}'
                }
            ]

            wardEncounterPartOf = {
                'reference': f'Encounter/{depEncounterId}'
            }

            wardEncounterType = [
                {
                    'coding':  [
                        {
                            'system': 'http://fhir.de/CodeSystem/Kontaktebene',
                            'code': 'versorgungsstellenkontakt',
                        }
                    ]
                }
            ]

            wardEncounterStatus = 'finished'
            if (location['status'] == 'active'):
                wardEncounterStatus = "in-progress"

            wardEncounter = Encounter.construct(
                id = wardEncounterId,
                identifier = wardEncounterIdentifier,
                meta = encounterMeta,
                status = wardEncounterStatus,
                class_fhir = encounterClass,
                type = wardEncounterType,
                partOf = wardEncounterPartOf,
                subject = encounterSubject,
                period = depEncounterLocation['period'],
                location = [depEncounterLocation]
            )

            fall.append(wardEncounter)

        depEncounterStatus = 'finished'
        if (wardLocation['status'] == 'active'):
            depEncounterStatus = "in-progress"

        depEncounter = Encounter.construct(
            id = depEncounterId,
            identifier = depEncounterIdentifier,
            meta = encounterMeta,
            status = depEncounterStatus,
            class_fhir = encounterClass,
            type = depEncounterType,
            partOf = depEncounterPartOf,
            subject = encounterSubject,
            period = depEncounterPeriod,
            location = depEncounterLocations
        )

        fall.append(depEncounter)

    return fall
