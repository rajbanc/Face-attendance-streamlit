import cv2
import face_recognition
import numpy as np
import uuid
import json
from datetime import datetime

from core.utils import NumpyArrayEncoder, get_image_base64, base64_img

duration = 3

def create_datetime(date, time):
    dt = str(date) + " " + str(time)
    dt = dt.split('.')[0]
    return datetime.strptime(dt,'%Y-%m-%d %H:%M:%S')

def register_guest_attendee(cropped_face, encode_face):
    guest_attendee_id = str(uuid.uuid4().hex)
    guest_name = None
    image_base64 = get_image_base64(np.asarray(cropped_face))
    image= base64_img(image_base64)
    cv2.imwrite("temp.jpg", image)
    
    face_encoding = {"face_embedding": encode_face}
    encoded_face_encoding = json.dumps(face_encoding, cls=NumpyArrayEncoder)

    created_on = datetime.now()
        
    return guest_attendee_id, guest_name, image_base64, encoded_face_encoding, created_on 

def insert_guest_registration(mysql_cursor, guest_attendee_id, guest_name, image_base64, encoded_face_encoding, created_on):
    query = """INSERT INTO guest_registration(
                guest_attendee_id, guest_name, image_base64, face_embedding, created_on)
                VALUES (%s, %s, %s, %s, %s)"""
                
    mysql_cursor.execute(query, (guest_attendee_id, guest_name, image_base64, encoded_face_encoding, created_on))

