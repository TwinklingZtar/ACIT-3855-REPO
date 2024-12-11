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


EVENT_FILE = "APIdata.json"
MAX_EVENTS = 5

DB_ENGINE = create_engine(
    f"mysql+pymysql://{app_config['datastore']['user']}:{app_config['datastore']['password']}@{app_config['datastore']['hostname']}:{app_config['datastore']['port']}/{app_config['datastore']['db']}",
    pool_size=10,                # Maximum number of connections in the pool
    max_overflow=5,              # Allow 5 more connections above pool_size
    pool_recycle=300,            # Recycle connections after 300 seconds
    pool_pre_ping=True           # Check if connections are alive before using
)


headers = {
        'Content-Type': 'application/json'
    }




logger.info(f"hostname: {app_config['datastore']['hostname']} | connection port {app_config['datastore']['port']}")



def get_event_stats():
    connection = mysql.connector.connect(
        user=app_config['datastore']['user'],
        password=app_config['datastore']['password'],
        host=app_config['datastore']['hostname'],
        port=app_config['datastore']['port'],
        database=app_config['datastore']['db']
    )
    
    stat_data = {"num_cop": 0, "num_jop": 0}
    
    
    cursor = connection.cursor(dictionary=True)
    
    sqlquery1 = "SELECT count(tc) FROM open_party"
    
    cursor.execute(sqlquery1)
    results = cursor.fetchall()
    logger.info("RESULTS HERE" + f"{results}")
    
 
    stat_data['num_cop'] = results[0]
    
    sqlquery2 = "SELECT count(tc) FROM open_party"
    
    cursor.execute(sqlquery2)
    results = cursor.fetchall()
    logger.info("RESULTS HERE" + f"{results}")
    
  
    stat_data['num_jop'] = results[0]
    
    logger.info("stats before" + stat_data)
    stat_data['num_cop'] = stat_data['num_cop']['count(tc)']
    stat_data['num_jop'] = stat_data['num_jop']['count(tc)']
    
    
    print(stat_data)
    logger.info(stat_data)
    
    
    return stat_data, 200


def get_open_parties(start_timestamp, end_timestamp):
    """Fetch open party records between the start and end timestamps using mysql.connector"""

    connection = mysql.connector.connect(
        user=app_config['datastore']['user'],
        password=app_config['datastore']['password'],
        host=app_config['datastore']['hostname'],
        port=app_config['datastore']['port'],
        database=app_config['datastore']['db']
    )

    cursor = connection.cursor(dictionary=True) 

    sql_query = """
        SELECT * FROM open_party
        WHERE date_created >= %s AND date_created < %s
    """

    # Execute the query with the provided timestamps
    cursor.execute(sql_query, (start_timestamp, end_timestamp))

    # Fetch the results
    results = cursor.fetchall()
    
    for result in results:
            if not all(key in result for key in ['tc', 'campaign', 'game_frequency', 'game_location', 'game_master_id', 'game_time', 'max_players', 'open_party_id']):
                logger.error("Result missing required properties: %s", result)
                return {'message': 'Missing required properties in results'}, 500

    # Close the cursor and connection
    cursor.close()
    connection.close()

    # If you want to return the results, you can return them here
    return results, 200






def get_party_join_request(start_timestamp, end_timestamp):
    """Fetch open party records between the start and end timestamps using mysql.connector"""

    connection = mysql.connector.connect(
        user=app_config['datastore']['user'],
        password=app_config['datastore']['password'],
        host=app_config['datastore']['hostname'],
        port=app_config['datastore']['port'],
        database=app_config['datastore']['db']
    )

    cursor = connection.cursor(dictionary=True) 

    sql_query = """
        SELECT * FROM player_join_request
        WHERE date_created >= %s AND date_created < %s
    """

    # Execute the query with the provided timestamps
    cursor.execute(sql_query, (start_timestamp, end_timestamp))


    

    # Fetch the results
    results = cursor.fetchall()



    # Close the cursor and connection
    cursor.close()
    connection.close()

    # If you want to return the results, you can return them here
    return results, 200



def process_messages():
    hostname = "%s:%d" % (app_config['events']['hostname'], app_config['events']['port'])
    client = KafkaClient(hosts=hostname)
    topic = client.topics[str.encode(app_config['events']['topic'])]
    consumer = topic.get_simple_consumer(consumer_group=b'event_group', reset_offset_on_start=False)
    
    
    for msg in consumer:
        msg_str = msg.value.decode('utf-8')
        msg = json.loads(msg_str)
        logger.info("Message: %s" % msg)
        
        body = msg["payload"]
        
        if msg["type"] == "create_open_party" :
            logger.debug(f"Received event :create_open_party with tracecode: {body['tc']}")
            
            body['date_created'] = datetime.datetime.now().isoformat()

            sql_query = sqlalchemy.text(f"INSERT INTO open_party (open_party_id, game_master_id, campaign, game_location, game_frequency, max_players, game_time, date_created, tc) VALUES('{body['open_party_id']}', '{body['game_master_id']}', '{body['campaign']}', '{body['game_location']}','{body['game_frequency']}',  {body['max_players']}, '{body['game_time']}', '{body['date_created']}','{body['tc']}');")
            
            
            
            with DB_ENGINE.connect() as connection:
                connection.execute(sql_query)
                connection.commit()
        if msg["type"] == "create_join_request":
            logger.debug(f"Received event :join_open_party with tracecode: {body['tc']}")
            
            body['date_created'] = datetime.datetime.now().isoformat()
            sql_query = sqlalchemy.text(f"INSERT INTO player_join_request (open_party_id, player_id, player_rating, alignment, background, class, level, species, date_created, tc) VALUES ('{body['open_party_id']}','{body['player_id']}',{body['player_rating']},'{body['alignment']}','{body['background']}','{body['class']}',{body['level']},'{body['species']}','{body['date_created']}','{body['tc']}')")
            
            with DB_ENGINE.connect() as connection:
                connection.execute(sql_query)
                connection.commit()  
        consumer.commit_offsets()
        
    pass


app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("OpenAPI.yaml",
strict_validation=True,
validate_responses=True)



if __name__=="__main__":
    t1 = Thread(target=process_messages)
    t1.setDaemon(True)
    t1.start()
    app.run(host="0.0.0.0",port=8090)
    