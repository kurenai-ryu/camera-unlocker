#!/opt/.virtualenvs/fingerprint/bin/python2
# -*- coding: utf-8 -*-

import sys
import logging
import os
from threading import Thread
#import Queue
import math
import time
import cv2
import numpy as np
import config #dependemos de config
LOGGER = logging.getLogger(__name__)
def recortar(image, posx, posy, width, height):
    """
    Recortar imagen para identificacion de rostros.
    recorta la imagen en la misma proporcion para el
    entrenamiento de rostros.
    Pero requiere cambiar de tamanho posteriormente con reajustar()
    Args:
        image: imagen a recortar
        x: coordenada inicial x
        y: coordenada inicial y
        w: ancho del rostro detectado
        h: alto del rostro detectado
    Returns:
        imagen recortada en la proporcion requerida
    """
    crop_height = int((config.FACE_HEIGHT / float(config.FACE_WIDTH)) * width)
    midy = posy + height/2
    posy1 = max(0, midy-crop_height/2)
    posy2 = min(image.shape[0]-1, midy+crop_height/2)
    return image[posy1:posy2, posx:posx+width]
#end recortar
def reajustar(image):
    """
    Cambiar tamanho de la imagen.
    Args:
        image: imagen cv2 a cambiar de tamaño
    Returns:
        imagen del tamaño indicado en
        config.FACE_WIDTH y config.FACE_HEIGHT
    """
    return cv2.resize(image, (config.FACE_WIDTH, config.FACE_HEIGHT),
                      interpolation=cv2.INTER_LANCZOS4)
#end reajustar
def alinear(imagegray, rostro, eyes):
    """
    Alinea una imagen según la posición de los ojos
    Args:
        imagegray : imagegray()
        eyes      : tuppla con las coordenadas de los dos ojos
    """
    cx_l = eyes[0][0] + (eyes[0][2]/2)
    cy_l = eyes[0][1] + (eyes[0][3]/2)
    cx_r = eyes[1][0] + (eyes[1][2]/2)
    cy_r = eyes[1][1] + (eyes[1][3]/2)
    angle = math.atan2(cy_r-cy_l, cx_r-cx_l) * 180 / math.pi
    #print 'angle ',angle
    (hei, wid) = imagegray.shape[:2] #tamnhos de la imagen original
    rotado = cv2.getRotationMatrix2D((rostro[0]+(cx_l+cx_r)/2,
                                      rostro[1]+(cy_l+cy_r)/2),
                                     angle, 1.0)
    return cv2.warpAffine(imagegray, rotado, (wid, hei),
                          flags=cv2.INTER_LINEAR)
