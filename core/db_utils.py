import mysql.connector as connector
import yaml
import sys

with open('./config/db_config.yaml', 'r') as config_file:
    config_data = yaml.safe_load(config_file)


def get_connection():
     return connector.connect(
        host = config_data['Database'][0]['host_docker'] if sys.platform=='linux' else config_data['Database'][0]['host_win'],
        port = config_data['Database'][0]['port'],
        user = config_data['Database'][0]['user'],
        password = config_data['Database'][0]['password']
    )


def create_database(db_name):
    db_creation_query = f'CREATE DATABASE IF NOT EXIST {db_name}'
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

def create_table(db_name, table_name, col_names):
    table_creation_query = f'CREATE TABLE IF NOT EXISTS {table_name} {col_names}'

    conn = db_connection(db_name)
    sql_cursor = conn.cursor()
    sql_cursor.execute(table_creation_query)

def create_tables():
    DB_NAME = 'srmlt_attendance'
    TABLE_NAME = ['registration', 'attendance', 'guest_attendance', 'guest_registration']

    create_table(
        DB_NAME,
        TABLE_NAME[0], 
        '''(id INT AUTO_INCREMENT PRIMARY KEY, attendee_name VARCHAR(100),
            attendee_id VARCHAR(40), device VARCHAR(40), image_base64 LONGTEXT,
            face_embedding JSON, created_on DATETIME)'''
    )

    create_table(
        DB_NAME,
        TABLE_NAME[1], 
        '''(id INT AUTO_INCREMENT PRIMARY KEY, attendee_name VARCHAR(100), attendee_id VARCHAR(40),
        device VARCHAR(40), date DATE, check_in TIME, check_out TIME)'''
    )
    create_table(
        DB_NAME,
        TABLE_NAME[2], 
        '''(id INT AUTO_INCREMENT PRIMARY KEY, guest_attendee_id VARCHAR(36) , guest_name VARCHAR(100), 
        device VARCHAR(40), date DATE, check_in TIME, check_out TIME)'''
    )
    create_table(
        DB_NAME,
        TABLE_NAME[3], 
        ''' (id INT AUTO_INCREMENT PRIMARY KEY, guest_attendee_id VARCHAR(36), guest_name VARCHAR(100), image_base64 LONGTEXT,
        face_embedding JSON, created_on DATETIME)'''
    )
