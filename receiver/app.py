import connexion 
import json
import time
import requests
import yaml
import logging
import logging.config
import uuid
import datetime
import uvicorn

from pykafka import KafkaClient


EVENT_FILE = "APIdata.json"
MAX_EVENTS = 5



headers = {
        'Content-Type': 'application/json'
    }

# load app config
with open('app_conf.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())

# load log config
with open('log_conf.yml', 'r') as f:
    log_config = yaml.safe_load(f.read(),)
    logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')

###### replacment code for post requests

# client = KafkaClient(hosts=f"{app_config['events']['hostname']}:{app_config['events']['port']}")
# topic = client.topics[str.encode(app_config['events']['topic'])]
# producer = topic.get_sync_producer()
# msg = {'type': 'open_party',
#        'datetime':datetime.datetime.now().isoformat(),
#        'payload': nb}
# msg_str = json.dumps(msg)
# producer.produce(msg_str.encode('utf-8'))

# functions here
def create_open_party(body):
    

    
    nb = body
 
    code_uuid = uuid.uuid4()
    now_time = datetime.datetime.now().isoformat()
    tracecode = f"{str(code_uuid)}_{str(now_time)}"
    
    nb['tc'] = tracecode
    

    
    
    logger.info(f"Received event :create_open_party with tracecode: {tracecode}")
    
    # r = requests.post(app_config["eventstore1"]['url'], json=nb, headers=headers)
    # rcontent = json.loads(r._content.decode('utf-8'))
    
    
    
    client = KafkaClient(hosts=f"{app_config['events']['hostname']}:{app_config['events']['port']}")
    topic = client.topics[str.encode(app_config['events']['topic'])]
    
    
    with topic.get_sync_producer() as producer:
        msg = {'type': 'create_open_party',
            'datetime':datetime.datetime.now().isoformat(),
            'payload': nb}
        msg_str = json.dumps(msg)
        producer.produce(msg_str.encode('utf-8'))
    
    
    # logger.info(f"Returned event :create_open_party with tracecode: {rcontent['tc']} and status: {r.status_code}")
    
    return connexion.NoContent, 201


def join_open_party(body):
    
    nb =  body
    
    code_uuid = uuid.uuid4()
    now_time = datetime.datetime.now().isoformat()
    tracecode = f"{str(code_uuid)}_{now_time}"
    
    nb['tc'] = tracecode   
     
    
    logger.info(f"Received event :join_open_party with tracecode: {tracecode}")
    
    # r = requests.post(app_config["eventstore2"]['url'], json=nb, headers=headers)
    # rcontent = json.loads(r._content.decode('utf-8'))
    
    
    client = KafkaClient(hosts=f"{app_config['events']['hostname']}:{app_config['events']['port']}")
    topic = client.topics[str.encode(app_config['events']['topic'])]
    
    
    
    with topic.get_sync_producer() as producer:
        msg = {'type': 'create_join_request',
            'datetime':datetime.datetime.now().isoformat(),
            'payload': nb}
        msg_str = json.dumps(msg)
        producer.produce(msg_str.encode('utf-8'))

    # logger.info(f"Returned event :join_open_party with tracecode: {rcontent['tc']} and status: {r.status_code}")
    
    return connexion.NoContent, 201


app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("OpenAPI.yaml",
strict_validation=True,
validate_responses=True)



if __name__=="__main__":
    app.run(port=8080)
    