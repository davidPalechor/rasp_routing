import sqlite3

conn = sqlite3.connect("BD.bd")

query = "CREATE TABLE IF NOT EXISTS ROUTING_TABLE (" + \
         "ID INTEGER PRIMARY KEY AUTOINCREMENT," + \
         "target_address VARCHAR(15) NOT NULL," + \
         "next_hop VARCHAR(15) NOT NULL," + \
         "target_seq_number INTEGER NOT NULL," + \
         "hot_count INTEGER NOT NULL," + \
         "lifetime DECIMAL(4,2) NOT NULL," + \
         "status INTEGER NOT NULL)"

with conn.cursor() as cursor:
    cursor.execute(query,)
