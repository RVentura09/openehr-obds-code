import os
import requests
import jsonpath

from datetime import datetime

def has_consent(patientId):
    fhir_server_address = os.environ['FHIR_SERVER_ADDRESS']
    response = requests.get(f'http://{fhir_server_address}/fhir/Consent?patient={patientId}')
    
    if response.json()['total'] != 1:
        return False
    else:
        return '2.16.840.1.113883.3.1937.777.24.5.3.6' in jsonpath.findall('$.entry[0].resource.provision.provision[0].code.[*].coding[0].code', response.json())
    
    
def get_encounter(patientId, search_datetime):
    fhir_server_address = os.environ['FHIR_SERVER_ADDRESS']
    response = requests.get(f'http://{fhir_server_address}/fhir/Encounter?_profile:below=https://www.medizininformatik-initiative.de/fhir/core/modul-fall/StructureDefinition/KontaktGesundheitseinrichtung&type=http://fhir.de/CodeSystem/Kontaktebene|einrichtungskontakt&class=IMP&subject=Patient/{patientId}')
    
    return process_encounter_response(response.json(), search_datetime)
    

def process_encounter_response(json_response, search_datetime: datetime):
    if 'entry' in json_response:
        entries = json_response['entry']
    else:
        return None
    
    # sort from newest to oldest
    entries = sorted(entries, key=lambda item: datetime.fromisoformat(item['resource']['period']['start']), reverse=True)

    for (idx, entry) in enumerate(entries):
        start_date = None 
        end_date = None
        try:
            start_date = datetime.fromisoformat(entry['resource']['period']['start'])
        except:
            continue
        try:
            end_date = datetime.fromisoformat(entry['resource']['period']['end'])
        except:
            end_date = None

        # if end date is None and idx==0 -> newest encounter (still acitve)
        if start_date != None and end_date == None and idx == 0:
            if search_datetime > start_date:
                return entry['resource']['id']
        
        elif start_date != None and end_date != None:
            if search_datetime > start_date and search_datetime < end_date:
                return entry['resource']['id']
    
    return None