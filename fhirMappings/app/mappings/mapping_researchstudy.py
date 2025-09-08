'''
This file is inteded to host the mapping it self. The method map_ressource(..) ist called
in the kafka_consumer.py file within the start_consumer() method.
'''

import json
from fhir.resources.R4B.evidencevariable import EvidenceVariable
from fhir.resources.R4B.researchstudy import ResearchStudy

def map_status(status):
    match status:
        case 'abgebrochen':
            return 'withdrawn'
        case 'in close out':
            return 'closed-to-accrual-and-intervention'
        case 'on Treatment / Follow-Up':
            return 'closed-to-accrual'
        case 'rekrutierend':
            return 'active'
        case 'Studie beendet':
            return 'completed'
        case 'vorübergehender Rekrutierungsstopp':
            return 'temporarily-closed-to-accrual'
    return None

def map_ressource(input_json):
    """
        Args:
            input_json (json): A json object
        Returns:
            str:    A str that must be valid json. Since we are mapping with fhir.resources 
                    this should be ensured id <ressource>.json() ist used for returning.
    """

    study = []

    extensions = []

    studyId = input_json['Studiencode']

    studyMeta = {
        'profile': [
            'https://www.medizininformatik-initiative.de/fhir/modul-studie/StructureDefinition/mii-pr-studie-studie|2025.0.0'
        ]
    }

    studyTitle = input_json['Studienname']
    if studyTitle is None:
        return []
    if input_json['Studientitel'] is not None:
        extensions.append({
            'extension':  [
                {
                    'url': 'value',
                    'valueString': input_json['Studienname']
                },
                {
                    'url': 'type',
                    'valueCodeableConcept': {
                        'text': 'Öffentlicher Titel'
                    }
                }
            ],
            'url': 'http://hl7.org/fhir/5.0/StructureDefinition/extension-ResearchStudy.label'
        })
        extensions.append({
            'extension':  [
                {
                    'url': 'value',
                    'valueString': input_json['Studienname']
                },
                {
                    'url': 'type',
                    'valueCodeableConcept': {
                        'coding':  [
                            {
                                'code': 'scientific',
                                'system': 'http://hl7.org/fhir/title-type'
                            }
                        ]
                    }
                }
            ],
            'url': 'http://hl7.org/fhir/5.0/StructureDefinition/extension-ResearchStudy.label'
        })

    studyStatus = map_status(input_json['Status'])

    if input_json['Studienakronym'] is not None:
        extensions.append({
            'url': 'https://www.medizininformatik-initiative.de/fhir/modul-studie/StructureDefinition/mii-ex-studie-akronym',
            'valueString': input_json['Studienakronym']
        },)

    studyIdentifier = [
        {
            'system': 'https://cnxx.codex.medicsh.de/centraxx/Studie',
            'value': input_json['Studiencode']
        }
    ]

    if input_json['DRKS_ID_der_Studie'] is not None:
        studyIdentifier.append({
            'system': 'https://www.medizininformatik-initiative.de/fhir/modul-studie/sid/drks',
            'value': input_json['DRKS_ID_der_Studie']
        })

    if input_json['NCT_ID_der_Studie'] is not None:
        studyIdentifier.append({
            'system': 'https://clinicaltrials.gov',
            'value': input_json['NCT_ID_der_Studie']
        })

    if input_json['EudraCT_ID_der_Studie'] is not None:
        studyIdentifier.append({
            'system': 'https://www.medizininformatik-initiative.de/fhir/modul-studie/sid/eudract',
            'value': input_json['EudraCT_ID_der_Studie']
        })

    category = [
        {
            'coding': {
                'code': input_json['Kategorie'],
                'system': 'https://cnxx.codex.medicsh.de/centraxx/Kategorie'
            }

        }
    ]

    studyCondition = None

    if input_json['ICD_Code'] is not None:
        studyCondition = [
            {
                'coding': [
                    {
                        'system': 'http://fhir.de/CodeSystem/bfarm/icd-10-gm',
                        'code': input_json['ICD_Code'],
                        'display': input_json['ICD_Titel']
                    }
                ]
            }
        ]

    characteristic = []

    if input_json['Einschlusskriterium_Geschlecht'] is not None:
        if input_json['Einschlusskriterium_Geschlecht'] == 'Beide, männlich und weiblich':
            input_json['Einschlusskriterium_Geschlecht'] = 'Alle'
        characteristic.append({
            'definitionCodeableConcept': {
                'text': 'Alle'
            },
            'description': 'Geschlecht',
            'exclude': False
        })

    if input_json['Einschlusskriterium_Mindestalter'] is not None:
        input_json['Einschlusskriterium_Mindestalter'] = f'{study["Einschlusskriterium_Mindestalter"]} Jahre'
        if input_json['Einschlusskriterium_Mindestalter'] == '0 Jahre':
            input_json['Einschlusskriterium_Mindestalter'] = 'kein Mindestalter'
        characteristic.append({
            'definitionCodeableConcept': {
                'text': input_json['Einschlusskriterium_Mindestalter']
            },
            'description': 'Mindestalter',
            'exclude': False
        })

    if input_json['Einschlusskriterium_Höchstalter'] is not None and input_json['Einschlusskriterium_Höchstalter'] != '0':
        characteristic.append({
            'definitionCodeableConcept': {
                'text': f'{study["Einschlusskriterium_Höchstalter"]} Jahre'
            },
            'description': 'Höchstalter',
            'exclude': False
        })

    if input_json['Weitere_Einschlusskriterien'] is not None:
        characteristic.append({
            'definitionCodeableConcept': {
                'text': input_json['Weitere_Einschlusskriterien'].replace('', ' - ').replace('', ' - ')
            },
            'description': 'weitere Einschlusskriterien',
            'exclude': False
        })

    if input_json['Weitere_Ausschlusskriterien'] is not None:
        characteristic.append({
            'definitionCodeableConcept': {
                'text': input_json['Weitere_Ausschlusskriterien'].replace('\n', '\r\n').replace('', ' - ').replace('', ' - ')
            },
            'description': 'Ausschlusskriterien',
            'exclude': True
        })

    if len(characteristic) > 0:

        evidenceMeta = {
            'profile': [
                'https://www.medizininformatik-initiative.de/fhir/modul-studie/StructureDefinition/mii-pr-studie-ein-auschluss-kriterium|2025.0.0'
            ]
        }

        ev = EvidenceVariable.construct(
            id = f'EV-{studyId}',
            meta = evidenceMeta,
            characteristic = characteristic,
            status = 'active'
        )

        study.append(ev)

        extensions.append({
            'url': 'https://www.medizininformatik-initiative.de/fhir/modul-studie/StructureDefinition/mii-ex-studie-eligibility',
            'valueReference': {
                'reference': f'EvidenceVariable/EV-{studyId}'
            }
        })

    fhirStudy = ResearchStudy.construct(
        id = studyId,
        meta = studyMeta,
        identifier = studyIdentifier,
        title = studyTitle,
        status = studyStatus,
        condition = studyCondition,
        extension = extensions
    )

    study.append(fhirStudy)

    return study
