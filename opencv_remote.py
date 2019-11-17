

def initialize():
     global gstCommand
     if os.name == "posix":
         args = shlex.split(('gst-launch-1.0 fdsrc ! "video/x-raw, width=320, \
          height=240, format=I420, framerate=1/1" ! rawvideoparse use-sink-caps=true ' +
         ' ! x264enc ! h264parse ! queue ! rtph264pay pt=96 ! gdppay !  udpsink host=10.0.0.54 port=5001'))
         gstCommand = subprocess.Popen(args, stdin=subprocess.PIPE)





initialize()
while 1:
    frame = vs.read()
    imshow('test',frame)


def imshow(name, img):
     if gstCommand:
         gstCommand.stdin.write(cv2.cvtColor(img, cv2.COLOR_BGR2YUV_I420))
     else:
         cv2.imshow(img)


working: (from https://www.chiefdelphi.com/t/stream-opencv-output-remotely-like-imshow-but-for-headless-video-processors/157108)

    def initialize(host, port, bitrate=1024):
     global gstCommand
     if os.name == "posix":
         args = shlex.split(('gst-launch-1.0 fdsrc ! videoparse format="i420" width=320 height=240' +
         ' ! x264enc speed-preset=1 tune=zerolatency bitrate={}' +
         ' ! rtph264pay config-interval=1 pt=96 ! udpsink host={} port={}').format(
         bitrate, host, port))
         gstCommand = subprocess.Popen(args, stdin=subprocess.PIPE)


    with
    gst-launch-1.0 udpsrc port=5800 caps="application/x-rtp" ! rtph264depay ! avdec_h264 ! autovideosink
    ^ this is p low latency and can be addapeted to work with existing code for raw streaming

import shlex
import os
import subprocess
import UDPComms

from imutils.video import VideoStream

class Server:
    def __init__(self, mode="rpi"):

        self.mode = mode
        self.commands = {"rpi": "test"}


    def listen(self):
        pass
        # blocking listens for conenction for viewer

    def init_imshow(self, port, host):

        # works
     global gstCommand
     if os.name == "posix":
         args = shlex.split(('gst-launch-1.0 fdsrc ! videoparse format="i420" width=320 height=240' +
         ' ! x264enc speed-preset=1 tune=zerolatency bitrate={}' +
         ' ! rtph264pay config-interval=1 pt=96 ! udpsink host={} port={}').format(
         bitrate, host, port))
         gstCommand = subprocess.Popen(args, stdin=subprocess.PIPE)

    """ display new image array on remote viewer """
    def imshow(self, img):
        if self.mode != "rpi":
            print("Error")
            return
        gstCommand.stdin.write(cv2.cvtColor(img, cv2.COLOR_BGR2YUV_I420))

    def run_rpi(self, port, host):
        cmd = """gst-launch-1.0 rpicamsrc preview=false bitrate=2000000 sensor-mode=5 ! 'video/x-h264,width=1280,height=720,framerate=45/1,profile=high' ! h264parse ! queue ! rtph264pay pt=96 ! gdppay ! udpsink host=10.0.0.54 port=5001"""

        # works (no gdppay)
        cmd = """gst-launch-1.0 rpicamsrc preview=false bitrate=2000000 sensor-mode=5 ! 'video/x-h264,width=1280,height=720,framerate=45/1,profile=high' ! h264parse ! queue ! rtph264pay pt=96 ! udpsink host=10.0.0.54 port=5001"""

    def run_usb(self, port, host):
        pass

class RemoteViewer:
    def __init__(self, mode = 'opencv'):
        self.mode = mode

    def stream(self, hostname):
        send (hostname, my_ip, resolution)
        port = recv()

    def start(self):
        cmd = 'gst-launch-1.0 udpsrc port={} caps="application/x-rtp" ! rtph264depay ! avdec_h264 ! fdsink'

        return imutils.FileVideoStream(cmd).start()
         # args = shlex.split((cmd).format(port))
         # gstCommand = subprocess.Popen(args, stdout=subprocess.PIPE)
         # img = gstCommand.stdout.read()

    def window(self):
        cmd = 'gst-launch-1.0 udpsrc port=5001 caps="application/x-rtp" ! rtph264depay ! avdec_h264 ! autovideosink'