def verify_face(
    image, stored_encodings, attendee_names, attendee_ids, conn, 
    device, guest_stored_encoding, guest_attendee_ids, face_bboxes
    ):
    print("Entered to verify_face_function")

    mysql_cursor = conn.cursor(buffered=True)

    recognized_faces = []
    current_time = datetime.now().time()

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

            mysql_cursor.execute("""SELECT * FROM attendance WHERE 
                            attendee_name = %s AND attendee_id = %s AND date = %s ORDER BY check_in DESC""",
                            (attendee_name, attendee_id, datetime.now().date()))
            attendance_result = mysql_cursor.fetchone()

            if attendance_result: 
                if attendance_result[6] is None:
                    attendee_dt = create_datetime(attendance_result[4], attendance_result[5])

                    diff = datetime.now() - attendee_dt
                    if diff.total_seconds() > duration:
                        # checktype: 1
                        mysql_cursor.execute("""UPDATE attendance 
                                    SET check_out = %s WHERE id=%s AND attendee_id = %s""",
                                    (current_time, attendance_result[0], attendance_result[2])
                        )
                        conn.commit()
                        recognized_faces.append({'name':attendee_name, 'id':attendee_id, 'state':'out', 'current_time':current_time, 'category':'manual'})
                
                elif isinstance(create_datetime(attendance_result[4], attendance_result[5]), datetime):
                    attendee_dt = create_datetime(attendance_result[4], attendance_result[6])
                    diff = datetime.now() - attendee_dt

                    if diff.total_seconds() > duration:
                        mysql_cursor.execute(
                            """INSERT INTO attendance 
                            (attendee_name, attendee_id, device, date, check_in, check_out)
                            VALUES (%s,%s,%s,%s,%s,%s)""",
                            (attendee_name, attendee_id, device, datetime.now().date(), datetime.now().time(), None) 
                        )
                        conn.commit()
                        recognized_faces.append({'name':attendee_name, 'id':attendee_id, 'state':'in', 'current_time':current_time, 'category':'manual'})

            else:
                '''If no rocord is found'''
                # check type : 0
                mysql_cursor.execute(
                    """INSERT INTO attendance 
                    (attendee_name, attendee_id, device, date, check_in, check_out)
                    VALUES (%s,%s,%s,%s,%s,%s)""",
                    (attendee_name, attendee_id, device, datetime.now().date(), datetime.now().time(), None) 
                )
                conn.commit()
                recognized_faces.append({'name':attendee_name, 'id':attendee_id, 'state':'in', 'current_time':current_time, 'category':'manual'})
    
        else:
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
            # try:
                guest_matches_id = np.argmin(guest_face_dict)
                # print('guest id', guest_matches_id )

                if guest_matches[guest_matches_id]:
                    guest_attendee_id = guest_attendee_ids[guest_matches_id]

                    mysql_cursor.execute("""SELECT * FROM guest_attendance 
                                            WHERE guest_attendee_id = %s AND date = %s ORDER BY check_in DESC""",
                                            (guest_attendee_id, datetime.now().date())
                                        )
                    guest_attendance_result = mysql_cursor.fetchone()

                    if guest_attendance_result:
                        if guest_attendance_result[6] is None:
                            guest_attendee_dt = create_datetime(guest_attendance_result[4], guest_attendance_result[5])

                            diff = datetime.now()- guest_attendee_dt
                            if diff.total_seconds() > duration:
                                mysql_cursor.execute("""UPDATE guest_attendance SET check_out = %s WHERE 
                                guest_attendee_id = %s  AND check_out IS NULL ORDER BY guest_attendee_id DESC LIMIT 1""",
                                (current_time, guest_attendance_result[1])
                                )
                                conn.commit()
                                # # Retrieve the updated row
                                # mysql_cursor.execute("SELECT * FROM guest_attendance WHERE guest_attendee_id = %s", (guest_attendance_result[0],))
                                # updated_row = mysql_cursor.fetchone()

                                # # Print the updated row
                                # print("updated_rows",  updated_row)

                                recognized_faces.append({
                                    'state':'out', 
                                    'category':'guest', 
                                    'image': cropped_face, 
                                    'id':guest_attendee_id
                                })
                                
                        elif isinstance(create_datetime(guest_attendance_result[4], guest_attendance_result[5]), datetime):
                                guest_attendee_dt = create_datetime(guest_attendance_result[4], guest_attendance_result[6])
                                diff = datetime.now() - guest_attendee_dt

                                if diff.total_seconds() > duration:
                                    mysql_cursor.execute(
                                        """INSERT INTO guest_attendance(guest_attendee_id, guest_name, device, date, check_in, check_out)
                                        VALUES (%s,%s,%s,%s,%s,%s)""",
                                        (guest_attendee_id, None, device, datetime.now().date(), datetime.now().time(),None)
                                    )
                                    conn.commit()
                                    recognized_faces.append({
                                        'state':'in', 
                                        'category':'guest', 
                                        'image': cropped_face, 
                                        'id':guest_attendee_id
                                    })

                    else: 
                        mysql_cursor.execute(
                                """INSERT INTO guest_attendance(guest_attendee_id, guest_name, device, date, check_in, check_out)
                                VALUES (%s,%s,%s,%s,%s,%s)""",
                                (guest_attendee_id, None, device, datetime.now().date(), datetime.now().time(),None)
                            )
                        conn.commit()
                        recognized_faces.append({
                            'state':'in', 
                            'category':'guest', 
                            'image' : cropped_face,
                            'id':guest_attendee_id
                        })

                else:
                    '''registration of guest for guest table with data'''
                    guest_attendee_id, guest_name, image_base64, encoded_face_encoding, created_on= register_guest_attendee(cropped_face, encode_face)

                    insert_guest_registration(mysql_cursor, guest_attendee_id, guest_name, image_base64, encoded_face_encoding, created_on)
                    guest_stored_encoding.append(encode_face)
                    guest_attendee_ids.append(guest_attendee_id)
                    
                    mysql_cursor.execute(
                        """INSERT INTO guest_attendance(guest_attendee_id, guest_name, device, date, check_in, check_out)
                        VALUES (%s,%s,%s,%s,%s,%s)""",
                        (guest_attendee_id, None, device,datetime.now().date(), datetime.now().time(),None)
                    )
                    conn.commit()
                    recognized_faces.append({
                        'state':'in_new', 
                        'category':'guest', 
                        'image': cropped_face,
                        'id':guest_attendee_id
                        })
            # except Exception as e:
            #     print(e)
            else:
                '''registration of guest for empty guest table'''
                guest_attendee_id, guest_name, image_base64, encoded_face_encoding, created_on= register_guest_attendee(cropped_face, encode_face)
                
                insert_guest_registration(mysql_cursor, guest_attendee_id, guest_name, image_base64, encoded_face_encoding, created_on)
                guest_stored_encoding.append(encode_face)
                guest_attendee_ids.append(guest_attendee_id)
                
                mysql_cursor.execute(
                    """INSERT INTO guest_attendance(guest_attendee_id, guest_name, device, date, check_in, check_out)
                    VALUES (%s,%s,%s,%s,%s,%s)""",
                    (guest_attendee_id, None, device,datetime.now().date(), datetime.now().time(),None)
                )
                conn.commit()
                recognized_faces.append({'state':'in_new', 'category':'guest', 'image': cropped_face})
                print('sucessful insert')

    # except Exception as e:
    #     print(f"Exception: \n{e}")
    #     pass
    mysql_cursor.close()
    return recognized_faces, guest_stored_encoding, guest_attendee_ids



