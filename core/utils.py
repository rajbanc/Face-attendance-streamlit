import streamlit as st
import cv2
import numpy as np
import base64
import io
from PIL import Image
from json import JSONEncoder

import pandas as pd

def report_btn_callback(mysql_cursor, id, report_placeholder):
    print("id:", id)
    try:
        mysql_cursor.execute("""SELECT * FROM checkinout WHERE userid = %s ORDER BY checktime DESC""", (id,))
        attendance_result = mysql_cursor.fetchall()
        attendance_result = pd.DataFrame(attendance_result
                                         ,columns=['id', 'userid', 'checktime', 'checktype', 'verifycode', 'SN', 'sensorid', 'WorkCode', 'Reserved'])
        print("attendance: ", attendance_result)
        # st.session_state['attendance_result'] = attendance_result
        report_placeholder.write(attendance_result)
    except Exception as e:
        print("Error executing MySQL query:", e)

def cam_available(ip_cam):
    cap = cv2.VideoCapture(ip_cam)
    if cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            return False
        return True
    
def image_cropped(image):
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    pad_percent = 15
    h, w, _ = image.shape

    y_pad = int(h*pad_percent/100)
    x_pad = int(w*pad_percent/100)

    img = Image.fromarray(image)
    img = img.crop((x_pad, y_pad, w-x_pad, h-y_pad))
    img = np.array(img)

    return img
    
class NumpyArrayEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return JSONEncoder.default(self, obj)
    
def get_image_base64(image):
    _, im_arr = cv2.imencode('.jpg', image)  # im_arr: image in Numpy one-dim array format.
    im_bytes = im_arr.tobytes()
    return base64.b64encode(im_bytes)

def base64_img(img_str):
    image = base64.b64decode((img_str))
    image = Image.open(io.BytesIO(image))
    image = np.array(image)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    # cv2.imwrite('detections/image.jpg', image)
    return image
