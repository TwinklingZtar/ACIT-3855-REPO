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
import os

from pykafka import KafkaClient




headers = {
        'Content-Type': 'application/json'
    }

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





# client = KafkaClient(hosts=f"{app_config['events']['hostname']}:{app_config['events']['port']}")
# topic = client.topics[str.encode(app_config['events']['topic'])]
# producer = topic.get_sync_producer()





### ENDPOINTS HERE


app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("OpenAPI.yaml",
strict_validation=True,
validate_responses=True)



if __name__=="__main__":
    app.run(host="0.0.0.0",port=8130)