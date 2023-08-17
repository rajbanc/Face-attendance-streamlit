import os
import time
import streamlit as st
import cv2
import dlib
import numpy as np
import pickle 
import tensorflow as tf
from datetime import datetime, timedelta
import pandas as pd

import yaml

from core.camera_init import fresh
from core.liveliness_face import check_liveliness
from core.db_utils import create_tables, db_connection, create_database
from core.utils_register import get_user_data, get_guest_data
from core.utils import image_cropped, cam_available, read_yaml_data
from core.utils_attendance import verify_face
from core.db_connect import get_dbname

st.cache_data.clear()
st.set_page_config(layout='wide',
                   page_title= "Attendance")

st.title("Attendance")

# with open('./config/db_config.yaml', 'r') as config_file:
#     config_data = yaml.safe_load(config_file)

create_tables()


# Function to read data from the YAML file
# def read_yaml_data(file_path):
#     if os.path.exists(file_path):
#         with open(file_path, 'r') as file:
#             existing_data = yaml.safe_load(file)
#         return existing_data
#     else:
#         return None


if __name__=="__main__":
    DB_NAME = get_dbname()
    # DB_NAME = 'srmlt_attendance'
    create_database(DB_NAME)
    # DB_NAME = config_data['Database'][0]['db_name']
    conn = db_connection(DB_NAME)


    frontal_face_detector = dlib.get_frontal_face_detector()
    model_path = './liveliness_model/liveness.model'
    le_path = './liveliness_model/label_encoder.pickle'
    
    yesterday = datetime.now().date() - timedelta(1)

    liveliness_model = tf.keras.models.load_model(model_path)
    labels = pickle.loads(open(le_path,'rb').read())

    ip_cam = st.sidebar.text_input("Enter Ip cam address")

    if 'id' not in st.session_state:
        st.session_state.id = []  

    camera_col, attendent_col, guest_col = st.columns(3)

    with camera_col:
        camera_placeholder = st.empty()
        
   
    with attendent_col:
        attendent_placeholder = st.empty()
        attendent_name_placeholder = st.empty()
        attendent_date_placeholder = st.empty()

    with guest_col:
        guest_placeholder = st.empty()
        guest_name_placeholder = st.empty()
        guest_date_placeholder = st.empty()
        close_btn_placeholder = st.empty()
    
    error_placeholder = st.empty()

    mysql_cursor = conn.cursor()
    stored_encodings, attendee_names, attendee_ids = get_user_data(mysql_cursor)
    guest_stored_encoding, guest_names, guest_attendee_ids = get_guest_data(mysql_cursor)

    # print(f"initail camers  {fresh.camera }")
    # with open('./config/ip_cam_config.yaml', 'r') as config_file:
    #     ip_config_data = yaml.safe_load(config_file)

    # if fresh.camera != ip_config_data['ip_cam_address']:
    #     fresh.change_camera(ip_config_data['ip_cam_address'])
    # print(f"changed camers  {fresh.camera }")

    # Create or get the 'existing_data' from st.session_state
    if 'existing_data' not in st.session_state:
        file_path = './config/ip_cam_config.yaml'
        existing_data = read_yaml_data(file_path)
        if existing_data is not None:
            st.session_state.existing_data = existing_data
        else:
            st.session_state.existing_data = {}  # Initialize to an empty dictionary
    
    else:
        # # Check if the user input has changed and update 'existing_data' if necessary
        # ip_cam = st.sidebar.text_input("Enter Ip cam address")

        if ip_cam:
            if ':' in ip_cam:
                split_ip_cam = ip_cam.split(':')
                ip_cam_split = split_ip_cam[0].split('.')
                number_value = True
                for x in ip_cam_split:
                    if not x.isnumeric():
                        number_value = False
                
                split_cam = split_ip_cam[1].split('/')
                numeric_value = True
                if not split_cam[0].isnumeric():
                    numeric_value = False
            else:
                ip_cam_split = ip_cam.split('.')
                number_value = True
                for x in ip_cam_split:
                    if not x.isnumeric():
                        number_value = False
                numeric_value = True


            if number_value and numeric_value and cam_available("rtsp://" + ip_cam):
                st.toast("Successful")
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

    print(f"initail camers  {fresh.camera }")
    with open('./config/ip_cam_config.yaml', 'r') as config_file:
        ip_config_data = yaml.safe_load(config_file)

    if fresh.camera != ip_config_data['ip_cam_address']:
        fresh.change_camera(ip_config_data['ip_cam_address'])
    print(f"changed camers  {fresh.camera }")


    st.sidebar.write(f"Ip_cam Address: {ip_config_data['ip_cam_address'][7:]}")

    if 'recognized_faces' not in st.session_state:
        st.session_state['recognized_faces'] = None
    
    while True:
        ret, frame = fresh.read()
        frame = image_cropped(frame)
        
        if not ret:
            st.error("Cannot capture frame")
            continue
        
        image, real_face_bboxes = check_liveliness(
            frame, 
            liveliness_model, 
            labels, 
            frontal_face_detector
        )
        camera_placeholder.image(image)

        if len(real_face_bboxes) >= 1:
            # continue
        
            st.session_state['recognized_faces'], guest_stored_encoding, guest_attendee_ids = verify_face(
                frame, stored_encodings, attendee_names, attendee_ids, conn,
                guest_stored_encoding, guest_attendee_ids, real_face_bboxes
                )
        
        ## detection and retrive 'in' or 'out' state
        start_time = time.time()        
        if st.session_state['recognized_faces']:
            for face in st.session_state['recognized_faces']:
                category = face['category']
                if category == 'manual':
                    print("category", category)
                    display_txt = ''
                    name = face['name']
                    id = face['id']
                    state = face['state']
                    dt = str(face['currentime']).split('.')[0]
                    if state == 0:
                        display_txt = f"Welcome "
                        display_txt1 = f"{name.title()}"
                        display_txt2 = f" {dt}"
                    elif state == 1:
                        display_txt = f"Thank you"
                        display_txt1 = f"{name.title()}"
                        display_txt2 = f"{dt}"

                        # close_btn_placeholder.text(display_txt)
                    if state == 0:
                        text_color = "green"
                        font_size = "70px"
                        text_color1 = "green"
                        font_size1 = "30px"
                    elif state == 1:
                        text_color = "blue"
                        font_size = "70px"
                        text_color1 = "blue"
                        font_size1 = "30px"
                        
                    styled_text = f'<p style="color: {text_color}; font-size: {font_size};">{display_txt}</p>'
                    styled_text1 = f'<p style="color: {text_color1}; font-size: {font_size1};">{display_txt1}</p>'
                    styled_text2 = f'<p style="color: {text_color1}; font-size: {font_size1};">{display_txt2}</p>'
                    attendent_placeholder.markdown(styled_text, unsafe_allow_html=True)
                    attendent_name_placeholder.markdown(styled_text1, unsafe_allow_html=True)
                    attendent_date_placeholder.markdown(styled_text2, unsafe_allow_html=True)
                         
                elif category=='guest':
                    print("categori_guest")
                    display_txt = ''
                    state = face['state']
                    image = face['image']
                    dt = str(face['currentime']).split('.')[0]
                    guest_id = face['id']

                    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                    close_btn_placeholder.image(image)
                    # if state == 0:
                    #     display_txt = f'Welcome Guest\n {id} {dt} IN'
                    # elif state == 1:
                    #     display_txt = f'Thank you Guest\n {id} {dt} OUT'
                    if state == 0:
                        display_txt = f"Welcome Guest "
                        display_txt1 = f"{guest_id}"
                        display_txt2 = f" {dt}"
                    elif state == 1:
                        display_txt = f"Thank you Guest"
                        display_txt1 = f"{guest_id}"
                        display_txt2 = f"{dt}"
                    # guest_placeholder.text(display_txt)
                        
                    if state == 0:
                        text_color = "green"
                        font_size = "50px"
                        text_color1 = "green"
                        font_size1 = "30px"
                    elif state == 1:
                        text_color = "blue"
                        font_size = "50px"
                        text_color1 = "blue"
                        font_size1 = "30px"
                        
                    styled_text = f'<p style="color: {text_color}; font-size: {font_size};">{display_txt}</p>'
                    styled_text1 = f'<p style="color: {text_color1}; font-size: {font_size1};">{display_txt1}</p>'
                    styled_text2 = f'<p style="color: {text_color1}; font-size: {font_size1};">{display_txt2}</p>'
                    guest_placeholder.markdown(styled_text, unsafe_allow_html=True)
                    guest_name_placeholder.markdown(styled_text1, unsafe_allow_html=True)
                    guest_date_placeholder.markdown(styled_text2, unsafe_allow_html=True)
        
        if 'recognized_faces'  in st.session_state:
            st.session_state['recognized_faces'] = []
        
        duration = time.time() - start_time

        if duration > 5:
            print('inside if')
            print('duration', duration)
            attendent_placeholder.empty()
            attendent_name_placeholder.empty()
            attendent_date_placeholder.empty()
            guest_placeholder.empty()
            guest_name_placeholder.empty()
            guest_date_placeholder.empty()

        

        num = datetime.now().date() - yesterday
        if num.days >= 1:
            # attendent_col.empty()
            yesterday = datetime.now().date()

        # close_btn_placeholder.empty()
        # guest_placeholder.empty()
    
    
    fresh.release()
