# python3 /home/pi/Desktop/car-iot.py
import time
import pyrebase
import cv2
import dlib
import imutils
import random
from imutils import face_utils
from scipy.spatial import distance as dist
import RPi.GPIO as GPIO
from threading import Thread

# INPUT PINS INITIALIZATION
GPIO.setmode(GPIO.BCM)
motor_pin = 22
acc_pin1 = 2
acc_pin2 = 3
acc_pin3 = 4
brake_pin1 = 14
brake_pin2 = 15
brake_pin3 = 18
seatbelt_pin = 17
bpm_pin = 27

GPIO.setup(motor_pin, GPIO.OUT)
GPIO.setup(acc_pin1, GPIO.IN)
GPIO.setup(acc_pin2, GPIO.IN)
GPIO.setup(acc_pin3, GPIO.IN)
GPIO.setup(brake_pin1, GPIO.IN)
GPIO.setup(brake_pin2, GPIO.IN)
GPIO.setup(brake_pin3, GPIO.IN)
GPIO.setup(seatbelt_pin, GPIO.IN)
GPIO.setup(bpm_pin, GPIO.IN)

FACIAL_LANDMARK_PREDICTOR = "/home/pi/mu_code/shape_predictor_68_face_landmarks.dat"
MINIMUM_EAR = 0.2
MAXIMUM_FRAME_COUNT = 10

faceDetector = dlib.get_frontal_face_detector()
landmarkFinder = dlib.shape_predictor(FACIAL_LANDMARK_PREDICTOR)
webcamFeed = cv2.VideoCapture(0)

(leftEyeStart, leftEyeEnd) = face_utils.FACIAL_LANDMARKS_IDXS["left_eye"]
(rightEyeStart, rightEyeEnd) = face_utils.FACIAL_LANDMARKS_IDXS["right_eye"]

def eye_aspect_ratio(eye):
    p2_minus_p6 = dist.euclidean(eye[1], eye[5])
    p3_minus_p5 = dist.euclidean(eye[2], eye[4])
    p1_minus_p4 = dist.euclidean(eye[0], eye[3])
    ear = (p2_minus_p6 + p3_minus_p5) / (2.0 * p1_minus_p4)
    return ear

EYE_CLOSED_COUNTER = 0

config = {
  "apiKey": "AIzaSyCXw8rIHYKQvDsXaK8CCm2-7L5PamYbBXQ",
  "authDomain": "iot-car-dashboard-b5e3a.firebaseapp.com",
  "databaseURL": "https://iot-car-dashboard-b5e3a-default-rtdb.firebaseio.com/",
  "storageBucket": "iot-car-dashboard-b5e3a.appspot.com",
  "projectId": "iot-car-dashboard-b5e3a",
  "messagingSenderId": "your-messaging-sender-id",
  "appId": "your-app-id"
}

firebase = pyrebase.initialize_app(config)
db = firebase.firestore()  # Use firestore() instead of database()

print("Send Data to Firestore Using Raspberry Pi")
print("----------------------------------------")
print()

seatbelt = False
bpm = 0
acc = "low"
brake = "low"

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
    while True:
        if((GPIO.input(acc_pin1) == 1) and (GPIO.input(acc_pin2) == 0) and (GPIO.input(acc_pin3) == 0)):
            acc = "low"
        elif((GPIO.input(acc_pin1) == 1) and (GPIO.input(acc_pin2) == 1) and (GPIO.input(acc_pin3) == 0)):
            acc = "med"
        elif((GPIO.input(acc_pin1) == 1) and (GPIO.input(acc_pin2) == 1) and (GPIO.input(acc_pin3) == 1)):
            acc = "high"
        elif((GPIO.input(acc_pin1) == 0) and (GPIO.input(acc_pin2) == 0) and (GPIO.input(acc_pin3) == 0)):
            acc = "idle"

        if((GPIO.input(brake_pin1) == 1) and (GPIO.input(brake_pin2) == 0) and (GPIO.input(brake_pin3) == 0)):
            brake = "low"
        elif((GPIO.input(brake_pin1) == 1) and (GPIO.input(brake_pin2) == 1) and (GPIO.input(brake_pin3) == 0)):
            brake = "med"
        elif((GPIO.input(brake_pin1) == 1) and (GPIO.input(brake_pin2) == 1) and (GPIO.input(brake_pin3) == 1)):
            brake = "high"
        elif((GPIO.input(brake_pin1) == 0) and (GPIO.input(brake_pin2) == 0) and (GPIO.input(brake_pin3) == 0)):
            brake = "idle"

        if(GPIO.input(seatbelt_pin) == 0):
            seatbelt = True
            GPIO.output(motor_pin, False)
        elif(GPIO.input(seatbelt_pin) == 1):
            seatbelt = False
            GPIO.output(motor_pin, True)

        if(GPIO.input(bpm_pin) == 0):
            bpm = random.randint(72, 81)
        elif(GPIO.input(bpm_pin) == 1):
            bpm = 0

        data = {
            "ear": earCalculation.ear_val,
            "seatbelt": seatbelt,
            "bpm" : bpm,
            "acceleration" : acc,
            "brake" : brake,
        }

        print(data)

        db.collection("sensor-values").add(data)
        time.sleep(2)

if _name_ == '_main_':
    Thread(target=earCalculation).start()
    Thread(target=parametersCalculation).start()
