import time
#import pyrebase
import RPi.GPIO as GPIO
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



cred = credentials.Certificate("/home/pi/Desktop/pmain/predictive-maintainence-1841d-firebase-adminsdk-oejc1-37178fae8b.json")
firebase_app = initialize_app(cred, {"databaseURL": "https://cockpit-intelligence-default-rtdb.firebaseio.com/"})
ref = db.reference("/")


print("Send Data to Firebase Using Raspberry Pi")
print("----------------------------------------")
print()



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
