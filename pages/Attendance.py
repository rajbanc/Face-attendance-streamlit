import streamlit as st
import cv2
import dlib
import numpy as np
import pickle 
import tensorflow as tf
from datetime import datetime, timedelta

import yaml

from core.camera_init import fresh
from core.liveliness_face import check_liveliness
from core.db_utils import create_tables, db_connection
from core.utils_register import get_user_data, get_guest_data
from core.utils import image_cropped
from core.utils_attendance import verify_face
from core.db_connect import get_dbname

st.cache_data.clear()
st.set_page_config(layout='wide')

st.title("Attendance")

# with open('./config/db_config.yaml', 'r') as config_file:
#     config_data = yaml.safe_load(config_file)

create_tables()

if __name__=="__main__":
    # DB_NAME = get_dbname()
    DB_NAME = 'srmlt_attendance'
    # DB_NAME = config_data['Database'][0]['db_name']
    conn = db_connection(DB_NAME)

    device = 'IP_cam'

    frontal_face_detector = dlib.get_frontal_face_detector()
    model_path = './liveliness_model/liveness.model'
    le_path = './liveliness_model/label_encoder.pickle'
    
    yesterday = datetime.now().date() - timedelta(1)

    liveliness_model = tf.keras.models.load_model(model_path)
    labels = pickle.loads(open(le_path,'rb').read())

    camera_col, guest_col, attendent_col = st.columns(3)
    text_col, img_col = guest_col.columns(2)

    with camera_col:
        camera_placeholder = st.empty()
        close_btn_placeholder = st.empty()

    with text_col:
        text_placeholder = st.empty()

    with img_col:
        img_placeholder = st.empty()
        
    with attendent_col:
        attendent_placeholder = st.empty()

    error_placeholder = st.empty()

    mysql_cursor = conn.cursor()
    stored_encodings, attendee_names, attendee_ids = get_user_data(mysql_cursor)
    guest_stored_encoding, guest_names, guest_attendee_ids = get_guest_data(mysql_cursor)
    # print("guest_stored_encoding, guest_names, guest_attendee_ids ", guest_names, guest_attendee_ids )

    print(f"initail camers  {fresh.camera }")
    with open('./config/ip_cam_config.yaml', 'r') as config_file:
        ip_config_data = yaml.safe_load(config_file)

    if fresh.camera != ip_config_data['ip_cam_address']:
        fresh.change_camera(ip_config_data['ip_cam_address'])
    print(f"changed camers  {fresh.camera }")

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

        if len(real_face_bboxes) < 1:
            continue
        
        recognized_faces, guest_stored_encoding, guest_attendee_ids = verify_face(
            frame, stored_encodings, attendee_names, attendee_ids, conn,
            device, guest_stored_encoding, guest_attendee_ids, real_face_bboxes
            )

        ## detection and retrive 'in' or 'out' state
        if recognized_faces:
            for face in recognized_faces:
                category = face['category']
                if category == 'manual':
                    print("category", category)
                    display_txt = ''
                    name = face['name']
                    id = face['id']
                    state = face['state']
                    dt = str(face['currentime']).split('.')[0]
                    if state == 0:
                        display_txt = f"Welcome {name.title()} {id} {dt}"
                    elif state == 1:
                        display_txt = f"Thank you {name.title()} {id} {dt}"
                    attendent_placeholder.text(display_txt)
                elif category=='guest':
                    print("categori_guest")
                    display_txt = ''
                    state = face['state']
                    image = face['image']
                    dt = str(face['currentime']).split('.')[0]
                    id = face['id']
                    print(id)

                    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                    img_placeholder.image(image)
                    if state == 0:
                        display_txt = f'Welcome Guest\n {id} {dt}'
                    elif state == 1:
                        display_txt = f'Thank you Guest\n {id} {dt}'
                    text_placeholder.text(display_txt)
                    close_btn_placeholder.text(display_txt)


        
        num = datetime.now().date() - yesterday
        if num.days >= 1:
            attendent_col.empty()
            yesterday = datetime.now().date()
    
    fresh.release()
