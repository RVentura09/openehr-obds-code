'''
This file is inteded to host the mapping it self. The method map_ressource(..) ist called
in the kafka_consumer.py file within the start_consumer() method.
'''

import json
from hashlib import sha224
from fhir.resources.R4B.consent import Consent
from fhir.resources.R4B.provenance import Provenance
from datetime import datetime
from dateutil.relativedelta import relativedelta
import pytz

def map_ressource(input_json):
    """
        Args:
            input_json (json): A json object
        Returns:
            str:    A str that must be valid json. Since we are mapping with fhir.resources 
                    this should be ensured id <ressource>.json() ist used for returning.
    """

    consentId = f'IC-{sha224(input_json["reportId"].encode("utf-8")).hexdigest()}'
    
    consentMeta = {
        'profile': [
            'https://www.medizininformatik-initiative.de/fhir/modul-consent/StructureDefinition/mii-pr-consent-einwilligung|2025.0.1'
        ]
    }
    
    consentStatus = 'active'
    
    consentScope = {
        'coding': [
            {
                'system': 'http://terminology.hl7.org/CodeSystem/consentscope',
                'code': 'research'
            }
        ]
    }
    
    consentCategory = [
        {
            'coding': [
                {
                    'system': 'http://loinc.org',
                    'code': '57016-8'
                }
            ]
        },
        {
            'coding': [
                {
                    'system': 'https://www.medizininformatik-initiative.de/fhir/modul-consent/CodeSystem/mii-cs-consent-consent_category',
                    'code': '2.16.840.1.113883.3.1937.777.24.2.184'
                }
            ]
        }
    ]
    
    consentPatient = {
        'reference': f'Patient/PID-{sha224(input_json["mpiId"].encode("utf-8")).hexdigest()}'
    }
    
    consentDateTimeStart = input_json["startDate"][:10]
    consentDateTimeEnd = str(datetime.strptime(consentDateTimeStart, '%Y-%m-%d') + relativedelta(years = 1000))[:10]
    
    consentPolicy = [
        {
            'uri': '2.16.840.1.113883.3.1937.777.24.2.1791'
        }
    ]
    
    # opt in, so per default set everything to deny
    consentProvision = {
        'type': 'deny',
        'period': {
            'start': consentDateTimeStart,
            'end': consentDateTimeEnd
        }
    }
    
    # see: https://wiki.medicsh.de/display/MEDIC/Consent+mapping
    # all permits for questions 1 or 2 or 3 or 4
    if "1.2.276.0.76.3.1.454.1.100.1.1.1.1" in input_json['policy'] or "1.2.276.0.76.3.1.454.1.100.1.1.2.1" in input_json['policy'] or "1.2.276.0.76.3.1.454.1.100.1.1.3.1" in input_json['policy'] or "1.2.276.0.76.3.1.454.1.100.1.1.4.1" in input_json['policy']:
        consentProvision['provision'] = [
                {
                'type': 'permit',
                'period': {
                    'start': consentDateTimeStart,
                    'end': consentDateTimeEnd
                },
                'code':  [
                    {
                        'coding':  [
                            {
                                'system': 'urn:oid:2.16.840.1.113883.3.1937.777.24.5.3',
                                'code': '2.16.840.1.113883.3.1937.777.24.5.3.2',
                                'display': 'IDAT erheben'
                            }
                        ]
                    },
                    {
                        'coding':  [
                            {
                                'system': 'urn:oid:2.16.840.1.113883.3.1937.777.24.5.3',
                                'code': '2.16.840.1.113883.3.1937.777.24.5.3.3',
                                'display': 'IDAT speichern, verarbeiten'
                            }
                        ]
                    }
                ]
            }
        ]
    
    # add only those specific to question 1 or 2
    if "1.2.276.0.76.3.1.454.1.100.1.1.1.1" in input_json['policy'] or "1.2.276.0.76.3.1.454.1.100.1.1.2.1" in input_json['policy']:
        consentProvision['provision'][0]['code'].append(
            {
                'coding':  [
                    {
                        'system': 'urn:oid:2.16.840.1.113883.3.1937.777.24.5.3',
                        'code': '2.16.840.1.113883.3.1937.777.24.5.3.4',
                        'display': 'IDAT zusammenfuehren Dritte'
                    }
                ]
            }
        )
        consentProvision['provision'][0]['code'].append(
            {
                'coding':  [
                    {
                        'system': 'urn:oid:2.16.840.1.113883.3.1937.777.24.5.3',
                        'code': '2.16.840.1.113883.3.1937.777.24.5.3.5',
                        'display': 'IDAT bereitstellen EU DSGVO NIVEAU'
                    }
                ]
            }
        )
        
    # add only those specific to question 1
    if "1.2.276.0.76.3.1.454.1.100.1.1.1.1" in input_json['policy']:
        consentProvision['provision'][0]['code'].append(
            {
                'coding':  [
                    {
                        'system': 'urn:oid:2.16.840.1.113883.3.1937.777.24.5.3',
                        'code': '2.16.840.1.113883.3.1937.777.24.5.3.6',
                        'display': 'MDAT erheben'
                    }
                ]
            }
        )
        consentProvision['provision'][0]['code'].append(
            {
                'coding':  [
                    {
                        'system': 'urn:oid:2.16.840.1.113883.3.1937.777.24.5.3',
                        'code': '2.16.840.1.113883.3.1937.777.24.5.3.7',
                        'display': 'MDAT speichern, verarbeiten'
                    }
                ]
            }
        )
        consentProvision['provision'][0]['code'].append(
            {
                'coding':  [
                    {
                        'system': 'urn:oid:2.16.840.1.113883.3.1937.777.24.5.3',
                        'code': '2.16.840.1.113883.3.1937.777.24.5.3.8',
                        'display': 'MDAT wissenschaftlich nutzen EU DSGVO NIVEAU'
                    }
                ]
            }
        )
        consentProvision['provision'][0]['code'].append(
            {
                'coding':  [
                    {
                        'system': 'urn:oid:2.16.840.1.113883.3.1937.777.24.5.3',
                        'code': '2.16.840.1.113883.3.1937.777.24.5.3.9',
                        'display': 'MDAT zusammenfuehren Dritte'
                    }
                ]
            }
        )
        consentProvision['provision'][0]['code'].append(
            {
                'coding':  [
                    {
                        'system': 'urn:oid:2.16.840.1.113883.3.1937.777.24.5.3',
                        'code': '2.16.840.1.113883.3.1937.777.24.5.3.45',
                        'display': 'MDAT retrospektiv speichern verarbeiten'
                    }
                ]
            }
        )
        consentProvision['provision'][0]['code'].append(
            {
                'coding':  [
                    {
                        'system': 'urn:oid:2.16.840.1.113883.3.1937.777.24.5.3',
                        'code': '2.16.840.1.113883.3.1937.777.24.5.3.46',
                        'display': 'MDAT retrospektiv wissenschaftlich nutzen EU DSGVO NIVEAU'
                    }
                ]
            }
        )
        consentProvision['provision'][0]['code'].append(
            {
                'coding':  [
                    {
                        'system': 'urn:oid:2.16.840.1.113883.3.1937.777.24.5.3',
                        'code': '2.16.840.1.113883.3.1937.777.24.5.3.47',
                        'display': 'MDAT retrospektiv zusammenfuehren Dritte'
                    }
                ]
            }
        )
        
    # add only those specific to question 2
    if "1.2.276.0.76.3.1.454.1.100.1.1.2.1" in input_json['policy']:
        consentProvision['provision'][0]['code'].append(
            {
                'coding':  [
                    {
                        'system': 'urn:oid:2.16.840.1.113883.3.1937.777.24.5.3',
                        'code': '2.16.840.1.113883.3.1937.777.24.5.3.19',
                        'display': 'BIOMAT erheben'
                    }
                ]
            }
        )
        consentProvision['provision'][0]['code'].append(
            {
                'coding':  [
                    {
                        'system': 'urn:oid:2.16.840.1.113883.3.1937.777.24.5.3',
                        'code': '2.16.840.1.113883.3.1937.777.24.5.3.20',
                        'display': 'BIOMAT lagern verarbeiten'
                    }
                ]
            }
        )
        consentProvision['provision'][0]['code'].append(
            {
                'coding':  [
                    {
                        'system': 'urn:oid:2.16.840.1.113883.3.1937.777.24.5.3',
                        'code': '2.16.840.1.113883.3.1937.777.24.5.3.21',
                        'display': 'BIOMAT Eigentum übertragen'
                    }
                ]
            }
        )
        consentProvision['provision'][0]['code'].append(
            {
                'coding':  [
                    {
                        'system': 'urn:oid:2.16.840.1.113883.3.1937.777.24.5.3',
                        'code': '2.16.840.1.113883.3.1937.777.24.5.3.22',
                        'display': 'BIOMAT wissenschaftlich nutzen EU DSGVO NIVEAU'
                    }
                ]
            }
        )
        consentProvision['provision'][0]['code'].append(
            {
                'coding':  [
                    {
                        'system': 'urn:oid:2.16.840.1.113883.3.1937.777.24.5.3',
                        'code': '2.16.840.1.113883.3.1937.777.24.5.3.23',
                        'display': 'BIOMAT Analysedaten zusammenfuehren Dritte'
                    }
                ]
            }
        )
        consentProvision['provision'][0]['code'].append(
            {
                'coding':  [
                    {
                        'system': 'urn:oid:2.16.840.1.113883.3.1937.777.24.5.3',
                        'code': '2.16.840.1.113883.3.1937.777.24.5.3.51',
                        'display': 'BIOMAT retrospektiv lagern verarbeiten'
                    }
                ]
            }
        )
        consentProvision['provision'][0]['code'].append(
            {
                'coding':  [
                    {
                        'system': 'urn:oid:2.16.840.1.113883.3.1937.777.24.5.3',
                        'code': '2.16.840.1.113883.3.1937.777.24.5.3.52',
                        'display': 'BIOMAT retrospektiv wissenschaftlich nutzen EU DSGVO NIVEAU'
                    }
                ]
            }
        )
        consentProvision['provision'][0]['code'].append(
            {
                'coding':  [
                    {
                        'system': 'urn:oid:2.16.840.1.113883.3.1937.777.24.5.3',
                        'code': '2.16.840.1.113883.3.1937.777.24.5.3.53',
                        'display': 'BIOMAT retrospektiv Analysedaten zusammenfuehren Dritte'
                    }
                ]
            }
        )
        
    # add only those specific to question 3
    if "1.2.276.0.76.3.1.454.1.100.1.1.3.1" in input_json['policy']:
        consentProvision['provision'][0]['code'].append(
            {
                'coding':  [
                    {
                        'system': 'urn:oid:2.16.840.1.113883.3.1937.777.24.5.3',
                        'code': '2.16.840.1.113883.3.1937.777.24.5.3.37',
                        'display': 'Rekontaktierung Ergebnisse erheblicher Bedeutung'
                    }
                ]
            }
        )
        consentProvision['provision'][0]['code'].append(
            {
                'coding':  [
                    {
                        'system': 'urn:oid:2.16.840.1.113883.3.1937.777.24.5.3',
                        'code': '2.16.840.1.113883.3.1937.777.24.5.3.31',
                        'display': 'Rekontaktierung Zusatzbefund'
                    }
                ]
            }
        )

    # add only those specific to question 4
    if "1.2.276.0.76.3.1.454.1.100.1.1.4.1" in input_json['policy']:
        consentProvision['provision'][0]['code'].append(
            {
                'coding':  [
                    {
                        'system': 'urn:oid:2.16.840.1.113883.3.1937.777.24.5.3',
                        'code': '2.16.840.1.113883.3.1937.777.24.5.3.28',
                        'display': 'Rekontaktierung weitere Erhebung'
                    }
                ]
            }
        )
        consentProvision['provision'][0]['code'].append(
            {
                'coding':  [
                    {
                        'system': 'urn:oid:2.16.840.1.113883.3.1937.777.24.5.3',
                        'code': '2.16.840.1.113883.3.1937.777.24.5.3.29',
                        'display': 'Rekontaktierung weitere Studien'
                    }
                ]
            }
        )

    consent = Consent.construct(
        id = consentId,
        meta = consentMeta,
        status = consentStatus,
        scope = consentScope,
        category = consentCategory,
        patient = consentPatient,
        dateTime = consentDateTimeStart,
        policy = consentPolicy,
        provision = consentProvision
    )

    provenanceId = f'PRV-{sha224(input_json["reportId"].encode("utf-8")).hexdigest()}'
    
    provenanceMeta = {
        'profile': [
            'https://www.medizininformatik-initiative.de/fhir/modul-consent/StructureDefinition/mii-pr-consent-provenance|2025.0.1'
        ]
    }
    
    provenanceTarget = {
        'reference': f'Consent/{consentId}'
    }
    
    localZone = pytz.timezone('Europe/Berlin')
    provenanceRecorded = localZone.localize(datetime.fromisoformat(input_json["startDate"])).isoformat()
    
    provenanceAgent = [
        {
            'who': {
                'display': 'ORBIS'
            }
        }
    ]
    
    provenance = Provenance.construct(
        id = provenanceId,
        meta = provenanceMeta,
        target = provenanceTarget,
        recorded = provenanceRecorded,
        agent = provenanceAgent
    )

    return [consent, provenance]
