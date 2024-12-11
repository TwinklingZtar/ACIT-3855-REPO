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


import requests
from requests.exceptions import Timeout, ConnectionError



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




RECEIVER_URL = app_config['url']['RECEIVER_URL']
STORAGE_URL = app_config['url']['RECEIVER_URL']
PROCESSING_URL = app_config['url']['PROCESSING_URL']
ANALYZER_URL = app_config['url']['ANALYZER_URL']
TIMEOUT = app_config['timeout'] # Set to 2 seconds in your config file
EVENTFILE = app_config['eventfile']



### ENDPOINTS HERE



def check_services():
    """ Called periodically """
    results = {}
    receiver_status = "Unavailable"
    try:
        response = requests.get(RECEIVER_URL, timeout=TIMEOUT)
        if response.status_code == 200:
            receiver_status = "Healthy"
            logger.info("Receiver is Healthly")
            results["receiver_status"] = receiver_status
        else:
            logger.info("Receiver returning non-200 response")
    except (Timeout, ConnectionError):
        logger.info("Receiver is Not Available")

    storage_status = "Unavailable"
    try:
        response = requests.get(STORAGE_URL, timeout=TIMEOUT)
        if response.status_code == 200:
            storage_json = response.json()
            storage_status = f"Storage has {storage_json['num_cop']} create events and {storage_json['num_jop']} join events"
            logger.info("Storage is Healthy")
            results['storage_status'] = storage_status
        else:
            logger.info("Storage returning non-200 response")
    except (Timeout, ConnectionError):
        logger.info("Storage is Not Available")
        
    try:
        response = requests.get(ANALYZER_URL, timeout=TIMEOUT)
        if response.status_code == 200:
            storage_json = response.json()
            analyzer_status = f"Analyzer has {storage_json['num_cop']} create events and {storage_json['num_jop']} join events"
            logger.info("Storage is Healthy")
            results['analyzer_status'] = analyzer_status
        else:
            logger.info("Storage returning non-200 response")
    except (Timeout, ConnectionError):
        logger.info("Storage is Not Available")
        
    with open(EVENTFILE, 'w') as file:
        json.dump(results)
        



def get_health():
    with open(EVENTFILE,'r')as file:
        data = json.load(file)
    return data, 200
        
def init_scheduler():
    
    sched = BackgroundScheduler(deamon=True)
    sched.add_job(check_services, 'interval', seconds = app_config['timer'])
    sched.start()
    pass



app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("OpenAPI.yaml",
strict_validation=True,
validate_responses=True)



if __name__=="__main__":
    init_scheduler()
    app.run(host="0.0.0.0",port=8130)