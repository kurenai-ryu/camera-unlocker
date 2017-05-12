#!/usr/bin/python
# -*- coding: utf-8 -*-

# import the necessary packages
from __future__ import print_function

from flask import Flask, render_template, Response
from flask_restful import Api, Resource, reqparse

import sys
import os
import wiringpi
import logging
from imutils.video import WebcamVideoStream
import config
import imutils
import cv2
import time
import base64

from conexion import Conexion
from personal import Personal, lista_usuarios
from face import FaceDetector
from threading import Thread, Timer
import gpio


#configuración inicia de bitácora
if __name__ == '__main__': #logging para los modulos
    logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s',datefmt='%Y-%m-%d %H:%M:%S', level=logging.DEBUG)
    LOGGER = logging.getLogger(__name__)
    def handle_exception(exc_type, exc_value, exc_traceback):
        """captura excepciones en la misma bitácora"""
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        LOGGER.error("Uncaught exception",
                     exc_info=(exc_type, exc_value, exc_traceback))
    sys.excepthook = handle_exception


caputador = None

print("[INFO] sampling THREADED frames from webcam...")
#vs.stream.set(cv2.cv.CV_CAP_PROP_BRIGHTNESS,1.0)

class CaptThread(Thread):
    def __init__(self):
        super(CaptThread, self).__init__(name="CaptThread", args=())
        self.setDaemon(True) #it's still dependant of mainthread
        self.facedetector = FaceDetector()
        self.img = dict() #las imagenes cv2 (numpy) como tal
        self.img["logo"] = cv2.imread('templates/logo.jpg') 
        self.img["camara"] = self.img["logo"] # para despliegue inicial
        self.img["inst"] = self.img["logo"]
        self.start()
    def message(self, mestr):
        """ Mensaje para el thread
        Args:
            mestr: mensaje
        Returns:
            self, la instancia misma para encadenar el wait()
        """
        self.mensaje_hilo.put(mestr)
        return self #para encadenar el wait
    #end message
    def busy(self):
        """ Capturador se encuentra ocupado.
        Returns:
            True si se encuentra realizando una tarea:
                (registro, entrenamiento,etc)
            False si se encuentra disponible en modo captura.
        """
        return bool(self.cnt["estado"] != 1)
    #end busy
    def wait(self): #todo, add timeout here?
        """ Esperar al capturador.
        bloquea esta ejecucion hasta que el capturador a finalizado sus tareas
        pendientes (mediante el Queue generado por Capturador.message() )

        Este método se debe llamar desde el thread principal si se quiere
        esperar a finalizar una tarea, nunca llamar desde este mismo thread del
        capturador ya que no le dará oportunidad de finalizar la tarea si se
        autobloquea.
        """
        self.mensaje_hilo.join() # will block?
        LOGGER.debug("Wait finnished!")
    #end wait
    def _cargar_rostros_archivo(self):
        """ Inicia la carga del modelo de rostros. """
        LOGGER.debug("Cargando Archivo de Entrenamiento")
        if self.facedetector is None:
            LOGGER.debug("sin entrenador")
            return
        if not self.facedetector.cargar_modelo():
            LOGGER.debug("Falla de Archivo...")
            self._entrenar_rostros()
        else:
            LOGGER.debug("Finalizado carga de Archivo")
    def _entrenar_rostros(self):
        """ Inicia un entrenamiento de Rostros. """
        if self.facedetector is None:
            LOGGER.debug("sin entrenador")
            return
        LOGGER.debug("Iniciando Entrenamiento de Rostros")
        self.facedetector.limpiar_entrenamiento()
        for i in Personal.usuarios:
            usu = Personal.usuarios[i]
            rostros = usu.obtener_rostros()
            for rin in rostros:
                #LOGGER.debug("adding face from user %i" % usu.pid) #funciona...
                self.facedetector.agregar_entrenamiento(rostros[rin], usu.pid)
        self.facedetector.entrenar()
        LOGGER.debug("Finalizado Entrenamiento de Rostros")

    def run(self):
        LOGGER.info("iniciando hilo captura")
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
        LOGGER.error("finalizado hilo!!!")
    #end run
    def empezar(self,brillo,contraste):
        self.facedetector.camera = WebcamVideoStream(src=0).start()
        self.facedetector.camera.stream.set(cv2.cv.CV_CAP_PROP_BRIGHTNESS,brillo/100.0)
        self.facedetector.camera.stream.set(cv2.cv.CV_CAP_PROP_CONTRAST,contraste/100.0)
    #end empezar
    def entrenamiento_inicial(self):
        LOGGER.info("Iniciando carga de imagenes")
        self.facedetector.limpiar_entrenamiento()
        for pid in Personal.usuarios:
            rostros = Personal.usuarios[pid].obtener_rostros()
            for r in rostros:
                self.facedetector.agregar_entrenamiento(rostros[r], pid)
        LOGGER.info("Iniciando entrenamiento")
        self.facedetector.entrenar()
        LOGGER.info("Entrenamiento Finalizado.")
    #end cargar_datos

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

