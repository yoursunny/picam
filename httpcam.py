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
        camera = PiCamera()
        try:
            camera.resolution = (800, 600)
            camera.start_preview()
            time.sleep(1)
            camera.capture(self.wfile, 'jpeg')
        finally:
            camera.close()

    def handleCamMjpeg(self):
        boundary = 'eb4154aac1c9ee636b8a6f5622176d1fbc08d382ee161bbd42e8483808c684b6'
        frameBeg = 'Content-Type: image/jpeg\n\n'.encode('ascii')
        frameEnd = ('\n--' + boundary + '\n').encode('ascii')
        self.send_response(200)
        self.send_header(
            'Content-Type', 'multipart/x-mixed-replace;boundary=' + boundary)
        self.end_headers()
        camera = PiCamera()
        try:
            camera.resolution = (320, 240)
            camera.start_preview()
            time.sleep(1)
            while True:
                self.wfile.write(frameBeg)
                camera.capture(self.wfile, 'jpeg')
                self.wfile.write(frameEnd)
                self.wfile.flush()
        finally:
            camera.close()


def run():
    httpd = HTTPServer(('', 8000), Handler)
    httpd.serve_forever()


if __name__ == '__main__':
    run()
