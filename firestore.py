import time
import firebase_admin
import RPi.GPIO as GPIO
import cv2
import dlib
import imutils
import random
from imutils import face_utils
from scipy.spatial import distance as dist
import RPi.GPIO as GPIO
from threading import Thread
from threading import Thread
from firebase_admin import credentials, initialize_app, db


# INPUT PINS INITIALIZATION
GPIO.setmode(GPIO.BCM)
# accelaration
acc_pin1 = 2
acc_pin2 = 3
acc_pin3 = 4
# brake pins
brake_pin1 = 14
brake_pin2 = 15
brake_pin3 = 18



# inputs
GPIO.setup(acc_pin1, GPIO.IN)
GPIO.setup(acc_pin2, GPIO.IN)
GPIO.setup(acc_pin3, GPIO.IN)
GPIO.setup(brake_pin1, GPIO.IN)
GPIO.setup(brake_pin2, GPIO.IN)
GPIO.setup(brake_pin3, GPIO.IN)

#
FACIAL_LANDMARK_PREDICTOR = "/home/pi/Desktop/Cockpit-Intelligence/shape_predictor_68_face_landmarks.dat"  # path to dlib's pre-trained facial landmark predictor
MINIMUM_EAR = 0.2    # Minimum EAR for both the eyes to mark the eyes as open
MAXIMUM_FRAME_COUNT = 10

#Initializations
faceDetector = dlib.get_frontal_face_detector()     # dlib's HOG based face detector
landmarkFinder = dlib.shape_predictor(FACIAL_LANDMARK_PREDICTOR)  # dlib's landmark finder/predcitor inside detected face
webcamFeed = cv2.VideoCapture(0)

# Finding landmark id for left and right eyes
(leftEyeStart, leftEyeEnd) = face_utils.FACIAL_LANDMARKS_IDXS["left_eye"]
(rightEyeStart, rightEyeEnd) = face_utils.FACIAL_LANDMARKS_IDXS["right_eye"]

def eye_aspect_ratio(eye):
    p2_minus_p6 = dist.euclidean(eye[1], eye[5])
    p3_minus_p5 = dist.euclidean(eye[2], eye[4])
    p1_minus_p4 = dist.euclidean(eye[0], eye[3])
    ear = (p2_minus_p6 + p3_minus_p5) / (2.0 * p1_minus_p4)
    return ear

EYE_CLOSED_COUNTER = 0



cred = credentials.Certificate("/home/pi/Desktop/Cockpit-Intelligence/cockpit-intelligence-firebase-adminsdk-a7ryd-509f7a433c.json")
firebase_app = initialize_app(cred, {"databaseURL": "https://cockpit-intelligence-default-rtdb.firebaseio.com/"})
ref = db.reference("/")


print("Send Data to Firebase Using Raspberry Pi")
print("----------------------------------------")
print()


def earCalculation():
    earCalculation.ear_val = 0
    while True:
        (status, image) = webcamFeed.read()
        image = imutils.resize(image, width=800)
        grayImage = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        faces = faceDetector(grayImage, 0)

        for face in faces:
            faceLandmarks = landmarkFinder(grayImage, face)
            faceLandmarks = face_utils.shape_to_np(faceLandmarks)

            leftEye = faceLandmarks[leftEyeStart:leftEyeEnd]
            rightEye = faceLandmarks[rightEyeStart:rightEyeEnd]

            leftEAR = eye_aspect_ratio(leftEye)
            rightEAR = eye_aspect_ratio(rightEye)

            ear = (leftEAR + rightEAR) / 2.0
            earCalculation.ear_val = ear

            leftEyeHull = cv2.convexHull(leftEye)
            rightEyeHull = cv2.convexHull(rightEye)

            cv2.drawContours(image, [leftEyeHull], -1, (255, 0, 0), 2)
            cv2.drawContours(image, [rightEyeHull], -1, (255, 0, 0), 2)

            if ear < MINIMUM_EAR:
                EYE_CLOSED_COUNTER += 1
            else:
                EYE_CLOSED_COUNTER = 0

            cv2.putText(image, "EAR: {}".format(round(ear, 1)), (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

            if EYE_CLOSED_COUNTER >= MAXIMUM_FRAME_COUNT:
                cv2.putText(image, "Drowsiness", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        cv2.imshow("Frame", image)
        cv2.waitKey(1)


def parametersCalculation():
    acc = "low"
    brake = "low"

    while True:
        # acc calc
        if((GPIO.input(acc_pin1) == 1) and (GPIO.input(acc_pin2) == 0) and (GPIO.input(acc_pin3) == 0)):
            acc = "low"
        elif((GPIO.input(acc_pin1) == 1) and (GPIO.input(acc_pin2) == 1) and (GPIO.input(acc_pin3) == 0)):
            acc = "med"
        elif((GPIO.input(acc_pin1) == 1) and (GPIO.input(acc_pin2) == 1) and (GPIO.input(acc_pin3) == 1)):
            acc = "high"
        elif((GPIO.input(acc_pin1) == 0) and (GPIO.input(acc_pin2) == 0) and (GPIO.input(acc_pin3) == 0)):
            acc = "idle"
        #print(acc)

        # brake calc
        if((GPIO.input(brake_pin1) == 1) and (GPIO.input(brake_pin2) == 0) and (GPIO.input(brake_pin3) == 0)):
            brake = "low"
        elif((GPIO.input(brake_pin1) == 1) and (GPIO.input(brake_pin2) == 1) and (GPIO.input(brake_pin3) == 0)):
            brake = "med"
        elif((GPIO.input(brake_pin1) == 1) and (GPIO.input(brake_pin2) == 1) and (GPIO.input(brake_pin3) == 1)):
            brake = "high"
        elif((GPIO.input(brake_pin1) == 0) and (GPIO.input(brake_pin2) == 0) and (GPIO.input(brake_pin3) == 0)):
            brake = "idle"


        data = {
            "acceleration" : acc,
            "brake" : brake,
        
        }

        print(data)

        db.child("sensor-values").set(data)
        time.sleep(2)

if __name__ == '__main__':
    Thread(target = earCalculation).start()
    Thread(target = parametersCalculation).start()
