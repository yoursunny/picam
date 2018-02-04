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


def run():
    httpd = HTTPServer(('', 8000), Handler)
    httpd.serve_forever()


if __name__ == '__main__':
    run()