class RestPersonal(Resource):
    def get(self): # get /personal
        return [Personal.usuarios[i].dict() for i in Personal.usuarios]
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('usuario', required=True) #type=int,
        parser.add_argument('tipo', type=int, required=True) #
        args = parser.parse_args() # throws 400
        usuario = Personal(personal_id=0, usuario=args['usuario'])
        usuario.tipo_acceso = args['tipo']
        usuario.activo = True
        usuario.habilitado = True #hardcode
        usuario.crear()
        return usuario.dict()
REST.add_resource(RestPersonal, '/personal')
        
class RestPersonalId(Resource):
    def get(self,pid):
        if pid in Personal.usuarios:
            return  Personal.usuarios[pid].dict()
        else: 
            return {
                "description": "no existe usuario",
                "error": "Not Found",
                "status_code": 404}, 404

REST.add_resource(RestPersonalId,'/personal/<int:pid>')

class RestRostros(Resource):
    def get(self,pid):
        parser = reqparse.RequestParser()
        parser.add_argument('index', required=False, type=int, default=0)
        args = parser.parse_args() # throws 400
        index = args['index']

        if pid in Personal.usuarios:
            usuario = Personal.usuarios[pid]
        else: 
            return {
                "description": "no existe usuario",
                "error": "Not Found",
                "status_code": 404}, 404
        images = usuario.obtener_rostros()
        if len(images) > 0:
            if index >= 0:
                if index >= len(images):
                    index = len(images)-1
                dummy, image = images.popitem()
                for _ in range(index):
                    dummy, image = images.popitem() #extra pop!
                mempgm = cv2.imencode('.png', image)[1]
                response = APP.make_response(mempgm.tostring()) #RAW
                """response = APP.make_response(
                    "data:image/png;base64,%s" %
                    base64.b64encode(mempgm.tostring())) #to bytes antiguo"""
                response.headers['content-type'] = 'image/png;base64'
                return response
            else: #responde un array(list)
                response = dict()
                for i in images:
                    mempgm = cv2.imencode('.png', images[i])[1]
                    response[i] = (
                        "data:image/png;base64,%s" %
                        base64.b64encode(mempgm.tostring()))
                return response
        else:
            return {
                "description": "no existen rostros registrados",
                "error": "Empty",
                "status_code": 204}, 204
    def post(self, pid):
        if pid in Personal.usuarios:
            usuario = Personal.usuarios[pid]
        else: 
            return {
                "description": "no existe usuario",
                "error": "Not Found",
                "status_code": 404}, 404
        capturador.facedetector.last["error"] = -1
        capturador.empezar(int(Conexion.opcion('brillo',50)),int(Conexion.opcion('contraste',50)))
        gpio.on(gpio.LED_ROJO)
        time.sleep(5)
        gpio.off(gpio.LED_ROJO)
        gpio.on(gpio.LED_AMARILLO)
        ready = False
        for i in range(60):
            if ready:
                continue
            if capturador.facedetector.last["error"] == 0:
                usuario.guardar_rostro(capturador.facedetector.last["rostro"])
                ready = True
                continue
            time.sleep(0.5)
        capturador.facedetector.camera.stop()
        time.sleep(0.1)
        capturador.facedetector.camera=None
        gpio.off(gpio.LED_AMARILLO)
        if not ready:
            gpio.on(gpio.LED_ROJO)
            Timer(5,gpio.leds_off).start()
            return {
                "description": "no se encontró un rostro valido",
                "error": "Internal Error",
                "status_code": 500}, 500
        #sino entrenar
        capturador.entrenamiento_inicial()
        gpio.on(gpio.LED_VERDE)
        Timer(5,gpio.leds_off).start()
        return {
            "description": "rostro registrado",
            "error": "OK",
            "status_code": 200}, 200
    def delete(self,pid):
        if pid in Personal.usuarios:
            usuario = Personal.usuarios[pid]
        else: 
            return {
                "description": "no existe usuario",
                "error": "Not Found",
                "status_code": 404}, 404
        usuario.borrar_rostros_persona()
        capturador.entrenamiento_inicial()
        return {
            "description": "rostros eliminados",
            "error": "Empty",
            "status_code": 204}, 204
