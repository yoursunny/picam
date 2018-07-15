#!/usr/bin/python3
from io import BytesIO
import logging
import time
from picamera import PiCamera
import pyndn
import pyndn.transport
import pyndn.util
import urllib.request


class NdnCam(object):
    def __init__(self, cameraName, face, resolution=None):
        self.log = logging.Logger('NdnCam')
        self.log.setLevel(logging.DEBUG)

        self.cameraName = cameraName
        self.prefix = pyndn.Name('/yoursunny.com/homecam-%s' % self.cameraName)
        self.resolution = (320, 240) if resolution is None else resolution
        self.quality = 30
        self.chunkSize = 1200
        self.freshnessPeriod = 10000

        self.face = face
        self.cache = pyndn.util.MemoryContentCache(self.face)
        self.cache.setInterestFilter(
            self.prefix, self.cache.getStorePendingInterest())

    def online(self):
        httpReq = urllib.request.Request(
            'https://yoursunny.com/p/homecam/?prefixreg=%s' % self.cameraName, method='POST')
        httpResp = urllib.request.urlopen(httpReq)
        prefixRegCmd = httpResp.read()
        self.log.info('Prefix registration command: %s', prefixRegCmd)
        self.face.expressInterest(pyndn.Name(
            '/ndn'), lambda interest, data: None)
        self.face.send(prefixRegCmd)

    def run(self):
        with PiCamera() as camera:
            camera.resolution = self.resolution
            while True:
                imageFile = BytesIO()
                camera.capture(imageFile, format='jpeg',
                               resize=self.resolution, quality=self.quality)
                image = imageFile.getvalue()
                versioned = pyndn.Name(self.prefix).appendVersion(
                    int(time.time() * 1000))
                chunkIndices = list(range(0, len(image), self.chunkSize))
                metaInfo = pyndn.MetaInfo()
                metaInfo.setFreshnessPeriod(self.freshnessPeriod)
                metaInfo.setFinalBlockId(
                    pyndn.Name.Component.fromSegment(len(chunkIndices) - 1))
                for seg, chunkIndex in enumerate(chunkIndices):
                    data = pyndn.Data(pyndn.Name(versioned).appendSegment(seg))
                    data.setMetaInfo(metaInfo)
                    data.setContent(
                        image[chunkIndex:chunkIndex+self.chunkSize])
                    self.cache.add(data)
                self.log.info('%s %d', versioned, len(chunkIndices))
                imageFile.close()
                for i in range(1000):
                    self.face.processEvents()


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(
        description='NDN HomeCam compatible camera.')
    parser.add_argument('--camera', type=str,
                        required=True, help='camera name')
    parser.add_argument('--router', type=str,
                        default='hobo.cs.arizona.edu', help='router hostname')
    args = parser.parse_args()
    camera = NdnCam(args.camera, pyndn.Face(args.router))
    camera.online()
    camera.run()
