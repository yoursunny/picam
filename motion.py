#!/usr/bin/python3
import contextlib
import cv2
import numpy as np
import threading
import time
from picamera import PiCamera


class MotionDetector:
    def __init__(self):
        self.requestBorrow = threading.Event()
        self.beginBorrow = threading.Event()
        self.endBorrow = threading.Event()
        self.thread = threading.Thread(target=self._threadMain, daemon=True)
        self.lastMotionImage = None
        self.lastMotionTime = 0

    def start(self):
        self.thread.start()

    @contextlib.contextmanager
    def borrowCamera(self):
        self.requestBorrow.set()
        self.beginBorrow.wait()
        self.beginBorrow.clear()
        try:
            with PiCamera() as camera:
                yield camera
        finally:
            self.endBorrow.set()

    def _threadMain(self):
        while True:
            self._run()
            self.requestBorrow.clear()
            self.beginBorrow.set()
            self.endBorrow.wait()
            self.endBorrow.clear()

    def _run(self):
        width, height, blur, weight, threshold, minArea, minFrames = 640, 480, 2, 0.2, 5, 6000, 3
        avgFrame, nFrames = None, 0
        with PiCamera() as camera:
            camera.resolution = (width, height)
            camera.video_denoise = False
            camera.image_effect = 'blur'
            camera.image_effect_params = (blur,)

            yuv = np.empty((int(width * height * 1.5),), dtype=np.uint8)
            for x in camera.capture_continuous(yuv, format='yuv', use_video_port=True):
                image = yuv[:width*height].reshape((height, width))
                if avgFrame is None:
                    avgFrame = image.copy().astype('float')
                else:
                    cv2.accumulateWeighted(image, avgFrame, weight)
                delta = cv2.absdiff(image, cv2.convertScaleAbs(avgFrame))
                thresh = cv2.threshold(
                    delta, threshold, 255, cv2.THRESH_BINARY)[1]
                thresh = cv2.dilate(thresh, None, iterations=2)

                hasMotion = False
                for contour in cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[1]:
                    if cv2.contourArea(contour) < minArea:
                        continue
                    hasMotion = True

                if hasMotion:
                    nFrames += 1
                    if nFrames == minFrames:
                        self.lastMotionImage = image.copy()
                        self.lastMotionTime = time.time()
                else:
                    nFrames = 0

                if self.requestBorrow.is_set():
                    return
                time.sleep(0.1)
