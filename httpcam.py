#!/usr/bin/python3
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from picamera import PiCamera


class MjpegMixin:
    """
    Add MJPEG features to a subclass of BaseHTTPRequestHandler.
    """

    mjpegBound = 'eb4154aac1c9ee636b8a6f5622176d1fbc08d382ee161bbd42e8483808c684b6'
    frameBegin = 'Content-Type: image/jpeg\n\n'.encode('ascii')
    frameBound = ('\n--' + mjpegBound + '\n').encode('ascii') + frameBegin

    def mjpegBegin(self):
        self.send_response(200)
        self.send_header('Content-Type',
                         'multipart/x-mixed-replace;boundary=' + MjpegMixin.mjpegBound)
        self.end_headers()
        self.wfile.write(MjpegMixin.frameBegin)

    def mjpegEndFrame(self):
        self.wfile.write(MjpegMixin.frameBound)


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
        with PiCamera() as camera:
            camera.resolution = (800, 600)
            time.sleep(1)
            camera.capture(self.wfile, format='jpeg')

    def handleCamMjpeg(self):
        self.mjpegBegin()
        with PiCamera() as camera:
            camera.resolution = (640, 480)
            for x in camera.capture_continuous(self.wfile, format='jpeg',
                                               use_video_port=True, quality=50):
                self.mjpegEndFrame()

    def handleContourMjpeg(self):
        width, height, blur, sigma = 640, 480, 2, 0.33
        import cv2
        import numpy as np
        self.mjpegBegin()
        with PiCamera() as camera:
            camera.resolution = (width, height)
            camera.image_denoise = False
            camera.image_effect = 'blur'
            camera.image_effect_params = (blur,)
            yuv = np.empty((int(width * height * 1.5),), dtype=np.uint8)
            for x in camera.capture_continuous(yuv, format='yuv', use_video_port=False):
                image = yuv[:width*height].reshape((height, width))
                v = np.median(image)
                lower = int(max(0, (1.0 - sigma) * v))
                upper = int(min(255, (1.0 + sigma) * v))
                edged = cv2.Canny(image, lower, upper)
                self.wfile.write(cv2.imencode('.jpg', edged)[1])
                self.mjpegEndFrame()


def run(port=8000):
    httpd = HTTPServer(('', port), Handler)
    httpd.serve_forever()


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='HTTP streaming camera.')
    parser.add_argument('--port', type=int, default=8000,
                        help='listening port number')
    args = parser.parse_args()
    run(port=args.port)
