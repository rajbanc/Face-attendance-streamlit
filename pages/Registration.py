import streamlit as st
import dlib
import cv2
import json
import time
import numpy as np
from datetime import datetime

import yaml

from core.db_utils import db_connection, create_tables
from core.utils_register import face_registration, get_userinfo_data, get_registration_data
from core.utils import get_image_base64, NumpyArrayEncoder, image_cropped, base64_img
from core.liveliness_face import frontalfacedetector
from core.camera_init import fresh
from core.db_connect import connect_db

st.set_page_config(layout='wide')
st.title("Registration")

# with open('./config/db_config.yaml', 'r') as config_file:
#     config_data = yaml.safe_load(config_file)
# DB_NAME = config_data['Database'][0]['db_name']
# print(f'Db_name {DB_NAME}')

# DB_NAME = connect_db()
DB_NAME = 'srmlt_attendance'
conn = db_connection(DB_NAME)
create_tables()

frontal_face_detection = dlib.get_frontal_face_detector()

def insert_user_info(mysql_cursor):
    mysql_cursor.execute('''INSERT INTO userinfo (
                     badgenumber, defaultdeptid, name, Password, Card, Privilege, AccGroup, TimeZones,
                    Gender, Birthday, street, zip, ophone,FPHONE, pager, minzu, title, SN, SSN, U_Time,
                    State, City, SECURITYFLAGS, DelTag, RegisterOT, AutoSchPlan, MinAutoSchinterval, Image_id, entry_token)
                    VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                          %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''',
                         (None, None, None, None, None, None, None, None, None, None, None, None,
                          None, None, None, None, None, None, None, None, None, None, None, None,
                          None, None, None, None, None))
    conn.commit()


def registration(images):
    img_h, img_w,_ = images[0].shape
    mysql_cursor = conn.cursor(buffered=True)
    if "registration" not in st.session_state:
        st.session_state.registration = False
    if 'face_embeddings' not in st.session_state:
        st.session_state.face_embeddings = []

    for idx, (face, image) in enumerate(zip(st.session_state.faces, st.session_state.image_list)):
        # face -> ([97, 146, 179, 180],)
        print(idx, face)
        if len(face) == 1:
            x, y, w, h = face[0]
            x, y = x - 10, y - 10
            x, y = max(x, 0), max(y, 0)
            x2, y2 = x + w + 10, y + h + 10
            x2, y2 = min(x2, img_w), min(y2, img_h)
            face_img = image[y:y2, x:x2]

            face_data, face_embedding = face_registration(image, face, mysql_cursor)

            if face_data:
                st.write("Face matched!")
                st.write(f"Face is assigned to {face_data[0]}")
                time.sleep(2)
                return True
            if isinstance(face_embedding, np.ndarray):
                st.session_state.face_embeddings.append(face_embedding)
            
            if idx == 0:
                image_base64 = get_image_base64(face_img) # storing only one photo
                image = base64_img(image_base64)
                cv2.imwrite("temp1.jpg", image)
        else:
            st.error("Multiple faces detected. Only a single face should be detected.")
            time.sleep(3)
            return True

    face_encoding = {"face_embedding":  st.session_state.face_embeddings}
    encoded_face_encoding = json.dumps(face_encoding, cls=NumpyArrayEncoder)
    print('face_encoding', encoded_face_encoding)
    print('face_encoding type', type(encoded_face_encoding))
    created_on = datetime.now()
    next_userid = get_userinfo_data(mysql_cursor)
    print('next_userid', next_userid)


    mysql_cursor.execute('''INSERT INTO manual_registration (
                attendee_name, userid, device, image_base64, face_embedding, created_on)
                VALUES (%s, %s, %s, %s, %s, %s)''',
                    (attendee_name, next_userid, device, image_base64, encoded_face_encoding, created_on))
    conn.commit()
    insert_user_info(mysql_cursor)

    # st.success("Registration submitted successfully.")
    st.session_state.registration = False
    st.session_state.face_embeddings = []
    return True

st.session_state.registration = True

placeholder = st.empty()

with placeholder.container():
    col1, col2 = st.columns(2)
    attendee_name = col1.text_input('Attendee Name', value='', key='attendee_name')
    # attendee_id = col1.text_input('Attendee ID', value='', key='attendee_id')
    device = col1.text_input('Registration Device', value='', key='device')

    if attendee_name  and device:
        # Open camera and capture photo
        camera_col, button_col = col2.columns(2)
        with camera_col:
            camera_placeholder = st.empty()
        with button_col:
            button_placeholder = st.empty()
        # # ip_cam_url = ip_config_data['ip_cam_address']
        # cam = cv2.VideoCapture(ip_cam_url)
        num_images_to_cap = 3

        if 'image_list' not in st.session_state :
            st.session_state.image_list = []

        while True:#cam.isOpened():
            # ret, camera_photo = cam.read()
            ret, camera_photo = fresh.read()#(seqnumber=cnt+1)
            camera_rgb = image_cropped(camera_photo)

            if not ret:
                st.error("Can't capture frame")
                continue
            camera_placeholder.image(camera_rgb, caption="Capture Image")
            
            try:
                capture_button = button_placeholder.button("Capture Image")

            except Exception as e:
                print(f"Capture button error\n{e}")

            if capture_button:
                capture_button  = False
                # image_list.append(camera_photo)
                # append camera photo only if face appears in camera
                faces_exists = frontalfacedetector(camera_photo, frontal_face_detection)[0]

                if len(faces_exists):
                    st.session_state.image_list.append(camera_photo)
                    st.success(f"Image  {len(st.session_state.image_list)} Capture Successful!")
                else:
                    st.info("ReCapture with face in image frame")
                print('num of image', len(st.session_state.image_list))
            try:
                if len(st.session_state.image_list) >= num_images_to_cap:
                    break
            except Exception as e:
                print(f"Errors\n{e}")
                if 'image_list' not in st.session_state :
                    st.session_state.image_list = []
                
        if 'faces' not in st.session_state:
            st.session_state.faces = []
            print('enter here')
        try:   
            for camera_photo in st.session_state.image_list:
                st.session_state.faces.append(frontalfacedetector(camera_photo, frontal_face_detection)[0])
            print('  st.session_state.faces',  st.session_state.faces)
            status = registration(st.session_state.image_list)
        except Exception as e:
            print(f"Error\n{e}")

        if 'image_list' in st.session_state :
            st.session_state.image_list = []
        if 'faces' in st.session_state :
            st.session_state.faces = []
        # print(status)
        # attendee_name, attendee_id, device = None, None, None
        # camera_photo = None
        try:
            if status:
                print('status', status)
            # placeholder.empty()
            status = False
        except Exception as e:
            print('eee' , e)
        
        for key in st.session_state:
            del st.session_state[key]

        st.experimental_rerun()


