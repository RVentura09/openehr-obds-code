import os
import json
import logging
import sys
from datetime import datetime
from time import sleep

from dotenv import load_dotenv
from kafka.consumer import KafkaConsumer
from kafka.producer import KafkaProducer

import http.client
import importlib

# only used for local testing.
load_dotenv('../.env')

mapping_file = os.environ['MAPPING_TO_USE']
if mapping_file.endswith('.py'):
   mapping_file = mapping_file[:-3]
mapping = importlib.import_module('mappings.' + mapping_file)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)-8s %(name)s ::: %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
logging.getLogger('kafka').setLevel(logging.WARNING)



def get_modus_props():
    in_topic = os.environ['INCOMING_TOPIC_NAME']
    consumer_group = os.environ['CONSUMER_GROUP']
    bootstrap_servers = os.environ['BOOTSTRAP_SERVER']
    fhir_server_address = os.environ['FHIR_SERVER_ADDRESS']
    return in_topic, consumer_group, bootstrap_servers, fhir_server_address
   


def send_error(message, bootstrap_servers, error):
    """
    This method is invoked if the incomming message could not be mapped. The message is then bundled with 
    a timestamp and the error and fowarded to the specefied error-topic.

    Problem: The sending to the downstream-topic could potentially also fail. But in that case the Consumer
    seems to crash anyway since there is no longer a broker available. Since the commit would happen after 
    this method the commit can not happen and so a message loss should not be possible.
    """
    producer = KafkaProducer(
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        bootstrap_servers=bootstrap_servers)

    res = dict()
    res['dateCreated'] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    res['message'] = message.value.decode("utf-8")
    res['error'] = str(error)
    
    producer.send(topic=os.environ['ERROR_TOPIC_NAME'], value=res)
    producer.flush()
    logger.warning(f"Message was send to topic '{os.environ['ERROR_TOPIC_NAME']}'")



def handle_send_failure(consumer, backoff_time):
    """
    This method is invoked whenever a downstream server has a problem. Messages are NOT commited then
    and the kafka offset is resetted to the last successful message. The service then sleeps for the
    'backoff_time'. After this intervall a retry is run with the same offset as before.
    """
    partition = consumer.assignment().pop()
    last_commit = consumer.committed(partition)
    consumer.seek(partition, last_commit)
    
    logger.warning(f'Backing off for {backoff_time} sek')    
    sleep(backoff_time)
    


def get_backoff_time(curr_backoff_time):
    """
    Method implements the back off stradegy: Doubles the time in each iteration until a max is hit 
    ( 3600 sek -> 1h )
    """
    if curr_backoff_time < 3600:
        return curr_backoff_time * 2
    else:
        return curr_backoff_time



def start_consumer():
   
    backoff_fhir_server_failure_sek = 5

    in_topic, consumer_group, bootstrap_servers, fhir_server_address = get_modus_props()

    try:
        consumer = KafkaConsumer(
            bootstrap_servers=bootstrap_servers,
            auto_offset_reset="latest",
            enable_auto_commit=False,
            group_id=consumer_group,
            max_poll_records=10,
            max_poll_interval_ms=60 * 1000
        )
        logger.info(f'Successfully created consumer for topic "{in_topic}"')

    except Exception as error:
        logger.error(f'Consumer could not be initialzed.\n{error}')
        exit()

    consumer.subscribe([in_topic])

    for message in consumer:
        try:
            payload = message.value
            # Here the mapping function is called 
            try:
                payload = payload.decode("utf-8")
                payload = json.loads(payload)
            except:
                raise Exception(f'Message from Kafka could not be parsed as JSON')
            
            mapped_resources = mapping.map_ressource(payload)

            if len(mapped_resources) == 0:
                logger.info("No resource(s) mapped. Commiting to Kafka...")
                consumer.commit()
            else:    
                logger.info("Successfully mapped resource(s).")
        except Exception as error:
            logger.error(f'Message could not be mapped ::: Error-Message ::: {error}')
            # the incomming message has a problem -> send message to error queue and commit to make way to process the next messages 
            send_error(message, bootstrap_servers, error)
            consumer.commit()
            # skip the rest since we don't have a valid mapped_resource
            continue
        try:
            for mapped_resource in mapped_resources:
                # Send to FHIR server
                conn = http.client.HTTPConnection(fhir_server_address)
                conn.request("PUT",f'/fhir/{mapped_resource.resource_type}/{mapped_resource.id}', headers={'Content-type': 'application/json'}, body=mapped_resource.json())
                response = conn.getresponse()

                if response.status in [200, 201]:
                    # only commit if server answered with 200 or 201
                    consumer.commit()
                    logger.info("Successfully send resouce to fhir server.")
                    backoff_fhir_server_failure_sek = 5
                elif response.status in [400, 404]:
                    error_msg = f'{response.status} - Server could not process message'
                    logger.error(error_msg)
                    # if 400/404 the message is the problem -> send to error queue, commit and move on.
                    send_error(message, bootstrap_servers, error_msg)
                    consumer.commit()
                else:
                    # otherwise potentially something wrong with the server -> trigger exception to go into error handling
                    raise Exception(f'Message could not be processed by the Server {response.status}')
        
        except Exception as error:
            # otherwise don't commit -> stop processing until server problem is resolved
            logger.error(f'Error while sending ressouce to FHIR server.\n{error}')
            backoff_time = get_backoff_time(backoff_fhir_server_failure_sek)
            handle_send_failure(consumer, backoff_time)
            backoff_fhir_server_failure_sek = backoff_time 
            

if __name__ == "__main__":
    start_consumer()
