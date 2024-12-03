import connexion
import json
import time
import uvicorn

# from db import make_session
# from models import Base, OpenParty, PartyJoinRequest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, String, DateTime
import datetime
import sqlalchemy
import mysql.connector
import logging
import logging.config
import yaml
import uuid
import pymysql
import os


from pykafka import KafkaClient
# from pykafka import OffsetType
from threading import Thread



if "TARGET_ENV" in os.environ and os.environ["TARGET_ENV"] == "test":
    print("In Test Environment")
    app_conf_file = "/config/app_conf.yml"
    log_conf_file = "/config/log_conf.yml"
else:
    print("In Dev Environment")
    app_conf_file = "app_conf.yml"
    log_conf_file = "log_conf.yml"
    
with open(app_conf_file, 'r') as f:
    app_config = yaml.safe_load(f.read())
    
    # External Logging Configuration
with open(log_conf_file, 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)
    
logger = logging.getLogger('basicLogger')
logger.info("App Conf File: %s" % app_conf_file)
logger.info("Log Conf File: %s" % log_conf_file)



headers = {
        'Content-Type': 'application/json'
    }


logger.info(f"create_open_party game_time threshold: {app_config['thresholds']['createOpen']}")
logger.info(f"create_join_request character level threshold: {app_config['thresholds']['joinOpen']}")





def get_anomalies(anomaly_type):
    datastore_path = f"/data/{app_config['datastore']}"
    
    try:
        with open(datastore_path, 'r') as file:
            data_list = json.load(file)  # Load existing data from the file
    except (FileNotFoundError, json.JSONDecodeError):
        data_list = []
        json.dump(data_list, datastore_path)
        
        
    if anomaly_type == "createOpen":
        newlist = []
        for item in data_list:
            if item['event_type'] == "create_open_party":
                newlist.append(item)
        if len(newlist) == 0:
            return { "message": "no createOpen anomalies"},404
        newlist.reverse()
        return newlist, 200
    if anomaly_type == "joinOpen":
        newlist = []
        for item in data_list:
            if item['event_type'] == "create_join_request":
                newlist.append(item)
        if len(newlist) == 0:
            return  { "message":  "no joinOpen anomalies"}, 404
        newlist.reverse()
        return  newlist, 200
    return { "message":  f"{anomaly_type} is not a valid anomaly type"}, 400






def process_messages():
    hostname = "%s:%d" % (app_config['events']['hostname'], app_config['events']['port'])
    client = KafkaClient(hosts=hostname)
    topic = client.topics[str.encode(app_config['events']['topic'])]
    consumer = topic.get_simple_consumer(consumer_group=b'anomaly_group', reset_offset_on_start=False, auto_commit_enable=True)
    
    
    for msg in consumer:
        msg_str = msg.value.decode('utf-8')
        msg = json.loads(msg_str)
        logger.info("Message: %s" % msg)
        
        body = msg["payload"]
        
        logger.info(body)
        
        if msg["type"] == "create_open_party" :
            if int(body["game_time"]) > int(app_config["thresholds"]["createOpen"]):
                datastore_path = f"/data/{app_config['datastore']}"

                try:
                    with open(datastore_path, 'r') as file:
                        data_list = json.load(file)  # Load existing data from the file
                except (FileNotFoundError, json.JSONDecodeError):
                    data_list = []
                logger.info(f"game_time too high anomaly added to datastore with the trace id: {body['tc']}")
                data_list.append({
                    "event_id" : str(uuid.uuid4()),
                    "trace_id" : body['tc'],
                    "event_type" : "create_open_party",
                    "anomaly_type" : "out-of-24-hour-clock",
                    "description" : f"game time value is {body['game_time']} which is above the max of {app_config['thresholds']['createOpen']}",
                    "timestamp" : datetime.datetime.now().isoformat()
                    
                })
                consumer.commit_offsets()
                
                with open(datastore_path, 'w') as file:
                    json.dump(data_list, file, indent=4)
                        
            
        if msg["type"] == "create_join_request":
            if int(body["level"]) > int(app_config["thresholds"]["joinOpen"]):
                datastore_path = f"/data/{app_config['datastore']}"

                try:
                    with open(datastore_path, 'r') as file:
                        data_list = json.load(file)  # Load existing data from the file
                except (FileNotFoundError, json.JSONDecodeError):
                    data_list = []
                logger.info(f"char level too high anomaly added to datastore with the trace id: {body['tc']}")
                data_list.append({
                    "event_id" : str(uuid.uuid4()),
                    "trace_id" : body["tc"],
                    "event_type" : "create_join_request",
                    "anomaly_type" : "too high",
                    "description" : f"character level is {body['level']} which is above the max of {app_config['thresholds']['joinOpen']}",
                    "timestamp" : datetime.datetime.now().isoformat()
                    
                })
                consumer.commit_offsets()
                
                with open(datastore_path, 'w') as file:
                    json.dump(data_list, file, indent=4)
    consumer.commit_offsets()
        
        
        



app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("OpenAPI.yaml",
strict_validation=True,
validate_responses=True)




if __name__=="__main__":
    t1 = Thread(target=process_messages)
    t1.setDaemon(True)
    t1.start()
    app.run(host="0.0.0.0",port=8120)
    