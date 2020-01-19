
import cv2

from opencv_remote import RemoteViewer
import time

r = RemoteViewer(RemoteViewer.OUTPUT.OPENCV)
r.stream('acrocart')

time.sleep(1)


while(True):
    # Capture frame-by-frame
    frame = r.read()

    # try:
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    cv2.imshow('frame',gray)
    # except:
    #     print('skiping')
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# When everything done, release the capture
cap.release()
cv2.destroyAllWindows()
