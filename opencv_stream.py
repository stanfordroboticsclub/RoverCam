from imutils.video import VideoStream
import datetime
import imutils
import time
import cv2

vs = VideoStream(usePiCamera=1).start()
time.sleep(1.0)

from opencv_remote import Server

server = Server(Server.INPUT.OPENCV)
server.listen()

while True:
    frame = vs.read()
    frame = imutils.resize(frame, width=320)

    timestamp = datetime.datetime.now()
    ts = timestamp.strftime("%A %d %B %Y %I:%M:%S%p")
    cv2.putText(frame, ts, (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)

    server.imshow("Frame", frame)

vs.stop()
