import shlex
import os
import subprocess
import signal
import re
from enum import Enum
import time
from contextlib import closing

import UDPComms

try:
    from imutils.video import VideoStream, FileVideoStream
    import cv2, imutils
except ImportError:
    cv2 = None


REQUEST_PORT = 5000

class ProcessMonitor:
    def __init__(self):
        self.process = None
        self.cmd = None

    def start(self, cmd):
        self.cmd = cmd
        if(self.process!=None):
            self.stop()

        # setting preexec_fn=os.setsid allows us to kill the process group allowing for shell=True
        # without it calling process.terminate() would only kill the shell and not the underlying process
        self.process = subprocess.Popen(self.cmd, shell=True, stdin=subprocess.PIPE, preexec_fn=os.setsid)

        # shell=True is needed as some commands have a shell pipe in them (raspivid specifically)
        # self.process = subprocess.Popen(shlex.split(self.cmd), stdin=subprocess.PIPE)

    def stop(self):
        if self.process != None:
            os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
            time.sleep(1)
            while self.running():
                os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
        self.process = None

    def restart(self):
        self.start(self.cmd)

    def running(self):
        return self.process.poll() == None

class Server:
    INPUT = Enum("INPUT", "RPI_CAM USB_CAM OPENCV USB_H264")
    def __init__(self, mode = None, name = None, device = None):
        if mode == None:
            mode = self.INPUT.RPI_CAM
        if device == None:
            device = "/dev/video0"

        self.mode = mode
        self.name = name
        self.device = device

        if(mode == self.INPUT.OPENCV and cv2 is None):
            raise ImportError("no opencv installed on this system")

        self.sub = UDPComms.Subscriber(REQUEST_PORT, timeout=0)
        self.hostname = subprocess.run('hostname', stdout=subprocess.PIPE).stdout.strip().decode("utf-8")

        self.process = ProcessMonitor()


    def parse_messages(self):
        messages = self.sub.get_list()
        for msg in messages:
            if msg['host'] ==  self.hostname:
                if msg.get('name') != self.name: # get returns None when key not found
                    continue
                print("got ", msg)
                if msg.get('cmd') ==  'close':
                    self.process.stop()
                else:
                    time.sleep(1) # sleep is necessary to not race ahead of viewer
                    cmd = self.get_cmd(msg)
                    self.process.start(cmd)

    def listen(self):
        """" block forever parsing messages """
        if self.mode == self.INPUT.OPENCV:
            raise ValueError("listen is only available in non OPENCV mode")

        while 1:
            self.parse_messages()

    """ display new image array on remote viewer """
    def imshow(self, name, img):
        if self.mode != self.INPUT.OPENCV:
            raise ValueError("imshow is only available in OPENCV mode")

        self.parse_messages()

        if self.process.process is None:
            print("No viewer connected")
            return

        img = imutils.resize(img, width=320) # resolution needs to match with video
        self.process.process.stdin.write(cv2.cvtColor(img, cv2.COLOR_BGR2YUV_I420))

    def get_cmd(self, msg):
        port, ip = msg["port"] , msg["ip"]
        if self.mode == self.INPUT.OPENCV:
            # resolution needs to match with opencv image
            cmd = 'gst-launch-1.0 -v fdsrc ! videoparse format="i420" width=320 height=240' +\
                  ' ! x264enc speed-preset=1 tune=zerolatency bitrate=1000000' +\
                  " ! rtph264pay pt=96 ! udpsink host={} port={}".format(ip,port)

        elif self.mode == self.INPUT.RPI_CAM:
            # works 120ms of latency
            # used Pi's H264 encoder so can only run one of those
            cmd = "raspivid -fps 26 -h 720 -w 1280 -md 6 -n -t 0 -b 1000000 -o - | gst-launch-1.0 -e fdsrc" +\
                  " ! h264parse ! rtph264pay pt=96 ! udpsink host={} port={}".format(ip,port)

                # also works on new os
                # gst-launch-1.0 v4l2src ! video/x-h264,width=1280,height=720,framerate=30/1 ! h264parse ! rtph264pay pt=127 config-interval=4 ! udpsink host=10.0.0.54 port=5001 sync=false
        elif self.mode == self.INPUT.USB_CAM:
            # works 180ms of latency
            # used Pi's H264 encoder so can only run one of those
            cmd = ("gst-launch-1.0 v4l2src device={} ! video/x-raw,width=640,height=480 " +\
                   "! x264enc bitrate=1000000 speed-preset=1 tune=zerolatency ! rtph264pay pt=96 ! udpsink host={} port={}".format(self.device, ip,port))

        elif self.mode == self.INPUT.USB_H264:
            # works 120-180ms of latency
            # encodes H264 on the camera so supperts multiples cameras
            # for some reason it only works with c920 not c930e :(
            cmd = ("gst-launch-1.0 v4l2src device={} ! video/x-h264,width=1280,height=720 "+\
                  " ! h264parse ! rtph264pay pt=96 ! udpsink host={} port={}".format(self.device, ip,port))

                    # also works (uvch can set more options)
                    # gst-launch-1.0 -e uvch264src device=/dev/video0 initial-bitrate=1000000 average-bitrate=10000000 iframe-period=1000 name=src auto-start=true src.vfsrc ! queue ! video/x-raw,width=320,height=240,framerate=30/1 ! fakesink src.vidsrc ! queue ! video/x-h264,width=1920,height=1080,framerate=30/1,profile=constrained-baseline ! h264parse ! rtph264pay pt=96 ! udpsink host=10.0.0.54 port=5001
        else:
            raise ValueError("Unknown mode")
        print(cmd)
        return cmd

