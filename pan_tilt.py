import RPi.GPIO as GPIO
import time
from UDPComms import Subscriber

pan_pin = 2
tilt_pin = 3

GPIO.setmode(GPIO.BCM)
GPIO.setup(pan_pin, GPIO.OUT)
GPIO.setup(tilt_pin, GPIO.OUT)

pan = GPIO.PWM(pan_pin, 50)
tilt = GPIO.PWM(tilt_pin, 50)

pan.start(7.5)
tilt.start(7.5)

sub = Subscriber(9999, timeout=1)

time.sleep(1)

def clamp(x,ma,mi):
    if x > ma:
        return ma
    elif x < mi:
        return mi
    else:
        return x

while True:
    time.sleep(0.1)
    msg = sub.get()

    pan_angle = clamp(msg['pan'], 90, -90)
    tilt_angle = clamp(msg['tilt'], 90, -24)

    pan.ChangeDutyCycle(7.5 + pan_angle*5.5/90)
    tilt.ChangeDutyCycle(8.5 - tilt_angle*5.5/90)

    pass
