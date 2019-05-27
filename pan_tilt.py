import RPi.GPIO as GPIO
import time
from UDPComms import Subscriber, timeout

pan_pin = 14
tilt_pin = 4

GPIO.setmode(GPIO.BCM)
GPIO.setup(pan_pin, GPIO.OUT)
GPIO.setup(tilt_pin, GPIO.OUT)

pan = GPIO.PWM(pan_pin, 50)
tilt = GPIO.PWM(tilt_pin, 50)

pan.start(7.5)
tilt.start(7.5)

sub = Subscriber(8120, timeout=1)

time.sleep(1)

pan_angle = 0
tilt_angle = 0

def clamp(x,ma,mi):
    if x > ma:
        return ma
    elif x < mi:
        return mi
    else:
        return x

while True:
    time.sleep(0.1)
    changed = False
    try:
        msg = sub.get()
        pan_angle = clamp(pan_angle + msg['pan'], 90, -90)
        tilt_angle = clamp(tilt_angle + msg['tilt'], 90, -24)
        if (msg['pan'] != 0) or (msg['tilt'] != 0):
            changed = True
    except timeout:
        pass

    if changed:
        pan.ChangeDutyCycle(7.5 + pan_angle*5.5/90)
        tilt.ChangeDutyCycle(8.5 - tilt_angle*5.5/90)
    else:
        pan.ChangeDutyCycle(0)
        tilt.ChangeDutyCycle(0)

