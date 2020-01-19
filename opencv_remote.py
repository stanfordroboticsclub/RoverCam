import shlex
import os
import subprocess
import UDPComms
import re

from imutils.video import VideoStream, FileVideoStream
import cv2

from enum import Enum
import time

REQUEST_PORT = 5000
class Server:
    INPUT = Enum("INPUT", "RPI_CAM USB_CAM OPENCV")
    def __init__(self, mode = None):
        if mode == None:
            mode = self.INPUT.RPI_CAM
        self.mode = mode

        self.sub = UDPComms.Subscriber(REQUEST_PORT)
        self.hostname = subprocess.run('hostname', stdout=subprocess.PIPE).stdout.strip().decode("utf-8")
        self.process = None

    def listen(self):
        """" block until connection from viewer """
        print("looking for ", self.hostname)
        while 1:
            try:
                msg = self.sub.recv()
                print("get msg: ", msg)
            except UDPComms.timeout:
                pass
            else:
                print("got", msg['host'])
                if msg['host'] ==  self.hostname:
                    time.sleep(1)
                    if self.mode == self.INPUT.OPENCV:
                        self.init_imshow( msg["port"] , msg["ip"] )
                    elif self.mode == self.INPUT.RPI_CAM:
                        self.run_rpi( msg["port"] , msg["ip"] )
                    elif self.mode == self.INPUT.USB_CAM:
                        self.run_usb( msg["port"] , msg["ip"] )

                    break

    """ display new image array on remote viewer """
    def imshow(self, name, img):
        if self.mode != self.INPUT.OPENCV or self.process is None:
            print("Error")
            return

        self.process.stdin.write(cv2.cvtColor(img, cv2.COLOR_BGR2YUV_I420))



    def init_imshow(self, port, host):
        # works
        args = shlex.split(('gst-launch-1.0 fdsrc ! videoparse format="i420" width=320 height=240' +
                            ' ! x264enc speed-preset=1 tune=zerolatency bitrate=1000000' +
                            ' ! rtph264pay config-interval=1 pt=96 ! udpsink host={} port={}').format(host, port))
        self.process = subprocess.Popen(args, stdin=subprocess.PIPE)

    def run_rpi(self, port, host):
        # works (no gdppay)
        arg = "raspivid -fps 26 -h 1280 -w 720 -md 6 -n -t 0 -b 1000000 -o -" +\
              " | gst-launch-1.0 fdsrc ! 'video/x-h264,width=1280,height=720,framerate=45/1,profile=high'" +\
              " ! h264parse ! queue ! rtph264pay pt=96 ! udpsink host={} port={}".format(host,port)
        args = shlex.split(arg)

        self.process = subprocess.Popen(args, shell=True)
        self.process.wait()
        print("video process died")



    def run_usb(self, port, host):
        pass

class RemoteViewer:
    OUTPUT = Enum("OUPUT", "OPENCV WINDOW")

    def get_my_ip(self):
        # capture_output is only in python 3.7 and above
        a = subprocess.run('ifconfig',capture_output=1)
        m = re.search( b"10\.0\.0\.[1-9][0-9]{0,2}", a.stdout)
        if m is not None:
            return m.group()
        else:
            print("Can't find my ip on robot network!")
            return None

    def __init__(self, mode = None):
        if mode == None:
            mode = self.OUTPUT.WINDOW
        self.mode = mode
        self.pub = UDPComms.Publisher(REQUEST_PORT)
        self.ip = self.get_my_ip()
        self.process = None

    def stream(self, hostname):
        port = 5001
        self.pub.send({"ip": self.ip, "host": hostname, "resolution": (320,240), "port":port})

        if self.mode == self.OUTPUT.WINDOW:
            cmd = 'gst-launch-1.0 udpsrc port={} caps="application/x-rtp" ! rtph264depay ! avdec_h264 ! autovideosink'.format(port)
            args = shlex.split(cmd)
            # shell = True need to open a window. $DISPLAY needs to be set?
            # print(args)
            # self.process = subprocess.Popen(cmd, shell=True)
            self.process = subprocess.Popen(args)
            while (1):
                pass

        elif self.mode == self.OUTPUT.OPENCV:
            cmd = 'gst-launch-1.0 udpsrc port={} caps="application/x-rtp" ! rtph264depay ! avdec_h264 ! fdsink'
            return imutils.FileVideoStream(cmd).start()

import argparse
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('op', choices=['server', 'viewer'])
    args = parser.parse_args()

    if args.op == "server":
        s = Server()
        s.listen()

    elif args.op == "viewer":
        r = RemoteViewer()
        r.stream("acrocart")

    else:
        print("argument error")

