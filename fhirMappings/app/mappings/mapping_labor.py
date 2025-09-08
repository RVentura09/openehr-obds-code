'''
This file is inteded to host the mapping it self. The method map_ressource(..) ist called
in the kafka_consumer.py file within the start_consumer() method.
'''

import json
from hashlib import sha224
from fhir.resources.R4B.diagnosticreport import DiagnosticReport
from fhir.resources.R4B.observation import Observation
from fhir.resources.R4B.servicerequest import ServiceRequest
from datetime import datetime
import pytz

def convertUnitToCode(unit):
    unit = unit.replace('^', '*')
    unit = unit.replace('/l', '/L')
    unit = unit.replace('ml', 'mL')
    unit = unit.replace('dl', 'dL')
    unit = unit.replace('fl', 'fL')
    unit = unit.replace('µ', 'u')
    unit = unit.replace('sec', 's')
    unit = unit.replace('x10', '10')
    return unit

def map_ressource(input_json):
    """
        Args:
            input_json (json): A json object
        Returns:
            str:    A str that must be valid json. Since we are mapping with fhir.resources 
                    this should be ensured id <ressource>.json() ist used for returning.
    """
    
    if input_json['analytCode'] is None or len(input_json['analytCode']) != len(input_json['interpretationCode']) or len(input_json['analytCode']) != len(input_json['analyt']):
        return []

    requestId = f'LSR-{sha224((input_json["requestId"] if input_json["requestId"] is not None else input_json["compositionId"]).encode("utf-8")).hexdigest()}'

    requestMeta = {
        'profile': [
            'https://www.medizininformatik-initiative.de/fhir/core/modul-labor/StructureDefinition/ServiceRequestLab|2025.0.2'
        ]
    }
    
    requestIdentifier = [
        {
            'type': {
                'coding':  [
                    {
                        'system': 'http://terminology.hl7.org/CodeSystem/v2-0203',
                        'code': 'PLAC'
                    }
                ]
            },
            'system': 'http://medic.uksh.de/fhir/ServiceRequest',
            'value': sha224((input_json["requestId"] if input_json["requestId"] is not None else input_json["compositionId"]).encode("utf-8")).hexdigest(),
            'assigner': {
                'display': 'Universitätsklinikum Schleswig-Holstein',
                'identifier': {
                    'system': 'https://www.medizininformatik-initiative.de/fhir/core/CodeSystem/core-location-identifier',
                    'value': 'UKSH'
                }
            }
        }
    ]
    
    requestStatus = 'completed'
    
    requestIntent = 'order'
    
    requestCategory = [
        {
            'coding': [
                {
                    'code': 'laboratory',
                    'system': 'http://terminology.hl7.org/CodeSystem/observation-category'
                }
            ]
        }
    ]
    
    requestCode = {
        'coding':  [
            {
                'code': input_json['requestCode'] if input_json['requestCode'] is not None else "Unknown",
                'system': 'http://medic.uksh.de/fhir/CodeSystem/LabTests'
            }
        ]
    }
    
    requestSubject = {
        'reference': f'Patient/PID-{sha224(input_json["mpiId"].encode("utf-8")).hexdigest()}'
    }

    requestEncounter = {
        'reference': f'Encounter/PV-{sha224(input_json["encounterId"].encode("utf-8")).hexdigest()}'
    }
    
    localZone = pytz.timezone('Europe/Berlin')
    requestAuthoredOn = localZone.localize(datetime.fromisoformat(input_json["effective"])).isoformat()

    request = ServiceRequest.construct(
        id = requestId,
        meta = requestMeta,
        identifier = requestIdentifier,
        status = requestStatus,
        intent = requestIntent,
        category = requestCategory,
        code = requestCode,
        subject = requestSubject,
        encounter = requestEncounter,
        authoredOn = requestAuthoredOn
    )

    results = []
    for i in range(len(input_json['analytCode'])-1):
        
        if input_json['analytCodeUKSH'][i] in ['LAB_medik', 'LAB_diag'] or 'value' not in input_json['analyt'][i]:
            continue
        
        idString = f'{input_json["reportId"]}_{input_json["analytCode"][i]}'
        resultId = f'LAB-{sha224(idString.encode("utf-8")).hexdigest()}'
        
        resultMeta = {
            'profile': [
                'https://www.medizininformatik-initiative.de/fhir/core/modul-labor/StructureDefinition/ObservationLab|2025.0.2'
            ]
        }
        
        resultIdentifier = [
            {
                'type': {
                    'coding':  [
                        {
                            'system': 'http://terminology.hl7.org/CodeSystem/v2-0203',
                            'code': 'OBI'
                        }
                    ]
                },
                'system': 'http://medic.uksh.de/fhir/Observation',
                'value': f'{sha224((input_json["requestId"] if input_json["requestId"] is not None else input_json["compositionId"]).encode("utf-8")).hexdigest()}-{input_json["analytCodeUKSH"][i]}',
                'assigner': {
                    'display': 'Universitätsklinikum Schleswig-Holstein',
                    'identifier': {
                        'system': 'https://www.medizininformatik-initiative.de/fhir/core/CodeSystem/core-location-identifier',
                        'value': 'UKSH'
                    }
                }
            }
        ]
        
        resultStatus = 'final'
        
        resultCategory = [
            {
                'coding': [
                    {
                        'code': input_json['category'],
                        'system': 'http://loinc.org',
                        'display': 'Laboratory studies (set)'
                    },
                    {
                        'code': 'laboratory',
                        'system': 'http://terminology.hl7.org/CodeSystem/observation-category',
                        'display': 'Laboratory'
                    }
                ]   
            }
        ]
        
        resultCode = {
            'coding': [
                {
                    'code': input_json['analytCodeUKSH'][i],
                    'system': input_json['analytCodeSystemUKSH'][i]
                }
            ]
        }
        
        if input_json['analytCodeUKSH'][i] != "Unknown":
            resultCode['coding'].append({
                'code': input_json['analytCode'][i],
                'system': input_json['analytCodeSystem'][i]
            })
        
        resultSubject = {
            'reference': f'Patient/PID-{sha224(input_json["mpiId"].encode("utf-8")).hexdigest()}'
        }

        resultEncounter = {
            'reference': f'Encounter/PV-{sha224(input_json["encounterId"].encode("utf-8")).hexdigest()}'
        }
        
        resultEffective = localZone.localize(datetime.fromisoformat(input_json["effective"])).isoformat()
        
        resultInterpretation = [
            {
                'coding': [
                    {
                        'code': input_json['interpretationCode'][i],
                        'system': input_json['interpretationSystem'][i]
                    }
                ]
            }
        ]
        
        resultValueQuantity = None
        resultQuantityReferenceRange = None
        
        if input_json['analyt'][i]['value']['@class'] == "DV_QUANTITY":
            resultValueQuantity = {
                'system': 'http://unitsofmeasure.org',
                'value': input_json['analyt'][i]['value']['magnitude'],
                'unit': input_json['analyt'][i]['value']['units'],
                'code': convertUnitToCode(input_json['analyt'][i]['value']['units'])
            }
        
            if 'normal_range' in input_json['analyt'][i]['value']:
                resultQuantityReferenceRange = [
                    {
                        'type': {
                            'coding': [
                                {
                                    'code': 'normal',
                                    'system': 'http://terminology.hl7.org/CodeSystem/referencerange-meaning'
                                }
                            ]
                        }
                    }
                ]
                if 'lower' in input_json['analyt'][i]['value']['normal_range']:
                    resultQuantityReferenceRange[0]['low'] = {
                        'value': input_json['analyt'][i]['value']['normal_range']['lower']['magnitude'],
                        'unit': input_json['analyt'][i]['value']['normal_range']['lower']['units'],
                        'system': 'http://unitsofmeasure.org',
                        'code': convertUnitToCode(input_json['analyt'][i]['value']['units'])
                    }
                if 'upper' in input_json['analyt'][i]['value']['normal_range']:
                    resultQuantityReferenceRange[0]['high'] = {
                        'value': input_json['analyt'][i]['value']['normal_range']['upper']['magnitude'],
                        'unit': input_json['analyt'][i]['value']['normal_range']['upper']['units'],
                        'system': 'http://unitsofmeasure.org',
                        'code': convertUnitToCode(input_json['analyt'][i]['value']['units'])
                    }

        resultValueCodeableConcept = None

        if input_json['analyt'][i]['value']['@class'] == "DV_TEXT":
            if input_json['analyt'][i]['value']['value'] in ['neg', 'negativ']:
                resultValueCodeableConcept = {
                    'coding': [
                        {
                            'system': 'http://snomed.info/sct',
                            'code': '260385009',
                            'display': 'Negative (qualifier value)'
                        }
                    ]
                }
            elif input_json['analyt'][i]['value']['value'] in ['pos', 'positiv']:
                resultValueCodeableConcept = {
                    'coding': [
                        {
                            'system': 'http://snomed.info/sct',
                            'code': '10828004',
                            'display': 'Positive (qualifier value)'
                        }
                    ]
                }
            elif input_json['analyt'][i]['value']['value'] == '++++':
                resultValueCodeableConcept = {
                    'coding': [
                        {
                            'system': 'http://snomed.info/sct',
                            'code': '260350009',
                            'display': 'Present ++++ out of ++++ (qualifier value)'
                        }
                    ]
                }
            elif input_json['analyt'][i]['value']['value'] == '+++':
                resultValueCodeableConcept = {
                    'coding': [
                        {
                            'system': 'http://snomed.info/sct',
                            'code': '260349009',
                            'display': 'Present +++ out of ++++ (qualifier value)'
                        }
                    ]
                }
            elif input_json['analyt'][i]['value']['value'] == '++':
                resultValueCodeableConcept = {
                    'coding': [
                        {
                            'system': 'http://snomed.info/sct',
                            'code': '260348001',
                            'display': 'Present ++ out of ++++ (qualifier value)'
                        }
                    ]
                }
            elif input_json['analyt'][i]['value']['value'] == '+':
                resultValueCodeableConcept = {
                    'coding': [
                        {
                            'system': 'http://snomed.info/sct',
                            'code': '260347006',
                            'display': 'Present + out of ++++ (qualifier value)'
                        }
                    ]
                }
            else:
                continue

        result = Observation.construct(
            id = resultId,
            meta = resultMeta,
            identifier = resultIdentifier,
            status = resultStatus,
            category = resultCategory,
            code = resultCode,
            subject = resultSubject,
            encounter = resultEncounter,
            effectiveDateTime = resultEffective,
            valueQuantity = resultValueQuantity,
            valueCodeableConcept = resultValueCodeableConcept,
            interpretation = resultInterpretation,
            referenceRange = resultQuantityReferenceRange
        )
        
        results.append(result)

    reportId = f'REP-{sha224(input_json["reportId"].encode("utf-8")).hexdigest()}'
    
    reportMeta = {
        'profile': [
            'https://www.medizininformatik-initiative.de/fhir/core/modul-labor/StructureDefinition/DiagnosticReportLab|2025.0.2'
        ]
    }
    
    reportIdentifier = [
        {
            'type': {
                'coding':  [
                    {
                        'system': 'http://terminology.hl7.org/CodeSystem/v2-0203',
                        'code': 'FILL'
                    }
                ]
            },
            'system': 'http://medic.uksh.de/fhir/DiagnosticReport',
            'value': sha224(input_json['reportId'].encode('utf-8')).hexdigest(),
            'assigner': {
                'display': 'Universitätsklinikum Schleswig-Holstein',
                'identifier': {
                    'system': 'https://www.medizininformatik-initiative.de/fhir/core/CodeSystem/core-location-identifier',
                    'value': 'UKSH'
                }
            }
        }
    ]
    
    reportBasedOn = {
        'reference': f'ServiceRequest/LSR-{sha224((input_json["requestId"] if input_json["requestId"] is not None else input_json["compositionId"]).encode("utf-8")).hexdigest()}'
    }
    
    reportStatus = input_json['statusCode']
    
    reportCategory = [
        {
            'coding': [
                {
                    'code': input_json['category'],
                    'system': 'http://loinc.org',
                    'display': 'Laboratory studies (set)'
                },
                {
                    'code': 'LAB',
                    'system': 'http://terminology.hl7.org/CodeSystem/v2-0074'    
                }
            ]
        }
    ]
        
    reportCode = {
        'coding': [
            {
                'code': '11502-2',
                'system': 'http://loinc.org',
                'display': 'Laboratory report'
            }
        ]
    }
    
    reportSubject = {
        'reference': f'Patient/PID-{sha224(input_json["mpiId"].encode("utf-8")).hexdigest()}'
    }

    reportEncounter = {
        'reference': f'Encounter/PV-{sha224(input_json["encounterId"].encode("utf-8")).hexdigest()}'
    }
    
    reportIssued = localZone.localize(datetime.fromisoformat(input_json["issued"])).isoformat()

    reportEffective = localZone.localize(datetime.fromisoformat(input_json["effective"])).isoformat()
    
    reportResult = []
    for result in results:
        reportResult.append({
            'reference': f'Observation/{result.id}'
        })
    
    report = DiagnosticReport.construct(
        id = reportId,
        meta = reportMeta,
        identifier = reportIdentifier,
        basedOn = reportBasedOn,
        status = reportStatus,
        category = reportCategory,
        code = reportCode,
        subject = reportSubject,
        encounter = reportEncounter,
        effectiveDateTime = reportEffective,
        issued = reportIssued,
        result = reportResult
    )

    results.extend([request, report])

    return results
