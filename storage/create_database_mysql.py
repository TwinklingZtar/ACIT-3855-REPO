import mysql.connector

db_conn = mysql.connector.connect(host="kafka-acit3855.eastus.cloudapp.azure.com", user="SIan",
password="password", database="events")
db_cursor = db_conn.cursor
c = db_conn.cursor()
c.execute('''
CREATE TABLE open_party
(id INTEGER AUTO_INCREMENT,
open_party_id VARCHAR(250),
game_master_id VARCHAR(250) NOT NULL,
campaign VARCHAR(250) NOT NULL,
game_location VARCHAR(250) NOT NULL,
game_frequency VARCHAR(250) NOT NULL,
max_players INTEGER NOT NULL,
game_time VARCHAR(100) NOT NULL,
date_created DATETIME NOT NULL,
tc VARCHAR(250) NOT NULL,
CONSTRAINT open_party_pk PRIMARY KEY (id))
''')

c.execute('''
CREATE TABLE player_join_request
(
id INTEGER AUTO_INCREMENT,
open_party_id VARCHAR(250)NOT NULL,
player_id VARCHAR(250) NOT NULL,
player_rating INTEGER NOT NULL,
alignment VARCHAR(100) NOT NULL,
background VARCHAR(100) NOT NULL,
class VARCHAR(100) NOT NULL,
level INTEGER NOT NULL,
species VARCHAR(100) NOT NULL,
date_created DATETIME NOT NULL,
tc VARCHAR(250) NOT NULL,
CONSTRAINT player_join_request_pk PRIMARY KEY (id))
''')
db_conn.commit()
db_conn.close()