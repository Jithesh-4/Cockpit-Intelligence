import time
import firebase_admin
import RPi.GPIO as GPIO
import cv2
import dlib
import imutils
import random
from imutils import face_utils
from scipy.spatial import distance as dist
from threading import Thread
from firebase_admin import credentials, initialize_app, db


# INPUT PINS INITIALIZATION
GPIO.setmode(GPIO.BCM)
# accelaration
acc_pin1 = 2
acc_pin2 = 3
# brake pins
brake_pin1 = 4
brake_pin2 = 18
# seat belt
seatbelt_pin = 17
# BPM
bpm_pin = 27
# steering
steering_pin = 9
# left - right - in
left_in_pin = 5
right_in_pin = 0
# headlight in
headlight_in_pin = 6
# gear
gear_pin1 = 20
gear_pin2 = 21
# cornering
cornering_pin1 = 16
cornering_pin2 = 12
# sudden break
sudden_break_pin = 10
# horn
horn_pin = 27
# beep out
beep_out_pin = 22
# headlight out
headlight_out_pin = 8
# left - right - out
left_out_pin = 24
right_out_pin = 25


# outputs
GPIO.setup(beep_out_pin, GPIO.OUT)
GPIO.setup(headlight_out_pin, GPIO.OUT)
GPIO.setup(left_out_pin, GPIO.OUT)
GPIO.setup(right_out_pin, GPIO.OUT)
# inputs
GPIO.setup(acc_pin1, GPIO.IN)
GPIO.setup(acc_pin2, GPIO.IN)
GPIO.setup(brake_pin1, GPIO.IN)
GPIO.setup(brake_pin2, GPIO.IN)
GPIO.setup(seatbelt_pin, GPIO.IN)
GPIO.setup(steering_pin, GPIO.IN)
GPIO.setup(left_in_pin, GPIO.IN)
GPIO.setup(right_in_pin, GPIO.IN)
GPIO.setup(headlight_in_pin, GPIO.IN)
GPIO.setup(gear_pin1, GPIO.IN)
GPIO.setup(gear_pin2, GPIO.IN)
GPIO.setup(cornering_pin1, GPIO.IN)
GPIO.setup(cornering_pin2, GPIO.IN)
GPIO.setup(sudden_break_pin, GPIO.IN)
GPIO.setup(horn_pin, GPIO.IN)

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



