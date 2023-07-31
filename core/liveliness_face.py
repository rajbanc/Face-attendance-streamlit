import cv2
import tensorflow as tf
import numpy as np


def frontalfacedetector(image, frontal_face_detector):
    height, width, _ = image.shape
    output_image = image.copy()
    # print("output", output_image)

    results = frontal_face_detector(output_image)
    face_coordinates = []
    pad_size = 25
    num_faces = len(results)
    for i in range(num_faces):
        bbox = results[i]
        # print(bbox)
    # for bbox in results:
    #     print('boxz', bbox)
        x1, y1, x2, y2 = bbox.left(),bbox.top(), bbox.right(), bbox.bottom()
        # w, h, _ = output_image.shape 
        # print('x1,y1,x2,y2: ', x1,y1,x2,y2)
        x1 = max(0, int(x1)-pad_size)
        y1 = max(0, int(y1)-pad_size)
        x2 = min(width, int(x2)+pad_size + 5)
        y2 = min(height, int(y2)+pad_size + 5)
        coordinate = [x1, y1, x2-x1, y2-y1]
        face_coordinates.append(tuple(coordinate))
        cv2.rectangle(output_image,(x1,y1),(x2,y2),(0,255,0),2)
    return face_coordinates, output_image

def check_liveliness(img, liveliness_model, labels,frontal_face_detector):
    frm = img.copy()

    frm = cv2.cvtColor(frm, cv2.COLOR_BGR2RGB)
    face_coordinates, image = frontalfacedetector(frm, frontal_face_detector)
    real_face_bboxes = []
    for (x1, y1, w, h) in face_coordinates:
        x2 = x1 + w
        y2 = y1 + h

        face = frm[y1:y2, x1:x2]
        is_valid_face = check_aspect_ratio(face)
        print(f"{is_valid_face=}")
        try:
            face = cv2.resize(face,(32,32))
        except:
            continue
        face = face.astype('float') / 255.0
        face = tf.keras.preprocessing.image.img_to_array(face)
        # print(f"shape of face {face.shape}")
        face = np.expand_dims(face, axis=0)

        preds =liveliness_model.predict(face)[0]
        j = np.argmax(preds)
        label_name = labels.classes_[j]

        label = f'{label_name}: {preds[j]:.4f}'
        # print(f'[INFO] {name}, {label_name}')

        if label_name == 'real' and is_valid_face:
            name = 'Approved'
            box = [x1,y1,w,h]
            real_face_bboxes.append(box)
        else:
            name = 'Not Approved'
            cv2.putText(img, name, (x1, y2 + 25),
                        cv2.FONT_HERSHEY_COMPLEX, 0.5, (70, 0, 255), 2)
        # print('box-'*5, len(real_face_bboxes))
        cv2.putText(img, name, (x1, y1 - 35), cv2.FONT_HERSHEY_COMPLEX, 0.5, (100, 130, 255), 2)
        cv2.putText(img, label, (x1, y1 - 10),
                    cv2.FONT_HERSHEY_COMPLEX, 0.5, (200, 0, 160), 2)
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 255), 1)
    return img, real_face_bboxes

def check_aspect_ratio(face_image):
    height, width =face_image.shape[:2]
    ar = width/height
    if 0.8 <= ar <= 1.25:
        return True
    return False
