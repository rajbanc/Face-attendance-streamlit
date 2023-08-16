import mysql.connector as connector
import yaml
import sys
import hashlib

with open('./config/db_config.yaml', 'r') as config_file:
    config_data = yaml.safe_load(config_file)


def get_connection():
     return connector.connect(
        host = config_data['Database'][0]['host_docker'] if sys.platform=='linux' else config_data['Database'][0]['host_win'],
        port = config_data['Database'][0]['port'],
        user = config_data['Database'][0]['user'],
        password = config_data['Database'][0]['password']#hashlib.md5(config_data['Database'][0]['password']).hexdigest()
        
    )
"""
def get_connection1():
    try:
        print("GET CONNECTION TO SERVER")
        return connector.connect(
            host = config_data['Database_server'][0]['host_docker'] if sys.platform=='linux' else config_data['Database_server'][0]['host_win'],
            port = config_data['Database_server'][0]['port'],
            user = config_data['Database_server'][0]['user'],
            password = config_data['Database_server'][0]['password']
        )
    except Exception as e:
        print("cannot connect to server_database and connect to local server")
    finally:
        print("GET CONNECT TO LOCAL ")
        return connector.connect(
            host = config_data['Database_local'][0]['host_docker'] if sys.platform=='linux' else config_data['Database_local'][0]['host_win'],
            port = config_data['Database_local'][0]['port'],
            user = config_data['Database_local'][0]['user'],
            password = config_data['Database_local'][0]['password'],
        )"""


def create_database(db_name):
    db_creation_query = f'CREATE DATABASE IF NOT EXISTS {db_name}'
    conn = get_connection()
    sql_cursor = conn.cursor()

    sql_cursor.execute("SHOW DATABASES")
    db_exists = False 
    for x in sql_cursor:
        # x is tuple('st_attendance',)
        if x[0]==db_name:
            # print('db name ',x[0], ' already exists.')
            db_exists = True
            return
    if not db_exists:
        sql_cursor.execute(db_creation_query)

def db_connection(db_name):
    return connector.connect(
        host = config_data['Database'][0]['host_docker'] if sys.platform=='linux' else config_data['Database'][0]['host_win'],
        port = config_data['Database'][0]['port'],
        user = config_data['Database'][0]['user'],
        password = config_data['Database'][0]['password'],
        database = db_name
    )

"""def db_connection1():
    try:
        print('connected to server datatabase')
        return connector.connect(
            host = config_data['Database_server'][0]['host_docker'] if sys.platform=='linux' else config_data['Database_server'][0]['host_win'],
            port = config_data['Database_server'][0]['port'],
            user = config_data['Database_server'][0]['user'],
            password = config_data['Database_server'][0]['password'],
            database = config_data['Database_server'][0]['db_name']
        )
    except Exception as e:
        print("cannot connect to server_database")

        print('connected to local database')
        return connector.connect(
            host = config_data['Database_local'][0]['host_docker'] if sys.platform=='linux' else config_data['Database_local'][0]['host_win'],
            port = config_data['Database_local'][0]['port'],
            user = config_data['Database_local'][0]['user'],
            password = config_data['Database_local'][0]['password'],
            database = config_data['Database_local'][0]['db_name']
        )
        """

def create_table(db_name, table_name, col_names):
    table_creation_query = f'CREATE TABLE IF NOT EXISTS {table_name} {col_names}'

    conn = db_connection(db_name)
    sql_cursor = conn.cursor()
    sql_cursor.execute(table_creation_query)

def create_tables():
    DB_NAME = 'adms_dbnew'
    # DB_NAME = 'srmlt_attendance'
    # DB_NAME = db_name

    TABLE_NAME = ['manual_registration', 'guest_registration', 'userinfo', 'checkinout']

    create_table(
        DB_NAME,
        TABLE_NAME[0], 
        '''(id INT AUTO_INCREMENT PRIMARY KEY, attendee_name VARCHAR(100),
            userid INT, device VARCHAR(40), image_base64 LONGTEXT,
            face_embedding JSON, created_on DATETIME)'''
    )

    create_table(
        DB_NAME,
        TABLE_NAME[1], 
        ''' (id INT AUTO_INCREMENT PRIMARY KEY, guest_id INT, guest_name VARCHAR(100), image_base64 LONGTEXT,
        face_embedding JSON, created_on DATETIME)'''
    )
    
    create_table(
        DB_NAME,
        TABLE_NAME[2], 
        '''(userid INT AUTO_INCREMENT PRIMARY KEY, badgenumber VARCHAR(20), defaultdeptid INT, name VARCHAR(40),
        Password VARCHAR(20), Card VARCHAR(20), Privilege INT, AccGroup INT, TimeZones VARCHAR(20), 
        Gender VARCHAR(2), Birthday DATETIME , street VARCHAR(40), zip VARCHAR(6), ophone VARCHAR(20), FPHONE VARCHAR(20),
        pager VARCHAR(20), minzu VARCHAR(8), title VARCHAR(20), SN VARCHAR(20), SSN VARCHAR(20), U_TIME VARCHAR(20), 
        STATE VARCHAR(2), CITY VARCHAR(2), SECURITYFLAGS INT, DELTag INT, RegisterOT INT,
        AutoSchPlan INT, MinAutoSchInterval INT, Image_id Int, entry_token VARCHAR(191) )'''
    )

    create_table(
        DB_NAME,
        TABLE_NAME[3],
        '''(id INT AUTO_INCREMENT PRIMARY KEY, userid INT, checktime DATETIME, checktype VARCHAR(2), verifycode INT,
        SN VARCHAR(20), sensorid VARCHAR(5), WorkCode VARCHAR(20), Reserved VARCHAR(20))'''
    )