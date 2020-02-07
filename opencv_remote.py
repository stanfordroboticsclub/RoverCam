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

    def listen(self,loop=True):
        """" block until connection from viewer """
        # print("looking for ", self.hostname)
        while 1:
            try:
                msg = self.sub.recv()
                print("get msg: ", msg)
            except UDPComms.timeout:
                if not loop:
                    return
                
            else:
                if msg['host'] ==  self.hostname:
                    if msg.get('cmd') ==  'close':
                        self.stop_process()
                    else:
                        time.sleep(1) # sleep is necessary to not race ahead of viewer
                        self.init_process(msg["port"] , msg["ip"])
                        if self.mode == self.INPUT.OPENCV:
                            return

    def stop_process(self):
        if self.process != None:
            self.process.terminate()
            time.sleep(1)
            while self.process.poll() == None:
                self.process.kill()
        self.process = None


    """ display new image array on remote viewer """
    def imshow(self, name, img):
        self.listen(loop=False)

        if self.mode != self.INPUT.OPENCV or self.process is None:
            print("Error")
            return

        self.process.stdin.write(cv2.cvtColor(img, cv2.COLOR_BGR2YUV_I420))

    def init_process(self,port,ip):
        self.stop_process()

        if self.mode == self.INPUT.OPENCV:
            self.init_imshow( port , ip )
        elif self.mode == self.INPUT.RPI_CAM:
            self.run_rpi( port , ip )
        elif self.mode == self.INPUT.USB_CAM:
            self.run_usb( port , ip )

    def init_imshow(self, port, host):
        # works
        arg = 'gst-launch-1.0 -v fdsrc ! videoparse format="i420" width=320 height=240' +\
                            ' ! x264enc speed-preset=1 tune=zerolatency bitrate=1000000' +\
                            " ! rtph264pay pt=96 ! udpsink host={} port={}".format(host,port)
        print(arg)
        # self.process = subprocess.Popen(arg, stdin=subprocess.PIPE, shell=True)
        self.process = subprocess.Popen(shell.split(arg), stdin=subprocess.PIPE)

    def run_rpi(self, port, host):
        arg = "raspivid -fps 26 -h 720 -w 1280 -md 6 -n -t 0 -b 1000000 -o - | gst-launch-1.0 -e fdsrc" +\
              " ! h264parse ! rtph264pay pt=96 ! udpsink host={} port={}".format(host,port)
        print(arg)
        # also works on new os
        # gst-launch-1.0 v4l2src ! video/x-h264,width=1280,height=720,framerate=30/1 ! h264parse ! rtph264pay pt=127 config-interval=4 ! udpsink host=10.0.0.54 port=5001 sync=false

        self.process = subprocess.Popen(shlex.split(arg))

    def run_usb(self, port, host):
        # doesn't work
        arg = ("gst-launch-1.0 v4l2src device=/dev/video0 ! video/x-h264,width=1280,height=720 "+\
              " ! h264parse ! rtph264pay pt=96 ! udpsink host={} port={}".format(host,port))
        print(arg)

        # works 180ms of laterncy
        #gst-launch-1.0 v4l2src device=/dev/video0 ! video/x-raw,width=640,height=480 ! x264enc bitrate=1000000 speed-preset=1 tune=zerolatency ! rtph264pay pt=96 ! udpsink host=10.0.0.54 port=5001

        # also works (uvch can set more options)
        # gst-launch-1.0 -e uvch264src device=/dev/video0 initial-bitrate=1000000 average-bitrate=10000000 iframe-period=1000 name=src auto-start=true src.vfsrc ! queue ! video/x-raw,width=320,height=240,framerate=30/1 ! fakesink src.vidsrc ! queue ! video/x-h264,width=1920,height=1080,framerate=30/1,profile=constrained-baseline ! h264parse ! rtph264pay pt=96 ! udpsink host=10.0.0.54 port=5001

        self.process = subprocess.Popen(shlex.split(arg))

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
        self.resolution = (320, 240)

        self.process = None
        self.remote_host = None

    def close(self):
        if self.remote_host is None:
            print("Error")
            return
        # send 3 times for reliability :P
        self.pub.send({"host": self.remote_host, "cmd": "close"})
        self.pub.send({"host": self.remote_host, "cmd": "close"})
        self.pub.send({"host": self.remote_host, "cmd": "close"})

    def open(self):
        port = 5001 # TODO CHANGE TO pick free port
        if self.remote_host is None:
            print("Error")
            return

        self.pub.send({"ip": self.ip, "host": self.remote_host, "resolution": self.resolution, "port":port})

        if self.mode == self.OUTPUT.WINDOW:
            # caps="application/x-rtp" is what makes things slow. replaces with gdppay
            cmd = 'gst-launch-1.0 udpsrc port={} caps="application/x-rtp" ! rtph264depay ! avdec_h264 ! autovideosink sync=false'.format(port)
            # cmd = 'gst-launch-1.0 udpsrc port={} ! gdpdepay ! rtph264depay ! avdec_h264 ! autovideosink sync=false'.format(port)
            args = shlex.split(cmd)
            # shell = True need to open a window. $DISPLAY needs to be set?
            # print(args)
            # self.process = subprocess.Popen(cmd, shell=True)
            self.process = subprocess.Popen(args)


        elif self.mode == self.OUTPUT.OPENCV:
            arg = 'gst-launch-1.0 udpsrc port={} caps="application/x-rtp" ! rtph264depay ! avdec_h264 ! fdsink sync=false'.format(port)
            # cmd = 'gst-launch-1.0 udpsrc port={} ! gdpdepay ! rtph264depay ! avdec_h264 ! fdsink'
            self.process = subprocess.Popen(arg, shell=True, stdout=subprocess.PIPE)

    def __del__(self):
        self.close()

    def stream(self, hostname):
        self.remote_host = hostname
        self.open()

        if self.mode == self.OUTPUT.WINDOW:
            self.monitor(loop = True)

    def read(self):
        # self.monitor(loop= False)
        return self.process.stdout.read(320*240*3)

    def monitor(self, loop = True):
        # TODO FINSHI
        if loop:
            while 1:
                self.process.wait()
                self.process = subprocess.Popen(arg, shell=True, stdout=subprocess.PIPE)
                self.open()

        else:
            if self.process.poll():
                return
            else:
                self.process = subprocess.Popen(arg, shell=True, stdout=subprocess.PIPE)
                self.open()
                # resend request




import argparse
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('op', choices=['server', 'usb','viewer'])
    args = parser.parse_args()

    if args.op == "server":
        s = Server()
        s.listen()
    elif args.op == "usb":
        s = Server(Server.INPUT.USB_CAM)
        s.listen()

    elif args.op == "viewer":
        r = RemoteViewer()
        r.stream("acrocart")

    else:
        print("argument error")

