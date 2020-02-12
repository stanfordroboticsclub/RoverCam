# RoverCam
"Documentation sucks so we'll do that later" - Chandler Watson, 2018
"Later is now " - Michal, 2020


## Usage

On the server side:
`python3 CameraStream.py server rpi` will lanuch a server what waits for a request from a viewer, and serve it the video stream from the rpi camera. `rpi` can be replaced with `usb` or `h264` to take the video from a normal usb webcam or to grab h264 encoded video straight from the webcam (only testing with the logitech c920). This is prefereable as it allows for mutiple cameras to be running of of one pi (as it doesn't use the pi's single hardware h264 encoder)

On the viewer side:
`python3 CameraStream.py viewer hostname` will request a video stream from the rpi with the specified hostname. When gstreamer is installed this also works on a mac!


## Motivation

Gstreamer allows for low latency streaming of video between two devices. The video is h264 encoded on one end and packaged into UDP packets. This works well but is annoying as you need to coordinate commands on two differnt devices (launching them in the correct order, with matched settings etc).  CameraStream provides that coordination. 

The idea is the device with the camera has a CameraStream server start on boot. That then waits for incoming commands from a viewer that wants to access its stream, and launches it. When the viewer exits (or a new request comes along) then previous stream gets gracefully shutdown. 

The server can also take the video stream from opencv (as shown in `example_opencv_server.py`). This is super useful for debugging opencv code running on a headless device