cred = credentials.Certificate("/home/pi/Desktop/Cockpit-Intelligence/cockpit-intelligence-firebase-adminsdk-a7ryd-7da4f325ef.json")
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
    seatbelt = False
    steering = False
    left_in = False
    right_in = False
    headlightin = False
    gear = "idle"
    cornering = "idle"
    sudden_break = "low"
    horn = "low"

    while True:
        # acc calc
        if((GPIO.input(acc_pin1) == 0) and (GPIO.input(acc_pin2) == 1)):
            acc = "low"
        elif((GPIO.input(acc_pin1) == 1) and (GPIO.input(acc_pin2) == 0)):
            acc = "med"
        elif((GPIO.input(acc_pin1) == 1) and (GPIO.input(acc_pin2) == 1)):
            acc = "high"
        elif((GPIO.input(acc_pin1) == 0) and (GPIO.input(acc_pin2) == 0)):
            acc = "idle"

        # brake calc
        if((GPIO.input(brake_pin1) == 0) and (GPIO.input(brake_pin2) == 1)):
            brake = "low"
        elif((GPIO.input(brake_pin1) == 1) and (GPIO.input(brake_pin2) == 0)):
            brake = "med"
        elif((GPIO.input(brake_pin1) == 1) and (GPIO.input(brake_pin2) == 1)):
            brake = "high"
        elif((GPIO.input(brake_pin1) == 0) and (GPIO.input(brake_pin2) == 0)):
            brake = "idle"

        # seatbelt calc
        if(GPIO.input(seatbelt_pin) == 1):
            seatbelt = True
        elif(GPIO.input(seatbelt_pin) == 0):
            seatbelt = False

        # steering calc
        if(GPIO.input(steering_pin) == 1):
            steering = True
        elif(GPIO.input(steering_pin) == 0):
            steering = False

        # left-in calc
        if(GPIO.input(left_in_pin) == 0):
            left_in = False
        elif(GPIO.input(left_in_pin) == 1):
            left_in = True

        # right-in calc
        if(GPIO.input(right_in_pin) == 0):
            right_in = False
        elif(GPIO.input(right_in_pin) == 1):
            right_in = True

        # headlight in calc
        if(GPIO.input(headlight_in_pin) == 1):
            headlightin = True
        elif(GPIO.input(headlight_in_pin) == 0):
            headlightin = False

        # gear calc
        if((GPIO.input(gear_pin1) == 0) and (GPIO.input(gear_pin2) == 1)):
            gear = "low"
        elif((GPIO.input(gear_pin1) == 1) and (GPIO.input(gear_pin2) == 0)):
            gear = "high"
        elif((GPIO.input(gear_pin1) == 0) and (GPIO.input(gear_pin2) == 0)):
            gear = "idle"

        # cornering calc
        if((GPIO.input(cornering_pin1) == 0) and (GPIO.input(cornering_pin2) == 1)):
            cornering = "low"
        elif((GPIO.input(cornering_pin1) == 1) and (GPIO.input(cornering_pin2) == 0)):
            cornering = "high"
        elif((GPIO.input(cornering_pin1) == 0) and (GPIO.input(cornering_pin2) == 0)):
            cornering = "idle"
        
        # seatbelt calc
        if(GPIO.input(sudden_break_pin) == 1):
            sudden_break = True
        elif(GPIO.input(sudden_break_pin) == 0):
            sudden_break = False
        
        # horn calc
        if(GPIO.input(horn_pin) == 1):
            horn = True
        elif(GPIO.input(horn_pin) == 0):
            horn = False
        
        # beep out
        if(GPIO.input(horn_pin) == 1):
            GPIO.output(beep_out_pin, GPIO.HIGH)
        elif(GPIO.input(horn_pin) == 0):
            GPIO.output(beep_out_pin, GPIO.LOW)
        
        # headlight out
        if(GPIO.input(headlight_in_pin) == 1):
            GPIO.output(headlight_out_pin, GPIO.HIGH)
        elif(GPIO.input(headlight_in_pin) == 0):
            GPIO.output(headlight_out_pin, GPIO.LOW)
        
        # left-in calc
        if(GPIO.input(left_in_pin) == 1):
            GPIO.output(left_out_pin, GPIO.HIGH)
        elif(GPIO.input(left_in_pin) == 0):
            GPIO.output(left_out_pin, GPIO.LOW)

        # right-in calc
        if(GPIO.input(right_in_pin) == 1):
            GPIO.output(right_out_pin, GPIO.HIGH)
        elif(GPIO.input(right_in_pin) == 0):
            GPIO.output(right_out_pin, GPIO.LOW)


        '''ref.child("ear").set(earCalculation.ear_val)
        ref.child("acceleration").set(acc)
        ref.child("brake").set(brake)
        ref.child("seatbelt").set(seatbelt)
        ref.child("steering").set(steering)
        ref.child("left_in").set(left_in)
        ref.child("right_in").set(right_in)
        ref.child("headlight").set(headlightin)
        ref.child("gear").set(gear)
        ref.child("cornering").set(cornering)
        ref.child("sudden break").set(sudden_break)
        ref.child("horn").set(horn)
        time.sleep(1)'''

        data={
      "ear":earCalculation.ear_val,
      "acceleration":acc,
      "brake":brake,
      "seatbelt":seatbelt,
      "steering":steering,
      "left_in":left_in,
      "right_in":right_in,
      "headlight":headlightin,
      "gear":gear,
      "cornering":cornering,
      "sudden break":sudden_break,
      "horn":horn
        }
        print(data)
        ref.child("sensorvalues").set(data)

if _name_ == '_main_':
    earCalculation()
    parametersCalculation()
