import yaml

def connect_db():
    with open('./config/db_config.yaml', 'r') as config_file:
        config_data = yaml.safe_load(config_file)
    DB_NAME = config_data['Database'][0]['db_name']
    return DB_NAME