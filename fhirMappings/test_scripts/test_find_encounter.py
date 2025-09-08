# run with: python -m test_scripts.test_find_encounter  

import json
from datetime import datetime

from app.mappings.helper_functions import process_encounter_response

search_res = None

with open('/Users/jesse/Code/MIKI-Proj/consumer/test_scripts/test_files/example_enc_search_bundle.json') as file:
    search_res = json.load(file)

# Test 1
# "start": "2019-12-24T21:38:00+01:00",
# "end":   "2020-01-04T11:00:00+01:00"

date_created = datetime.fromisoformat("2020-01-02T11:00:00+01:00")

encounter_ref = process_encounter_response(search_res, date_created)
assert(encounter_ref == 'PV-c4b08990a2fe8eba8bb559ad46a5e5738cd7599286b3bcf611cfdfe5')
print(encounter_ref)


# Test 2
date_created = datetime.fromisoformat("2024-01-02T11:00:00+01:00")

encounter_ref = process_encounter_response(search_res, date_created)
assert(encounter_ref == None)


# Test 3

# "start": "2020-04-15T09:01:00+02:00",
# "end": "2020-04-17T16:00:00+02:00"
date_created = datetime.fromisoformat("2020-04-16T09:01:00+02:00")

encounter_ref = process_encounter_response(search_res, date_created)
assert(encounter_ref == None)


# test no entry
with open('/Users/jesse/Code/MIKI-Proj/consumer/test_scripts/test_files/example_enc_search_bundle_2.json') as file:
    search_res = json.load(file)

date_created = datetime.fromisoformat("2020-04-16T09:01:00+02:00")

encounter_ref = process_encounter_response(search_res, date_created)
assert(encounter_ref == None)
