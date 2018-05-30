import time


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


class SmoothedFpsCalculator:
    """
    Provide smoothed frame per second calculation.
    """

    def __init__(self, alpha=0.1):
        self.t = time.time()
        self.alpha = alpha
        self.sfps = None

    def __call__(self):
        t = time.time()
        d = t - self.t
        self.t = t
        fps = 1.0 / d
        if self.sfps is None:
            self.sfps = fps
        else:
            self.sfps = fps * self.alpha + self.sfps * (1.0 - self.alpha)
        return self.sfps