# TODO: this class is a mess!
class RemoteViewer:
    OUTPUT = Enum("OUPUT", "OPENCV WINDOW")

    def get_my_ip(self):
        # a = subprocess.run('ifconfig',capture_output=1) #capture_output is only in python 3.7 and above
        a = subprocess.run('ifconfig', stdout=subprocess.PIPE).stdout.strip()
        m = re.search( b"10\.0\.0\.[1-9][0-9]{0,2}", a)
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
        self.resolution = (320, 240) #TODO: make resultuiong be sent along

        self.process = None
        self.remote_host = None
        self.camera_name = None

    def close(self):
        if self.remote_host is None:
            print("Error")
            return
        # send 3 times for reliability :P
        self.pub.send({"host": self.remote_host, "cmd": "close"})
        self.pub.send({"host": self.remote_host, "cmd": "close"})
        self.pub.send({"host": self.remote_host, "cmd": "close"})

    def get_free_port(self):
        port = 5001
        while 1:
            try:
                with closing(socket.socket(socket.AF_INET, socket.SOCK_DGRAM)) as s:
                    s.bind(('', port))
                    return port
            except OSError:
                port += 1
                if port > 7000:
                    raise

    def open(self):
        port = self.get_free_port()
        if self.remote_host is None:
            print("Error")
            return

        self.pub.send({"ip": self.ip, "host": self.remote_host, "resolution": self.resolution, "port":port, "name":self.camera_name})

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

    def stream(self, hostname, camera_name = None):
        self.remote_host = hostname
        self.camera_name = camera_name
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
    subparsers = parser.add_subparsers(dest='subparser')

    server = subparsers.add_parser("server")
    server.add_argument('source', help="where should the video come from", choices=['rpi', 'usb','h264'])
    server.add_argument('camera_name', nargs='?', default=None, help="used to disambiguate multiple cameras on one pi")

    viewer = subparsers.add_parser("viewer")
    viewer.add_argument('hostname', help="hostname of the computer we want to view")
    viewer.add_argument('camera_name', nargs='?', default=None, help="used to disambiguate multiple cameras on one pi")

    args = parser.parse_args()

    if args.subparser == 'viewer':
        r = RemoteViewer()
        r.stream(args.hostname, args.camera_name)

    elif args.subparser == 'server':
        if args.source == "rpi":
            s = Server(Server.INPUT.RPI_CAM, args.camera_name)
            s.listen()
        elif args.source == "usb":
            s = Server(Server.INPUT.USB_CAM, args.camera_name)
            s.listen()
        elif args.source == "h264":
            s = Server(Server.INPUT.USB_H264, args.camera_name)
            s.listen()

