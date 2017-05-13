#!/opt/.virtualenvs/fingerprint/bin/python2
# -*- coding: utf-8 -*-
"""
CONFIGURACIÓN INICIAL DEL SISTEMA
Cambiar los valores acorde sea necesario.
Algunos valores se pueden definir mediante variables de entorno,
consulte la documentación.
Configuración de Comunicación:
Estos valores de configuración se pueden poblar mediante variables de entorno
para ello se puede utilizar el archivo (configruacion/envvars) donde se exporte
las variables de entorno necesarias, y luego hacer un 'source' antes de iniciar
el programa
Estas variables son muy importantes para
iniciar la comunicación con la(s) base de datos
de donde se puede obtener el resto de las configuraciones.
TODO: obtener el resto de las configuraciones desde la BD.
"""
# Código inicial basado en Treasure Box by Tony DiCola 2013
import sys
import os
import logging
#import snowflake
LOGGER = logging.getLogger(__name__)
sys.path.append(os.path.abspath(".."))
sys.path.append(os.path.abspath("../configuracion"))

def str2bool(cadena):
    """retorna un booleano a partir de una cadena [yes,true,t] o numero 1 """
    return cadena.lower() in ("yes", "true", "t", "1")
LOGGER.info("Cargando configuración por defecto")

# Datos de comunicacion a DB principal
PGHOST = os.getenv('PGHOST', "localhost")
PGPORT = os.getenv('PGPORT', 5432)
PGDATABASE = os.getenv('PGDATABASE', "database")
PGUSER = os.getenv('PGUSER', "postgres")
PGPASSWORD = os.getenv('PGPASSWORD', "*******")

# datos del servicio http para acceso api REST
# pueden venir mediante variables de entorno
HOSTNAME = os.getenv('HOSTADDR', "0.0.0.0")
HOSTPORT = int(os.getenv('HOSTPORT', 5000))

# Tamaño en pixeles de las imagenes de entrenamiento y predicción de rostros
# **No cambiar a menos que se registren todas las fotos nuevamente**
FACE_WIDTH = 92
FACE_HEIGHT = 112

# Umbral de confianza del modelo, depende mucho del tipo de modelo,
# cuanto mas cercano a 0, el modelo es mas exacto.
POSITIVE_THRESHOLD = 100.0 #elias test

# Archivo para guardar el modelo entrenado!
TRAINING_FILE = 'training.xml'

# Configuración del clasificador por cascada
# No modificar a menos que sepa lo que está haciendo
# See: http://docs.opencv.org/modules/objdetect/doc/cascade_classification.html
HAAR_FACES = 'haarcascade_frontalface_alt.xml'
HAAR_SCALE_FACTOR = 1.1
HAAR_MIN_NEIGHBORS = 5
HAAR_MIN_SIZE = (30, 30)

# Modelo de REconocimiento:
# puede ser 'LBPH' 'Eigen' 'Fisher'
# por defecto 'LBPH'
MODEL_RECOGNIZER = 'LBPH'

#tiempo de conteo para cancelar registro
REG_TIMEOUT = 300