REST.add_resource(RestRostros,'/personal/<int:pid>/rostros')


class RestBuscador(Resource):
    def get(self):
        pid = 0
        capturador.facedetector.last["error"] = -1
        capturador.empezar(int(Conexion.opcion('brillo',50)),int(Conexion.opcion('contraste',50)))
        gpio.leds_off() #jic
        gpio.on(gpio.LED_ROJO)
        time.sleep(5)
        gpio.off(gpio.LED_ROJO)
        gpio.on(gpio.LED_AMARILLO)
        capturador.facedetector.last["id"] = -1
        capturador.facedetector.search = True
        ready = False
        for i in range(60):
            if ready:
                continue
            if capturador.facedetector.lat["id"] > 0: #from bd 1 or more
                pid = capturador.facedetector.last["id"]
                print ("encontradoo!!!!", pid)
                ready = True
                continue
            time.sleep(0.5)
        gpio.off(gpio.LED_AMARILLO)
        capturador.facedetector.search = False
        capturador.facedetector.camera.stop()
        time.sleep(0.1)
        capturador.facedetector.camera=None
        if not ready:
            gpio.on(gpio.LED_ROJO)
            Timer(5,gpio.leds_off).start()
            return {
                "description": "no se encontró un rostro valido",
                "error": "Internal Error",
                "status_code": 500}, 500
        #sino identificar
        gpio.on(gpio.LED_VERDE)
        gpio.on(gpio.RELE)
        Timer(15,gpio.leds_off).start()
        return {
            "description": "rostro identificado",
            "usuario":Personal.usuarios[pid].dict(),
            "error": "OK",
            "status_code": 200}, 200
REST.add_resource(RestBuscador,'/buscar')

class RestBrillo(Resource):
    def get(self):
        if capturador.facedetector.camera:
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
        if capturador.facedetector.camera:
            capturador.facedetector.camera.stream.set(cv2.cv.CV_CAP_PROP_BRIGHTNESS,brillo/100.0)
        return int(Conexion.opcion('brillo',50))
REST.add_resource(RestBrillo, '/brillo')

class RestContraste(Resource):
    def get(self):
        if capturador.facedetector.camera:
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
        if capturador.facedetector.camera:
            capturador.facedetector.camera.stream.set(cv2.cv.CV_CAP_PROP_CONTRAST,contraste/100.0)
        return int(Conexion.opcion('contraste',50))
REST.add_resource(RestContraste, '/contraste') # get JWT



if __name__ == '__main__':
    #print "iniciando conexion..."
    Conexion.iniciar()
    capturador = CaptThread()
    capturador.entrenamiento_inicial()
    APP.run(host='0.0.0.0', port=config.HOSTPORT, threaded=True)


