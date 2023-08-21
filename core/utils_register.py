import json
import numpy as np
import face_recognition

stored_encodings = None
attendee_names = None
attendee_ids = None

def get_registration_data(mysql_cursor):
    mysql_cursor.execute("SELECT * FROM manual_registration")
    data = mysql_cursor.fetchall()
    # print('data', data)
    return data

def get_guest_register_data(mysql_cursor):
    mysql_cursor.execute("SELECT * FROM guest_registration")
    data = mysql_cursor.fetchall()
    return data

def get_checkinout_data(mysql_cursor):
    mysql_cursor.execute('SELECT * FROM checkinout')
    data = mysql_cursor.fetchall()
    print('data of checkinout', data)
    return data

def get_userinfo_data(mysql_cursor):
    mysql_cursor.execute('SELECT userid FROM userinfo ORDER BY userid DESC')
    try:
        last_userid = mysql_cursor.fetchone()[0]
        return last_userid + 1
    except:
        return 1

def get_user_data(mysql_cursor):
    reg = get_registration_data(mysql_cursor)
    stored_encodings = []
    attendee_names = []
    attendee_ids = []
    for row in reg:
        attendee_name = row[1]
        userid = row[2]
        face_embeddings = row[5] #['face_embedding']
        if isinstance(face_embeddings, bytes):
            face_embeddings = str(face_embeddings, encoding='utf-8')
        elif isinstance(face_embeddings, str):
            face_embeddings = str(face_embeddings)
        else:
            raise TypeError("Type should be string or bytes")
        face_embeddings = json.loads(face_embeddings)
        face_embeddings = face_embeddings['face_embedding']
        # use for loop to extract each of the face embedding of different positions
        for face_embedding in face_embeddings:
            decoded_face_embedding = np.asarray(face_embedding)

            stored_encodings.append(decoded_face_embedding)
            attendee_names.append(attendee_name)
            attendee_ids.append(userid)
    return stored_encodings, attendee_names, attendee_ids

def get_guest_data(mysql_cursor):
    guest = get_guest_register_data(mysql_cursor)
    guest_stored_encodings = []
    guest_names = []
    guest_attendee_ids = []
    for row in guest:
        guest_name = row[2]
        guest_userid = row[1]
        face_embeddings = row[4]
        if isinstance(face_embeddings, bytes):
            face_embeddings = str(face_embeddings, encoding='utf-8')
        elif isinstance(face_embeddings, str):
            face_embeddings = str(face_embeddings)
        else:
            raise TypeError("Type should be string or bytes")
        face_embedding = json.loads(str(face_embeddings))
        face_embedding = face_embedding['face_embedding']
        decoded_face_embedding = np.asarray(face_embedding)
        decoded_face_embedding = decoded_face_embedding.flatten()

        guest_stored_encodings.append(decoded_face_embedding)
        guest_names.append(guest_name)
        guest_attendee_ids.append(guest_userid)
    return guest_stored_encodings, guest_names, guest_attendee_ids

def face_registration(image, face_crop, mysql_cursor):
    stored_encodings, attendee_names, attendee_ids = get_user_data(mysql_cursor)

     # CHANGE INTO FACE RECOGNITION FORMAT
    face_cropped  = [(face[1], face[0] + face[2], face[1] + face[3], face[0]) for face in face_crop]

    encoded_face_in_frame = face_recognition.face_encodings(image, face_cropped)
    ret_val = [] 
    for encode_face, face_loc in zip(encoded_face_in_frame, face_cropped):
        stored_encodings = np.array(stored_encodings)
        matches = face_recognition.compare_faces(stored_encodings, encode_face, tolerance= 0.45)
        print('matches ', matches)
        face_dist = face_recognition.face_distance(stored_encodings, encode_face)
        print('face_dist ',face_dist)
        try:
            match_index = np.argmin(face_dist)
            print(match_index)
            print('matches[match_index] ', matches[match_index])
            if matches[match_index]:
                name = attendee_names[match_index].upper()
                id = attendee_ids[match_index]
                dist = face_dist[match_index]
                ret_val.append([name, id])
        except:
            print("Face not found in database")
    print('ret_val: ', ret_val)
    print('encoded_face_in_frame: ', encoded_face_in_frame)

    if len(encoded_face_in_frame) > 0:
        return ret_val, encoded_face_in_frame[0]
    return False, False
