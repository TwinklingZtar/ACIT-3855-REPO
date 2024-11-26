import connexion
import json
import time
import uvicorn
from apscheduler.schedulers.background import BackgroundScheduler
import requests

# from db import make_session
# from models import Base, OpenParty, PartyJoinRequest
# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker
# from sqlalchemy import Column, Integer, String, DateTime
import datetime
import sqlalchemy
import mysql.connector
import logging
import logging.config
import yaml
import uuid
import pymysql
import os




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





# # load app config
# with open('app_conf.yml', 'r') as f:
#     app_config = yaml.safe_load(f.read())


EVENT_FILE = "APIdata.json"


# DB_ENGINE = create_engine(f"mysql+pymysql://{app_config['datastore']['user']}:{app_config['datastore']['password']}@{app_config['datastore']['hostname']}:{app_config['datastore']['port']}/{app_config['datastore']['db']}")



headers = {
        'Content-Type': 'application/json'
    }


# # load log config
# with open('log_conf.yml', 'r') as f:
#     log_config = yaml.safe_load(f.read(),)
#     logging.config.dictConfig(log_config)
# logger = logging.getLogger('basicLogger')



# def get_open_party(start_timestamp, end_timestamp):
#     #do db stuff
#     sql_query = sqlalchemy.text(f"SELECT * FROM open_party WHERE date_created >= {str(start_timestamp)} AND date_created <= {str(end_timestamp)} ")
    
    
#     with DB_ENGINE.connect() as connection:
#         connection.execute(sql_query)
    
#     return
    





def populate_stats():
    logger.info('periodic processing start')
    try:
        with open(app_config['datastore']['filename'], 'r') as file:
            data = json.load(file)
            
    except FileNotFoundError:
        logger.warning(f"File {app_config['datastore']['filename']} not found. Creating an empty file.")
        
        # If the file doesn't exist, create an empty JSON file
        with open(app_config['datastore']['filename'], 'w') as file:
            json.dump({ 
                'num_open_parties' : 0,
                'num_join_requests': 0,
                'avg_party_size' :0,
                'avg_player_rating':0,
                'last_updated': '2024-10-06 02:52:31'
            }, file)  
            data = {
                'num_open_parties' : 0,
                'num_join_requests': 0,
                'avg_party_size' :0,
                'avg_player_rating':0,
                'last_updated': '2024-10-06 02:52:31'
            }
            
            
    time_now = datetime.datetime.now().isoformat()  # Use ISO format for consistency
    params = {'start_timestamp': data['last_updated'], 'end_timestamp': time_now}
    
    try:
        copR = requests.get(f"{app_config['eventstore']['url']}/party-list/create-open-party", headers=headers, params=params)
        copR.raise_for_status()  # Raises an error for HTTP errors
        print(f"Response for create-open-party: {copR.text}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
    
    try:
        jopR = requests.get(f"{app_config['eventstore']['url']}/party-list/join-open-party", headers=headers, params=params)
        jopR.raise_for_status()  # Raises an error for HTTP errors
        print(f"Response for join-open-party: {jopR.text}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
        
    
    
    print(data)
    
    current_avg_rating = data["num_join_requests"] * data['avg_player_rating']
    current_avg_party_size = data['num_open_parties'] * data['avg_party_size']
    
    
    copR_content = json.loads(copR.content)
    data['num_open_parties'] += len(copR_content)

    jopR_content = json.loads(jopR.text)
    data['num_join_requests'] += len(jopR_content)
    
    logger.info(f" recieved {len(copR_content)} new events from /party-list/create-open-party | recieved {len(jopR_content)} new events from /party-list/join-open-party | totaling {len(jopR_content) + len(copR_content)} new events")
    
    for item in copR_content:
        current_avg_party_size += item['max_players']

    data['avg_party_size'] = current_avg_party_size / data['num_open_parties']
    
    
    
    for item in jopR_content:
        current_avg_rating += item["player_rating"]
    data['avg_player_rating'] = current_avg_rating / data['num_join_requests']

        


    
    data["last_updated"] = time_now
    
    
    with open(app_config['datastore']['filename'], 'w') as file:
        json.dump(data, file)
    
    
    
    logger.debug(f"Updated Data: {data}")
    logger.info("periodic process is done")
    
    pass

def init_scheduler():
    
    sched = BackgroundScheduler(deamon=True)
    sched.add_job(populate_stats, 'interval', seconds = app_config['scheduler']['period_sec'])
    sched.start()
    pass

def getstats():
    """Fetch stats from log file"""
    logger.info("getstats request has started")
    try:
        with open(app_config['datastore']['filename'], 'r') as file:
                data = json.load(file)
    except FileNotFoundError:
        logger.error("statistics do not exist")
        return 404
     
    logger.debug(f"{data}")
    logger.info("request completed")

    # If you want to return the results, you can return them here
    
    return data, 200















app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("OpenAPI.yaml",
strict_validation=True,
validate_responses=True)



if __name__=="__main__":
    init_scheduler()
    app.run(host="0.0.0.0",port=8100)