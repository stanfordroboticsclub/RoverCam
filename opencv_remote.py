

# def initialize():
#      global gstCommand
#      if os.name == "posix":
#          args = shlex.split(('gst-launch-1.0 fdsrc ! "video/x-raw, width=320, \
#           height=240, format=I420, framerate=1/1" ! rawvideoparse use-sink-caps=true ' +
#          ' ! x264enc ! h264parse ! queue ! rtph264pay pt=96 ! gdppay !  udpsink host=10.0.0.54 port=5001'))
#          gstCommand = subprocess.Popen(args, stdin=subprocess.PIPE)





# initialize()
# while 1:
#     frame = vs.read()
#     imshow('test',frame)


# def imshow(name, img):
#      if gstCommand:
#          gstCommand.stdin.write(cv2.cvtColor(img, cv2.COLOR_BGR2YUV_I420))
#      else:
#          cv2.imshow(img)


# working: (from https://www.chiefdelphi.com/t/stream-opencv-output-remotely-like-imshow-but-for-headless-video-processors/157108)

#     def initialize(host, port, bitrate=1024):
#      global gstCommand
#      if os.name == "posix":
#          args = shlex.split(('gst-launch-1.0 fdsrc ! videoparse format="i420" width=320 height=240' +
#          ' ! x264enc speed-preset=1 tune=zerolatency bitrate={}' +
#          ' ! rtph264pay config-interval=1 pt=96 ! udpsink host={} port={}').format(
#          bitrate, host, port))
#          gstCommand = subprocess.Popen(args, stdin=subprocess.PIPE)


#     with
#     gst-launch-1.0 udpsrc port=5800 caps="application/x-rtp" ! rtph264depay ! avdec_h264 ! autovideosink
#     ^ this is p low latency and can be addapeted to work with existing code for raw streaming

import shlex
import os
import subprocess
import UDPComms
import re

from imutils.video import VideoStream, FileVideoStream

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
        self.cmd = None

    def listen(self):
        # blocking listens for conenction for viewer
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


    def init_imshow(self, port, host):
        # works
        args = shlex.split(('gst-launch-1.0 fdsrc ! videoparse format="i420" width=320 height=240' +
                            ' ! x264enc speed-preset=1 tune=zerolatency bitrate=1000000' +
                            ' ! rtph264pay config-interval=1 pt=96 ! udpsink host={} port={}').format(host, port))
        self.cmd = subprocess.Popen(args, stdin=subprocess.PIPE)

    """ display new image array on remote viewer """
    def imshow(self, img):
        if self.mode != self.INPUT.OPENCV or self.cmd is None:
            print("Error")
            return

        self.cmd.stdin.write(cv2.cvtColor(img, cv2.COLOR_BGR2YUV_I420))

    def run_rpi(self, port, host):
        # works (no gdppay)
        arg = "gst-launch-1.0 rpicamsrc preview=false bitrate=2000000 sensor-mode=5 ! 'video/x-h264,width=1280,height=720,framerate=45/1,profile=high' ! h264parse ! queue ! rtph264pay pt=96 ! udpsink host={} port={}".format(host,port)
        args = shlex.split(arg)

        self.cmd = subprocess.Popen(args)
        while 1:
            pass


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
        self.pub.send({"ip": self.ip, "host": hostname, "resolution": (300,200), "port":port})

        if self.mode == self.OUTPUT.WINDOW:
            cmd = 'gst-launch-1.0 udpsrc port={} caps="application/x-rtp" ! rtph264depay ! avdec_h264 ! autovideosink'.format(port)
            args = shlex.split(cmd)
            # shell = True need to open a window. $DISPLAY needs to be set?
            print(args)
            self.process = subprocess.Popen(cmd, shell=True)
            # self.process = subprocess.Popen(args)
            while(1):
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

