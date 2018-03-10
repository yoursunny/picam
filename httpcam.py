#!/usr/bin/python3
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from picamera import PiCamera


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/robots.txt':
            self.handleRobotsTxt()
        elif self.path == '/cam.jpg':
            self.handleCamJpg()
        elif self.path == '/cam.mjpeg':
            self.handleCamMjpeg()
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
            camera.capture(self.wfile, format='jpeg')

    def handleCamMjpeg(self):
        boundary = 'eb4154aac1c9ee636b8a6f5622176d1fbc08d382ee161bbd42e8483808c684b6'
        frameBegin = 'Content-Type: image/jpeg\n\n'.encode('ascii')
        frameBound = ('\n--' + boundary + '\n').encode('ascii') + frameBegin
        self.send_response(200)
        self.send_header(
            'Content-Type', 'multipart/x-mixed-replace;boundary=' + boundary)
        self.end_headers()
        with PiCamera() as camera:
            camera.resolution = (640, 480)
            time.sleep(1)
            self.wfile.write(frameBegin)
            for dummy in camera.capture_continuous(self.wfile, format='jpeg',
                                                   use_video_port=True, quality=50):
                self.wfile.write(frameBound)


def run():
    httpd = HTTPServer(('', 8000), Handler)
    httpd.serve_forever()


if __name__ == '__main__':
    run()
