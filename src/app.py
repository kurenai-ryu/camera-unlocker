#!/usr/bin/python
# -*- coding: utf-8 -*-

# import the necessary packages
from __future__ import print_function

from flask import Flask, render_template, Response
from flask_restful import Api, Resource, reqparse

import logging
from imutils.video import WebcamVideoStream
import config
import imutils
import cv2
import time

from conexion import Conexion
from face import FaceDetector
from threading import Thread
LOGGER = logging.getLogger(__name__)

caputador = None

print("[INFO] sampling THREADED frames from webcam...")
#vs.stream.set(cv2.cv.CV_CAP_PROP_BRIGHTNESS,1.0)

class CaptThread(Thread):
    def __init__(self):
        super(CaptThread, self).__init__(name="CaptThread", args=())
        self.setDaemon(True) #it's still dependant of mainthread
        self.facedetector = FaceDetector()
        self.facedetector.camera = WebcamVideoStream(src=0).start()
        self.img = dict() #las imagenes cv2 (numpy) como tal
        self.img["logo"] = cv2.imread('templates/logo.jpg') 
        self.img["camara"] = self.img["logo"] # para despliegue inicial
        self.img["inst"] = self.img["logo"]
        self.start()
    def run(self):
        LOGGER.info("iniciando hilo captura");
        while (True):
            time.sleep(0.5)
            #agregar aqui cambios para indetificacion y entrenamiento
            if (self.facedetector is not None
                    and self.facedetector.camera is not None):
                #first read the image for debug purposes
                self.img["camara"] = self.facedetector.camera.read().copy() #self.facedetector.last["imagen"]
                if self.facedetector.last["coord"] is not None:
                    print ("encontró")
                    posx, posy, width, height = self.facedetector.last["coord"]
                    cv2.rectangle(self.img["camara"],
                                  (posx, posy), (posx+width, posy+height),
                                  (255, 0, 0), 2)
                if self.facedetector.margin is not None:
                    posx1, posy1, posx2, posy2 = self.facedetector.margin
                    cv2.rectangle(self.img["camara"],
                                  (posx1, posy1), (posx2, posy2),
                                  (255, 255, 0), 2) # hardcoded by now
                self.facedetector.finish = False
        LOGGER.error("finalizado hilo!!!");

"""class VideoCamera(object):
    def __init__(self):
        # Using OpenCV to capture from device 0. If you have trouble capturing
        # from a webcam, comment the line below out and use a video file
        # instead.
        self.video = cv2.VideoCapture(0)
        # If you decide to use video.mp4, you must have this file in the folder
        # as the main.py.
        # self.video = cv2.VideoCapture('video.mp4')
    
    def __del__(self):
        self.video.release()
    
    def get_frame(self):
        success, image = self.video.read()
        # We are using Motion JPEG, but OpenCV defaults to capture raw images,
        # so we must encode it into JPEG in order to correctly display the
        # video stream.
        ret, jpeg = cv2.imencode('.jpg', image)
        return jpeg.tostring()"""



print ("starting flask def...")

APP = Flask(__name__)
REST = Api(APP)

@APP.route('/')
def index():
    return render_template('index.html')

def gen():
    while True:
	image = capturador.img["camara"]
	#image = imutils.resize(image, width=400)
        ret, jpeg = cv2.imencode('.jpg', image)
        frame = jpeg.tostring()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

@APP.route('/video_feed')
def video_feed():
    return Response(gen(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

class RestBrillo(Resource):
    def get(self):
        print ("CV_CAP_PROP_BRIGHTNESS",capturador.facedetector.camera.stream.get(cv2.cv.CV_CAP_PROP_BRIGHTNESS))
        print ("CV_CAP_PROP_CONTRAST",capturador.facedetector.camera.stream.get(cv2.cv.CV_CAP_PROP_CONTRAST))
        print ("CV_CAP_PROP_SATURATION",capturador.facedetector.camera.stream.get(cv2.cv.CV_CAP_PROP_SATURATION))
        print ("CV_CAP_PROP_HUE",capturador.facedetector.camera.stream.get(cv2.cv.CV_CAP_PROP_HUE))
        print ("CV_CAP_PROP_GAIN",capturador.facedetector.camera.stream.get(cv2.cv.CV_CAP_PROP_GAIN))
        print ("CV_CAP_PROP_EXPOSURE",capturador.facedetector.camera.stream.get(cv2.cv.CV_CAP_PROP_EXPOSURE))
        print ("CV_CAP_PROP_FRAME_WIDTH",capturador.facedetector.camera.stream.get(cv2.cv.CV_CAP_PROP_FRAME_WIDTH))
        print ("CV_CAP_PROP_FRAME_HEIGHT",capturador.facedetector.camera.stream.get(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT))
        return int(Conexion.opcion('brillo',50))
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('valor', required=True, type=int) 
        args = parser.parse_args() # throws 400
        brillo = args['valor']
        print ("post algo?", brillo)
        Conexion.escribir_opcion('brillo',brillo)
        capturador.facedetector.camera.stream.set(cv2.cv.CV_CAP_PROP_BRIGHTNESS,brillo/100.0)
        return int(Conexion.opcion('brillo',50))
REST.add_resource(RestBrillo, '/brillo')

class RestContraste(Resource):
    def get(self):
        print ("CV_CAP_PROP_BRIGHTNESS",capturador.facedetector.camera.stream.get(cv2.cv.CV_CAP_PROP_BRIGHTNESS))
        print ("CV_CAP_PROP_CONTRAST",capturador.facedetector.camera.stream.get(cv2.cv.CV_CAP_PROP_CONTRAST))
        print ("CV_CAP_PROP_SATURATION",capturador.facedetector.camera.stream.get(cv2.cv.CV_CAP_PROP_SATURATION))
        print ("CV_CAP_PROP_HUE",capturador.facedetector.camera.stream.get(cv2.cv.CV_CAP_PROP_HUE))
        print ("CV_CAP_PROP_GAIN",capturador.facedetector.camera.stream.get(cv2.cv.CV_CAP_PROP_GAIN))
        print ("CV_CAP_PROP_EXPOSURE",capturador.facedetector.camera.stream.get(cv2.cv.CV_CAP_PROP_EXPOSURE))
        print ("CV_CAP_PROP_FRAME_WIDTH",capturador.facedetector.camera.stream.get(cv2.cv.CV_CAP_PROP_FRAME_WIDTH))
        print ("CV_CAP_PROP_FRAME_HEIGHT",capturador.facedetector.camera.stream.get(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT))
        return int(Conexion.opcion('contraste',50))
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('valor', required=True, type=int) 
        args = parser.parse_args() # throws 400
        contraste = args['valor']
        print ("post algo?", contraste)
        Conexion.escribir_opcion('contraste',contraste)
        capturador.facedetector.camera.stream.set(cv2.cv.CV_CAP_PROP_CONTRAST,contraste/100.0)
        return int(Conexion.opcion('contraste',50))
REST.add_resource(RestContraste, '/contraste') # get JWT


if __name__ == '__main__':
    #print "iniciando conexion..."
    Conexion.iniciar()
    capturador = CaptThread()
    APP.run(host='0.0.0.0', port=config.HOSTPORT, threaded=True)

