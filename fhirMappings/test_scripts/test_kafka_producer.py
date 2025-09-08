from logging import log
from kafka import KafkaProducer
from kafka.errors import KafkaError

def produce_test_vars(what_to_test):
    match what_to_test:
        case 'atemfrequenz':
            return ('test_files/example_atemfreq.json', 'medicsh.openehr.json.kds-icu-atemfrequenz')
        case 'groesse':
            return ('test_files/example_groesse.json', 'medicsh.openehr.json.kds-icu-koerpergroesse')
        case 'gewicht':
            return ('test_files/example_gewicht.json', 'medicsh.openehr.json.kds-icu-koerpergewicht')
        case 'herzfrequenz':
            return ('test_files/example_herzfrequenz.json', 'medicsh.openehr.json.kds-icu-herzfrequenz')
        case 'blutdruck':
            return ('test_files/example_blutdruck.json', 'input.topic')
        case 'spo2':
            return ('test_files/example_spo2.json', 'medicsh.openehr.json.kds-icu-spo2')
        case 'temp1':
            return ('test_files/example_temp1.json', 'input.topic')
        case 'temp2':
            return ('test_files/example_temp2.json', 'input.topic')
        case 'temp3':
            return ('test_files/example_temp3.json', 'input.topic')
        case 'temp4':
            return ('test_files/example_temp4.json', 'input.topic')
        case 'temp5':
            return ('test_files/example_temp5.json', 'input.topic')
        case 'test_pat':
            return ('test_files/example_patient.json', 'input.topic')
        case 'provoke_error':
            return ('test_files/provoke_error.json', 'input.topic')
        case 'no_json':
            return ('test_files/provoke_error_no_json.txt', 'input.topic')
        case _: 
            raise('No valid input to produce test vars')




producer = KafkaProducer(bootstrap_servers=['localhost:9092'])

(path, topic) = produce_test_vars('temp5')

print('Sending message from file: {}'.format(path))

with open(path) as file:
    example_msg = file.read()

future = producer.send(topic, bytes(example_msg, 'utf-8'))

try:
    record_metadata = future.get(timeout=10)
except KafkaError:
    log.exception()
    pass

print('Topic: {} '.format(record_metadata.topic))
print('Partition: {} '.format(record_metadata.partition))
print('Offset: {} '.format(record_metadata.offset))
