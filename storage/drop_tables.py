import mysql.connector

db_conn = mysql.connector.connect(host="kafka-acit3855.eastus.cloudapp.azure.com", user="",
password="", database="events")
db_cursor = db_conn.cursor
c = db_conn.cursor()






c.execute('DROP TABLE open_party')
c.execute('DROP TABLE player_join_request' )
db_conn.commit()
db_conn.close()