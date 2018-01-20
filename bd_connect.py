import sqlite3
import logging

def dictfetchall(cursor):
    "Return all rows from a cursor as a dict"
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]

def create_connection(db_file):
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print e
    return None

def insert_routing_table(values):
    logger = logging.debug("Inserting into Routing table")
    query = "INSERT INTO routing_table (target_address, next_hop, target_seq_number, hop_count, lifetime, status)" + \
            "VALUES (?,?,?,?,?,?)"

    conn = create_connection("BD.db")
    cursor = conn.cursor()
    cursor.execute(query, values)
    
    conn.commit()
    conn.close()

def insert_rreq(values):
    logger = logging.debug("Inserting into RREQ table")
    query = "INSERT INTO RREQ VALUES(?, ?)"
    conn = create_connection("BD.db")
    cursor = conn.cursor()
    cursor.execute(query, values)
    
    conn.commit()
    conn.close()    

def consult_source(source):
    t = (source,)
    query = "SELECT * FROM routing_table WHERE source_address = ? "

    conn = create_connection("BD.db")
    cursor = conn.cursor()
    cursor.execute(query, t)
    rows = cursor.fetchall()

    conn.close()

    return rows


def consult_target(target):
    t = (target, target,)
    query = '''SELECT * FROM routing_table WHERE target_address = ? 
                AND status = 1 and hop_count = (SELECT min(hop_count) FROM routing_table WHERE target_address = ?)
                LIMIT 1'''

    conn = create_connection("BD.db")
    cursor = conn.cursor()
    cursor.execute(query, t)
    rows = dictfetchall(cursor)

    conn.close()

    return rows

def consult_duplicate(values):

    query = "SELECT * FROM rreq WHERE source_address = ? AND broadcast_id = ?"

    conn = create_connection("BD.db")
    cursor = conn.cursor()
    cursor.execute(query, values)
    rows = cursor.fetchall()

    conn.close()

    return rows

def update_routing_table(values):
    logger = logging.debug("Updating Routing_Table UPDATE ROUTING_TABLE SET %s = '%s' WHERE %s = %s" % values)
    query = "UPDATE ROUTING_TABLE SET %s = '%s' WHERE %s = %s" % values

    conn = create_connection("BD.db")
    cursor = conn.cursor()
    cursor.execute(query)

    conn.commit()
    conn.close()
