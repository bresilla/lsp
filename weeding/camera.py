import sys
import cv2
import time
import os

import datetime

x = datetime.datetime.now()
date_folder = "C:\\Cam\\" + str(x.strftime("%Y%m%d"))


if not os.path.exists(date_folder):
    os.makedirs(date_folder)


class Stream():
    def __init__(self):
        self.sleeper = 1

    def sleep(self):
        time.sleep(self.sleeper)


def main(args=None):
    cpt = 0
    maxFrames = 100  # if you want 5 frames only.

    try:
        vidStream = cv2.VideoCapture(0)  # index of your camera
    except:
        print("problem opening input stream")
        sys.exit(1)

    while cpt < maxFrames:
        cpt += 1
        ret, frame = vidStream.read()
        frame_copy=frame
        if not ret:
            sys.exit(0)
        cv2.imwrite(date_folder + "\\image%06i.jpg" % cpt, frame)
        cv2.imshow("CAM", frame_copy)
        time.sleep(0.25)


if __name__ == '__main__':
    main()
