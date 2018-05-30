#!/usr/bin/python3
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from picamera import PiCamera
from socketserver import ThreadingMixIn

from mjpeg_util import MjpegMixin, SmoothedFpsCalculator


cameraLock = threading.Lock()


class Handler(BaseHTTPRequestHandler, MjpegMixin):
    def do_GET(self):
        if self.path == '/robots.txt':
            self.handleRobotsTxt()
        elif self.path == '/cam.jpg':
            self.handleCamJpg()
        elif self.path == '/cam.mjpeg':
            self.handleCamMjpeg()
        elif self.path == '/contour.mjpeg':
            self.handleContourMjpeg()
        else:
            self.send_response(404)
            self.end_headers()

    def handleRobotsTxt(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write('User-Agent: *\nDisallow: /\n'.encode('ascii'))

    def handleCamJpg(self):
        self.send_response(200)
        self.send_header('Content-Type', 'image/jpeg')
        self.end_headers()
        with cameraLock, PiCamera() as camera:
            camera.resolution = (800, 600)
            time.sleep(1)
            camera.capture(self.wfile, format='jpeg')

    def handleCamMjpeg(self):
        self.mjpegBegin()
        with cameraLock, PiCamera() as camera:
            camera.resolution = (640, 480)
            sfps = SmoothedFpsCalculator()
            for x in camera.capture_continuous(self.wfile, format='jpeg',
                                               use_video_port=True, quality=50):
                self.mjpegEndFrame()
                camera.annotate_text = '%0.2f fps' % sfps()

    def handleContourMjpeg(self):
        import cv2
        import numpy as np
        width, height, blur, sigma = 640, 480, 2, 0.33
        fpsFont, fpsXY = cv2.FONT_HERSHEY_SIMPLEX, (0, height-1)
        self.mjpegBegin()
        with cameraLock, PiCamera() as camera:
            camera.resolution = (width, height)
            camera.video_denoise = False
            camera.image_effect = 'blur'
            camera.image_effect_params = (blur,)
            yuv = np.empty((int(width * height * 1.5),), dtype=np.uint8)
            sfps = SmoothedFpsCalculator()
            for x in camera.capture_continuous(yuv, format='yuv', use_video_port=True):
                image = yuv[:width*height].reshape((height, width))
                v = np.median(image)
                lower = int(max(0, (1.0 - sigma) * v))
                upper = int(min(255, (1.0 + sigma) * v))
                image = cv2.Canny(image, lower, upper)
                cv2.putText(image, '%0.2f fps' %
                            sfps(), fpsXY, fpsFont, 1.0, 255)
                self.wfile.write(cv2.imencode('.jpg', image)[1])
                self.mjpegEndFrame()


class ThreadedHttpServer(ThreadingMixIn, HTTPServer):
    pass


def run(port=8000):
    httpd = ThreadedHttpServer(('', port), Handler)
    httpd.serve_forever()


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='HTTP streaming camera.')
    parser.add_argument('--port', type=int, default=8000,
                        help='listening port number')
    args = parser.parse_args()
    run(port=args.port)
