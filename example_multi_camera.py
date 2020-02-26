

from CameraStream import Server
import threading


servers = []
servers.append( Server(Server.INPUT.USB_H264, "1", device = "/dev/video0" ) )
servers.append( Server(Server.INPUT.USB_H264, "2", device = "/dev/video2" ) )
servers.append( Server(Server.INPUT.USB_H264, "3", device = "/dev/video4" ) )

for server in servers:
    thread = threading.Thread(target = server.listen, daemon = True)
    thread.start()

while 1:
    pass
