import yaml

def get_dbname():
    with open('./config/db_config.yaml', 'r') as config_file:
        config_data = yaml.safe_load(config_file)
    DB_NAME = config_data['Database'][0]['db_name']
    
    # if config_data['Database_server']:
    #     DB_NAME = config_data['Database_server'][0]['db_name']

    # elif config_data['Database_local']:
    #     DB_NAME = config_data['Database_local'][0]['db_name']
    
    # print('DB_NAME', DB_NAME)
    return DB_NAME