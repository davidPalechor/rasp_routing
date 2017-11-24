import sqlite3

def create_connection(db_file):
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print e
    return None

def insert(values):
    query = "INSERT INTO routing_table (target_address, next_hop, target_seq_number, hop_count, lifetime, status)" + \
            "VALUES (?,?,?,?,?,?)"

    conn = create_connection("BD.bd")
    cursor = conn.cursor()
    cursor.execute(query, values)
    
    conn.commit()
    conn.close()
