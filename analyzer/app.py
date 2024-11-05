import connexion
import json
import time
import datetime
import uvicorn

import yaml
import logging
import logging.config

from pykafka import KafkaClient

EVENT_FILE = "APIdata.json"

with open('app_conf.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())
    

headers = {
        'Content-Type': 'application/json'
    }

# load log config
with open('log_conf.yml', 'r') as f:
    log_config = yaml.safe_load(f.read(),)
    logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')






def get_open_parties(index):
    hostname = "%s:%d" % (app_config['events']['hostname'], app_config['events']['port'])
    client = KafkaClient(hosts = hostname)
    topic = client.topics[str.encode(app_config['events']['topic'])]
    
    
    
    consumer = topic.get_simple_consumer(reset_offset_on_start=True, consumer_timeout_ms=1000)
    
    
    logger.info(f"retrieving open_party_card at index: {index}")
    count = 0
    try:
        for msg in consumer:
            msg_str = msg.value.decode('utf-8')
            logger.debug(f"THIS IS WHAT YOU WANT: {msg_str}")
            msg = json.loads(msg_str)
            logger.debug(f"checking msg type: {msg['type']}")
            if msg['type'] == 'create_open_party':
                logger.debug(f"type gate passed | checking index {index}")
                if count == index:
                    logger.debug('index == count gate passed')
                    body = msg['payload']
                    logger.debug(f"checking body: {body}")
                    event = {'tc':body['tc'],
                             'campaign':body['campaign'],
                             'game_frequency':body['game_frequency'],
                             'game_location':body['game_location'],
                             'game_master_id':body['game_master_id'],
                             'game_time':body['game_time'],
                             'max_players':body['max_players'],
                             'open_party_id':body['open_party_id']}
                    logger.debug(f"checking event {event}")
                    return event, 200
                count += 1
        

        
    except:
        logger.error("No more messages found")
    logger.error("Could not find open_party_card at index %d" % index)
    return { "message": "Not Found"}, 404



def get_join_requests(index):
    hostname = "%s:%d" % (app_config['events']['hostname'], app_config['events']['port'])
    client = KafkaClient(hosts = hostname)
    topic = client.topics[str.encode(app_config['events']['topic'])]
    
    
    
    consumer = topic.get_simple_consumer(reset_offset_on_start=True, consumer_timeout_ms=1000)
    
    
    logger.info(f"retrieving join_request at index: {index}")
    count = 0
    try:
        for msg in consumer:
            msg_str = msg.value.decode('utf-8')
            msg = json.loads(msg_str)
            if msg['type'] == 'create_join_request':
                if count == index:
                    body = msg['payload']
                    event = {'tc':body['tc'],
                            'open_party_id':body['open_party_id'],
                            'player_id':body['player_id'],
                            'player_rating':body['player_rating'],
                            'alignment':body['alignment'],
                            'background':body['background'],
                            'class':body['class'],
                            'level':body['level'],
                            'species':body['species']
                            }
                    return event, 200
                count += 1
        

        
    except:
        logger.error("No more messages found")
    logger.error("Could not find player_join_request at index %d" % index)
    return { "message": "Not Found"}, 404 


def get_stats():
    hostname = "%s:%d" % (app_config['events']['hostname'], app_config['events']['port'])
    client = KafkaClient(hosts = hostname)
    topic = client.topics[str.encode(app_config['events']['topic'])]
    
    
    
    consumer = topic.get_simple_consumer(reset_offset_on_start=True, consumer_timeout_ms=1000)
    
    
    logger.info(f"retrieving total events")
    
    num_cop = 0
    num_jop = 0
    
    for msg in consumer:
        msg_str = msg.value.decode('utf-8')
        msg = json.loads(msg_str)
        if msg['type'] == 'create_open_party':
            num_cop += 1
        if msg['type'] == 'create_join_request':
            num_jop += 1
    return {'num_cop':num_cop, 'num_jop': num_jop} , 200
    






app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("OpenAPI.yaml",
strict_validation=True,
validate_responses=True)

if __name__=="__main__":
    app.run(host="0.0.0.0",port=8110)


