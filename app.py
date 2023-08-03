import cv2
import streamlit as st
import os
import yaml

from core.db_utils import create_database, create_tables
from core.utils import cam_available
from core.db_connect import connect_db

from core.camera_init import fresh
print(f'{fresh=}')



st.title("Face Attendance system")
st.cache_data.clear()


# with open('./config/db_config.yaml', 'r') as config_file:
#     config_data = yaml.safe_load(config_file)

# DB_NAME = connect_db()
DB_NAME = 'srmlt_attendance'

# DB_NAME = config_data['Database'][0]['db_name']
# print(f'Db_name {DB_NAME}')

create_database(DB_NAME)

create_tables()

# Function to read data from the YAML file
def read_yaml_data(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            existing_data = yaml.safe_load(file)
        return existing_data
    else:
        return None

# Create or get the 'existing_data' from st.session_state
if 'existing_data' not in st.session_state:
    file_path = './config/ip_cam_config.yaml'
    existing_data = read_yaml_data(file_path)
    if existing_data is not None:
        st.session_state.existing_data = existing_data
    else:
        st.session_state.existing_data = {}  # Initialize to an empty dictionary

# Check if the user input has changed and update 'existing_data' if necessary
ip_cam = st.sidebar.text_input("Enter Ip cam address")

if ip_cam:
    ip_cam_split = ip_cam.split('.')
    number_value = True
    for x in ip_cam_split:
        if not x.isnumeric():
            number_value = False

    if number_value and cam_available("rtsp://" + ip_cam):
        st.success("Successful")
    else:
        st.error(f"Invalid address `{ip_cam}`")
        st.stop()

ip_cam = "rtsp://" + ip_cam

if st.session_state.existing_data.get('ip_cam_address') != ip_cam and ip_cam !='rtsp://':
    data = {'ip_cam_address': ip_cam}

    # Update 'existing_data'
    st.session_state.existing_data = data

    # Write the new data to the YAML file
    file_path = './config/ip_cam_config.yaml'
    with open(file_path, 'w') as file:
        yaml.dump(data, file)

    print(f'Before {fresh.camera =}')
    fresh.change_camera(ip_cam)
    print(f'After {fresh.camera =}')