class FaceDetector(Thread):
    """
    Clase detectora de Rostros.
    Permite realizar el analisis de una imagen cv2 (array de numpy) para
    reconocer un rostro y alinear mediante los ojos.
    contiene tambien un modelo clasificador de imagenes
    que combinado con los rostros capturados permiten identificar a una persona
    """
    def _cargar_clasificadores(self):
        """solo clasificadores en haar[]"""
        self.haar["faces"] = cv2.CascadeClassifier(
            '/usr/share/opencv/haarcascades/%s' % config.HAAR_FACES)
        if self.haar["faces"].empty():
            LOGGER.error('no se pudo hallar clasificador de rostros')
            return
        self.haar["eyes"] = cv2.CascadeClassifier(
            '/usr/share/opencv/haarcascades/haarcascade_eye.xml')
        if self.haar["eyes"].empty():
            LOGGER.error('no se pudo hallar clasificador de ojos')
            return
        self.haar["glasses"] = cv2.CascadeClassifier(
            '/usr/share/opencv/haarcascades/haarcascade_eye_tree_eyeglasses.xml')
        if self.haar["glasses"].empty():
            LOGGER.error('no se pudo hallar clasificador de lentes')
            return
        self.haar["smile"] = cv2.CascadeClassifier(
            '/usr/share/opencv/haarcascades/haarcascade_smile.xml')
        if self.haar["smile"].empty():
            LOGGER.info('no se pudo hallar clasificador de sonrisa')
        if config.MODEL_RECOGNIZER == 'Eigen':
            LOGGER.info("Modelo de Reconocimiento EigenFace")
            self.haar["modelo"] = cv2.createEigenFaceRecognizer()
        elif config.MODEL_RECOGNIZER == 'Fisher':
            LOGGER.info("Modelo de Reconocimiento FisherFace")
            self.haar["modelo"] = cv2.createFisherFaceRecognizer()
        else: #else LBPH or another thing
            LOGGER.info("Modelo de Reconocimiento LBPHFace ")
            self.haar["modelo"] = cv2.createLBPHFaceRecognizer(radius=2)
    def _configurar_detectores(self):
        """parametros iniciales"""
        self.cfg["rostro"] = dict()
        self.cfg["rostro"]["scaleFactor"] = config.HAAR_SCALE_FACTOR
        self.cfg["rostro"]["minNeighbors"] = config.HAAR_MIN_NEIGHBORS
        self.cfg["rostro"]["minSize"] = config.HAAR_MIN_SIZE
        self.cfg["rostro"]["flags"] = cv2.CASCADE_SCALE_IMAGE
        self.cfg["ojos"] = dict()
        self.cfg["ojos"]["scaleFactor"] = 2.0
        self.cfg["ojos"]["minNeighbors"] = 2
        self.cfg["ojos"]["minSize"] = (10, 10)
        self.cfg["ojos"]["flags"] = cv2.CASCADE_SCALE_IMAGE
        self.cfg["lentes"] = dict()
        self.cfg["lentes"]["scaleFactor"] = 1.5
        self.cfg["lentes"]["minNeighbors"] = 2
        self.cfg["lentes"]["minSize"] = (30, 30)
        self.cfg["lentes"]["flags"] = cv2.CASCADE_SCALE_IMAGE
        self.cfg["boca"] = dict()
        self.cfg["boca"]["scaleFactor"] = config.HAAR_SCALE_FACTOR
        self.cfg["boca"]["minNeighbors"] = config.HAAR_MIN_NEIGHBORS
        self.cfg["boca"]["minSize"] = config.HAAR_MIN_SIZE
        self.cfg["boca"]["flags"] = cv2.CASCADE_SCALE_IMAGE
    def __init__(self):
        """
        Constructor.
        Inicializa la clase con el tipo de clasificador para rostros
        y el modelo de reconocimiento de rostros.
        El clasificador es un archivo XML en la carpeta harr y se define
        mediante config.HAAR_FACES
        El modelo de reconocimiento puede ser Eigen, Fisher o LBPH y se define
        mediante config.MODEL_RECOGNIZER
        """
        super(FaceDetector, self).__init__(name="FaceDetectorThread", args=())
        self.setDaemon(True)
        self.haar = dict()
        self._cargar_clasificadores()
        self.camera = None # se cargará con una instancia picamera()
        self.images = []
        self.labels = []
        self.trained = False
        self.cfg = dict()
        self._configurar_detectores()
        #thread flags
        self.finish = False
        self.search = False # don't search yet
        self.margin = None # Coords from the other side
        #thread_responses
        self.last = dict()
        self.last["imagen"] = None
        self.last["error"] = -1
        self.last["rostro"] = None
        self.last["valido"] = None
        self.last["coord"] = (0, 0, 0, 0)
        self.last["id"] = 0
        self.last["coef"] = config.POSITIVE_THRESHOLD*2
        self.start() #autostart detector
    #end init
    def parametro_detectores(self):
        """dict() de los parametros actuales"""
        return {
            "single":self.cfg["rostro"],
            "eyes":self.cfg["ojos"],
            "glasses":self.cfg["lentes"],
            "smile":self.cfg["boca"]} # for debug
    def limpiar_entrenamiento(self):
        """
        Limpiar e inicializar las listas para el
        entrenamiento del modelo de reconocimiento.
        """
        self.images = []
        self.labels = []
        self.trained = False
    #end limpiar_entrenamiento
    def agregar_entrenamiento(self, image, index):
        """
        Agregar una imagen para su entrenamiento.
        Args:
            image: imagen en escala de grises (numpy 2d)
                    de un solo tamaño (segun el config)
            index: indice asociado a la imagen
        """
        self.labels.append(index)
        self.images.append(image)
    #end agregar_entrenamiento
    def entrenar(self):
        """
        Entrenar el modelo de identificacion.
        Entrena el modelo en funcion de dos listas self.labels y self.images
        previamente llenadas mediante agregar_entrenamiento()
        """
        if len(self.labels) > 0:
            LOGGER.debug("Entrenando modelo")
            self.haar["modelo"].train(self.images, np.array(self.labels))
            LOGGER.debug("Modelo entrenado!")
            self.guardar_modelo()
            self.trained = True
        else:
            LOGGER.info("sin datos para entrenar")
    #end entrenar
    def guardar_modelo(self):
        """
        Guarda el modelo entrenado en el archivo
        XML definido en config.TRAINING FILE.
        """
        self.haar["modelo"].save(config.TRAINING_FILE)
    #end guardar_modelo
    def cargar_modelo(self):
        """
        Recupera un modelo entrenado del archivo
        XML definido en config.TRAINING FILE.
        """
        if os.path.exists(config.TRAINING_FILE):
            try:
                self.haar["modelo"].load(config.TRAINING_FILE)
                self.trained = True
                return True
            except cv2.error:
                LOGGER.debug("Error cargar_modelo: %s", sys.exc_info()[0])
                LOGGER.error("falla al abrir archivo de entrenamiento")
        else:
            LOGGER.debug("Archivo de entrenamiento no encontrado")
        return False
    #end cargar_modelo
    def predecir(self, image):
        """
        Realiza la prediccion de una imagen.
        la predicion consiste en la identificacion de un rostro segun
        el modelo entrenado.
        Args:
            image: imagen cv2 (numpy) a predecir. debe ser del mismo tamaño
                   que el de las imagenes
                   utilizadas para el entrenamiento.
        Returns:
            Tupla de dos elementos (id, coef) donde id corresponde al indice
            identificado y coef es el nivel de confiabilidad de la
            identificacion ( = 0, identificacion perfecta).
            Si el nivel es mayor a config.POSITIVE_THERSHOLD,
            el resultado se descarta (id=0)
        """
        self.last["valido"] = image.copy() # for further processing
        if not self.trained:
            return 0, config.POSITIVE_THRESHOLD*2
        uid, coef = self.haar["modelo"].predict(self.last["valido"])
        if coef > config.POSITIVE_THRESHOLD:
            LOGGER.info("face: intento  %s, coef: %s insuficiente", uid, coef)
            return 0, coef #if predict was valid but not enough coef...
        if uid < 0: #por si acaso, filtrar posibles entrenamientos negativos
            return 0, config.POSITIVE_THRESHOLD*2
        return uid, coef
    #end predecir
    def run(self):
        """
        bucle del hilo
        """
        LOGGER.info("iniciando bucle de deteccion de rostros")
        while True:
            if (self.camera is not None
                    and self.camera.read() is not None
                    and not self.finish):
                #print "trying detect"
                imagen = self.camera.read().copy() # cv2.flip(, 1)
                lab = cv2.cvtColor(imagen, cv2.COLOR_BGR2LAB)
                l, a, b = cv2.split(lab)
                clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(8,8))
                cl = clahe.apply(l)
                limg = cv2.merge((cl,a,b))
                self.last["imagen"] = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)
                (self.last["error"],
                 self.last["rostro"],
                 self.last["coord"]) = self.detect(l, self.margin)
                if self.last["error"] == 0 and self.search:
                    print "trying search"
                    (self.last["id"],
                     self.last["coef"]) = self.predecir(self.last["rostro"])
                self.finish = True
                time.sleep(0.1)
            else:
                #print "zzzz sleeping"
                time.sleep(0.1)
    #end run
    def detect(self, image, limit=None):
        """
        Realiza la deteccion de un rostro.
        Internamente convierte la imagen a escala de grises.
        Args:
            image: imagen cv2 (numpy) a analizar. esta debe
                   ser una imagen a colores RGB.
            limit: tupla (x0, y0, x1, y1) que define un marco límite
                   para la detección, por defecto None (sin limite)
        Returns:
            Devuelve una tupla (err, imageResult, imageCoord)
            imageCoord son las coordenadas del rostro detectado.
            imageResult es un rostro valido tamaño 92x112
                        (segun el config.py) cuando err es 0.
            si err = -1 no se encontro un rostro valido
            si err = -2 se identifico un rostro, pero no se encontró los ojos.
        """
        # a grises
        #imagegraylow = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        #image = cv2.equalizeHist(imagegraylow)
        # Get coordinates of single face in captured image.
        rostro = self._detectar_rostro(image)
        if rostro is None:
            #print 'No se encontro un rostro valido!'
            return -1, None, None
        #x, y, w, h = rostro
        crp = recortar(image, rostro[0], rostro[1], rostro[2], rostro[3])
        return 0, reajustar(crp), rostro
        #end
        indface = image[rostro[1]:rostro[1]+rostro[3],
                            rostro[0]:rostro[0]+rostro[2]]
        #just the face, no resize,
        eyes = self._detectar_ojos(indface)
        if eyes is None:
            print 'no se encontraron ojos!'
            return -2, None, None
        #cv2.rectangle(image,(x,y),(x+w,y+h),(255,0,0),2)
        if limit is not None and isinstance(limit, tuple):
            # limit[0] x0, limit[1] y0, limit[2] x1, limit[3] y1
            if (rostro[0] < limit[0] or rostro[0]+rostro[2] > limit[2]
                    or rostro[1] < limit[1] or rostro[1]+rostro[3] > limit[3]):
                print 'No se encontro un rostro valido!'
                return -1, None, rostro #but draw the border!
        #for (ex,ey,ew,eh) in eyes:
        #    cv2.rectangle(image,(x+ex,y+ey),(x+ex+ew,y+ey+eh),(0,255,0),2)
        # ponerle borde verde
        #centro de los ojos
        imageang = alinear(image, rostro, eyes)
        rostro2 = self._detectar_rostro(imageang)
        if rostro2 is None:
            print 'Could not detect single face after all!'
            return -1, None, None
        crp = recortar(imageang, rostro2[0], rostro2[1], rostro2[2], rostro2[3])
        return 0, reajustar(crp), rostro
    #end detect
    def _detectar_rostro(self, image):
        """
        Detecta un solo rostro.
        Args:
            image: imagen cv2 (numpy) a analizar. debe ser una imagen en
            escala de grises.
        Returns:
            tupla rectangular (x, y, width, height) del rostro detectado.
            si se identifica mas de un rostro, o no se encuentra ninguno,
            se retorna None.
        """
        faces = self.haar["faces"].detectMultiScale(
            image,
            scaleFactor=self.cfg["rostro"]["scaleFactor"],
            minNeighbors=self.cfg["rostro"]["minNeighbors"],
            minSize=self.cfg["rostro"]["minSize"],
            flags=self.cfg["rostro"]["flags"])
        if len(faces) < 1:
            return None
        if len(faces) == 1:
            return faces[0] #tupla de coordenadas
        #else look for bigger
        m_face = np.array(faces)
        return faces[np.argmax(m_face[:, 2])]
    #end _detectar_rostro
    def _detectar_ojos(self, imagen):
        """
        Detecta ambos ojos.
        Returns:
            tupla de dos coordenadas rectangulares, correspondientes a los
            ojos izquierdo y derecho.
            si no encuentra los dos ojos, retorna None.
        """
        eyes = self.haar["eyes"].detectMultiScale(
            imagen,
            scaleFactor=self.cfg["ojos"]["scaleFactor"],
            minNeighbors=self.cfg["ojos"]["minNeighbors"],
            minSize=self.cfg["ojos"]["minSize"],
            flags=self.cfg["ojos"]["flags"])
        if len(eyes) != 2: #try glasses?
            eyes = self.haar["glasses"].detectMultiScale(
                imagen,
                scaleFactor=self.cfg["lentes"]["scaleFactor"],
                minNeighbors=self.cfg["lentes"]["minNeighbors"],
                minSize=self.cfg["lentes"]["minSize"],
                flags=self.cfg["lentes"]["flags"])
            if len(eyes) != 2:
                return None
        #check alignment?
        if eyes[0][0] > eyes[1][0]: #first 1
            eyes = eyes[1], eyes[0]
            #print 'Eye swap'
        if eyes[1][0] < (eyes[0][0]+eyes[0][2]): #overlap
            return None
        if ((eyes[1][1] > eyes[0][1]
             and eyes[1][1] < eyes[0][1]+eyes[0][3]) or (
                 eyes[0][1] > eyes[1][1]
                 and eyes[0][1] < eyes[1][1]+eyes[1][3])):
            #print 'found eyes!'
            return eyes[0], eyes[1]
        return None
    #end _detectar_ojos
    def _detectar_sonrisa(self, image):
        """
        Detecta una sonrisa!
        Args:
            image - imagen cv2 del rostro a buscar (para evitar falso-positivos
                    en el resto de la imagen)
        Returns: tupla rectangular (x,y,w,h) de la sonrisa detectada
        """
        smiles = self.haar["smile"].detectMultiScale(
            image,
            scaleFactor=self.cfg["boca"]["scaleFactor"],
            minNeighbors=self.cfg["boca"]["minNeighbors"],
            minSize=self.cfg["boca"]["minSize"],
            flags=self.cfg["boca"]["flags"])
        if len(smiles) < 1:
            return None
        return smiles[0]
    #end detect_smile
#end class

