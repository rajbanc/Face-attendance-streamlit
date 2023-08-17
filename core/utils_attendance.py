import cv2
import face_recognition
import numpy as np
import uuid
import json
from datetime import datetime

from core.utils import NumpyArrayEncoder, get_image_base64, base64_img

duration = 30


def verify_face(
    image, stored_encodings, attendee_names, attendee_ids, conn, 
    guest_stored_encoding, guest_attendee_ids, face_bboxes
    ):
    print("Entered to verify_face_function")

    mysql_cursor = conn.cursor(buffered=True)

    recognized_faces = []
    current_time = datetime.now()
    checktype = 0
    verifycode = 32
    SN = 1
    sensorid = 124

     # Mapping coordinates from opencv into face_recognition format
    # Format [[x1, y2, w, h]] --> [(y1, x2, y2, x1)]
    faces_cropped  = [(face[1], face[0] + face[2], face[1] + face[3], face[0]) for face in face_bboxes]
    encoded_face_in_frame = face_recognition.face_encodings(image, faces_cropped)

    for encode_face, face_cropped in zip(encoded_face_in_frame, faces_cropped):
        if len(encode_face) != 128:
            continue
        matches = face_recognition.compare_faces(stored_encodings, encode_face, tolerance=0.45)
        face_dist = face_recognition.face_distance(stored_encodings, encode_face)

        if any(matches):
            print("Manual")
            match_index = np.argmin(face_dist)
            # aggregate matched user data
            attendee_name = attendee_names[match_index].upper()
            attendee_id = attendee_ids[match_index]

            mysql_cursor.execute("""SELECT * FROM checkinout WHERE userid = %s
                             ORDER BY checktime DESC""",
                            (attendee_id, ))
            attendance_result = mysql_cursor.fetchone()

            if attendance_result: 
                # grab value of checktype column and store in last_checktype variable
                dt= attendance_result[2]
                diff = current_time - dt
                last_checktype = int(attendance_result[3])
                if dt.date() == datetime.now().date():
                    if last_checktype == 0:
                        checktype = 1
                    elif last_checktype == 1:
                        checktype = 0
                else:
                    checktype = 0
                if diff.total_seconds() > duration:
                    mysql_cursor.execute(
                        """INSERT INTO checkinout
                        (userid, checktime, checktype, verifycode, SN, sensorid, WorkCode, Reserved )
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
                        ( attendee_id, datetime.now(),checktype, verifycode, SN, sensorid, None, None) 
                    )
                    conn.commit()
                    recognized_faces.append({'id': attendee_id,'name': attendee_name ,'state': checktype, 'currentime':current_time, 'category':'manual'})

            else:
                '''If no rocord is found'''
                
                mysql_cursor.execute(
                    """INSERT INTO checkinout
                    (userid, checktime, checktype, verifycode, SN, sensorid, WorkCode, Reserved )
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
                    ( attendee_id, datetime.now(),checktype, verifycode, SN, sensorid, None, None) 
                )
                conn.commit()
                recognized_faces.append({'name':attendee_name, 'id':attendee_id, 'state': checktype, 'currentime':current_time, 'category':'manual'})
        
        else:
            # continue
            print('For Guest.')
            try:
                guest_matches = face_recognition.compare_faces(guest_stored_encoding, encode_face, tolerance=0.45)
                guest_face_dict = face_recognition.face_distance(guest_stored_encoding, encode_face)
            except:
                continue

            try:
                y1, x2, y2, x1 = face_cropped
                cropped_face = image[ y1:y2, x1:x2]
                cropped_face = cv2.cvtColor(cropped_face, cv2.COLOR_BGR2RGB)
            except Exception as e:
                print(f"Exception:\n{e}")
                continue
            
            if len(guest_face_dict) > 0:
                guest_matches_id = np.argmin(guest_face_dict)

                mysql_cursor.execute("""SELECT guest_id FROM guest_registration ORDER BY guest_id DESC""")
                guest_attendance_results = mysql_cursor.fetchone()

                if guest_matches[guest_matches_id]:
                    guest_attendee_id = guest_attendee_ids[guest_matches_id]

                    if guest_attendance_results:
                        mysql_cursor.execute("""SELECT * FROM checkinout WHERE userid = %s
                             ORDER BY checktime DESC""",
                            (guest_attendee_id, ))
                        attendance_result = mysql_cursor.fetchone()
                        # grab value of checktype column and store in last_checktype variable
                        dt = attendance_result[2]
                        diff = current_time - dt
                        last_checktype = int(attendance_result[3])
                        if dt.date() == datetime.now().date():
                            if last_checktype == 0:
                                checktype = 1
                            elif last_checktype == 1:
                                checktype = 0
                        else:
                            checktype = 0
                        if diff.total_seconds() > duration:
                            mysql_cursor.execute(
                                """INSERT INTO checkinout
                                (userid, checktime, checktype, verifycode, SN, sensorid, WorkCode, Reserved )
                                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
                                ( guest_attendee_id, datetime.now(),checktype, verifycode, SN, sensorid, None, None) 
                            )
                            conn.commit()
                            recognized_faces.append({'state':checktype, 'category':'guest', 'image': cropped_face, 'id':guest_attendee_id, 'currentime':current_time,})
                    
                else:
                    last_guest_id= guest_attendance_results[0]
                    next_guest_id = last_guest_id + 1
                    guest_name = None
                    image_base64 = get_image_base64(np.asarray(cropped_face))
                    face_encoding = {"face_embedding": encode_face}
                    encoded_face_encoding = json.dumps(face_encoding, cls=NumpyArrayEncoder)
                    created_on = datetime.now()
                    mysql_cursor.execute(
                        """INSERT INTO guest_registration(
                                guest_id, guest_name, image_base64, face_embedding, created_on)
                                VALUES (%s, %s, %s, %s, %s)""",
                            (next_guest_id, guest_name, image_base64,encoded_face_encoding, created_on)   
                    )
                    conn.commit()
                    print('Inserted new guest')
                    guest_stored_encoding.append(encode_face)
                    guest_attendee_ids.append(next_guest_id)

                    mysql_cursor.execute(
                        """INSERT INTO checkinout
                        (userid, checktime, checktype, verifycode, SN, sensorid, WorkCode, Reserved )
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
                        ( next_guest_id, datetime.now(),checktype, verifycode, SN, sensorid, None, None) 
                    )
                    conn.commit()
                    recognized_faces.append({'state':checktype, 'category':'guest', 'image': cropped_face, 'id':next_guest_id, 'currentime':current_time,})

            else:
                '''registration of guest for empty guest table'''

                init_userid = 40001
                guest_name = None
                image_base64 = get_image_base64(np.asarray(cropped_face))
                face_encoding = {"face_embedding": encode_face}
                encoded_face_encoding = json.dumps(face_encoding, cls=NumpyArrayEncoder)
                created_on = datetime.now()
                
                mysql_cursor.execute(
                   """INSERT INTO guest_registration(
                        guest_id, guest_name, image_base64, face_embedding, created_on)
                        VALUES (%s, %s, %s, %s, %s)""",
                    (init_userid, guest_name, image_base64,encoded_face_encoding, created_on)   
                )
                conn.commit()
                guest_stored_encoding.append(encode_face)
                guest_attendee_ids.append(init_userid)

                mysql_cursor.execute(
                    """INSERT INTO checkinout
                    (userid, checktime, checktype, verifycode, SN, sensorid, WorkCode, Reserved )
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
                    ( init_userid, datetime.now(),checktype, verifycode, SN, sensorid, None, None) 
                )
                conn.commit()
                recognized_faces.append({'state':'in_new', 'category':'guest', 'image': cropped_face, 'id': init_userid, 'currentime':current_time,})
                print('sucessful insert')

    mysql_cursor.close()
    return recognized_faces, guest_stored_encoding, guest_attendee_ids



