#!/opt/.virtualenvs/fingerprint/bin/python2
# -*- coding: utf-8 -*-

import logging
import datetime

import psycopg2
import cv2 # para convertir la imagen a cv2
import numpy as np #para ller de buffer a numpy array

import config
import conexion # no puede ser from conexion import...

LOGGER = logging.getLogger(__name__)

def is_number(cadena):
    """retorna True si el argumento es un número entero o flotante"""
    try:
        float(cadena)
        return True
    except (ValueError, TypeError):
        return False


class Personal(object):
    """
    Clase personal

    mantiene una lista estática del personal,
    asi como buscar una instancia en esta lista
    """
    conn = None #llenar en cuanto se tenga una conexion
    usuarios = dict()
    hashids = None #poblar en otro lado

    @staticmethod
    def conectar(es_servidor=False):
        """
        Realizar la inicialización de la clase,
        obtener una(1) conexion a la base de datos
        """
        conn_string = "host=%s port=%s dbname=%s user=%s password=%s" % (
            config.PGHOST,
            config.PGPORT,
            config.PGDATABASE,
            config.PGUSER,
            config.PGPASSWORD)
        Personal.conn = psycopg2.connect(conn_string)
    #end conectar
    @staticmethod
    def buscar(key=None, usuario=None, uid=0, solo_habilitados=False):
        """
        Buscar usuario por uid o id en la lista Personal.usuarios,

        Args:
            key: personal_id o usuario a buscar
            usuario: nombre uid del usuario a buscar (opcional)
            uid: id de la base de datos del usuario a buscar
            solo_habilitados: forzar sólo usuarios habilitados?

        Returns:
            instancia Personal del usuario encontrado,
            o None si no existe un usuario con ese nombre
        """
        if is_number(key) and uid == 0:
            uid = int(key)
        elif usuario is None:
            usuario = key
        if uid > 0:
            if uid in Personal.usuarios:
                usu = Personal.usuarios[uid]
                if not solo_habilitados or usu.habilitado:
                    return usu
                else:
                    LOGGER.warning("usuario %i no habilitado!", uid)
                    return None
            else:
                LOGGER.warning("No existe usuario con indice %i", uid)
        elif usuario is not None:
            for uid in Personal.usuarios:
                if Personal.usuarios[uid].usuario == usuario:
                    usu = Personal.usuarios[uid]
                    if not solo_habilitados or usu.habilitado:
                        return usu
                    else:
                        LOGGER.warning("usuario %s no habilitado!", usuario)
                        return None
            LOGGER.warning("no se encontro usuario = %s", usuario)
        return None
    #end search
    @staticmethod
    def crear_root(acceso=3):
        """Crea una instancia de Personal para autenticacion de admins"""
        root = Personal(personal_id=0)
        root.pid = 0 # lo unico que se irá?
        root.nombre = ""
        root.usuario = ""
        root.cargo = "pg_local"
        root.carnet = "0"
        root.tipo_acceso = acceso # root
        if acceso == 0:
            root.nombre = "usuario"
            root.usuario = "usuario"
            root.cargo = "usuario"
        elif acceso == 1:
            root.nombre = "jefe-unidad"
            root.usuario = "jefe-unidad"
            root.cargo = "jefe-unidad"
        elif acceso == 2:
            root.nombre = "rrhh"
            root.usuario = "rrhh"
            root.cargo = "Recursos Humanos"
            root.rrhh = 1
        elif acceso == 3:
            root.nombre = "admin"
            root.usuario = "admin"
            root.cargo = "Administrador"
            root.rrhh = 1
        else:
            root.nombre = "guest"
            root.usuario = "guest"
            root.cargo = "Visitante"
        root.num_huellas = 0 #no tiene nada..
        root.num_rostros = 0
        return root

    def __init__(self, personal_id=0, usuario=None, data=None):
        """
        Constructor:

        Crea una instancia de una persona,

        si se indica el id:
            buscará la información en la base de datos y luego en LDAP
        si se indica el usuario:
            igualmente se buscará en la base de datos y luego LDAP
        si se indica la data:
            se asumirá como respuesta de la consulta LDAP

        Args:
            personal_id: id de la persona a buscar
            usuario: nombre de usuario de la persona a instanciar
            data: dict{nombre, usuario, cargo} de una consulta ldap
        """
        self.pid = personal_id # reemplazar luego
        self.usuario = "usuario"
        self.nombre = "usuario"
        self.cargo = "sin cargo"
        self.carnet = "0"
        self.tipo_empleado = ""
        self.tipo_acceso = -1 #guest?
        self.rrhh = False #nunca!
        self.num_huellas = 0
        self.num_rostros = 0
        self.activo = False #por defecto usuarios desactivador
        self.habilitado = False #por defecto usuarios deshabilitados
        #calculos e inferencias adicionales:
        if self.pid > Personal.maxFing:
            Personal.maxFing = self.pid
    #end __init__()
    def fix_ldap(self, data):
        """
        Corrige la instancia con los datos de LDAP

        Args:
            data dict {
                "nombre",
                "usuario",
                "cargo",
                "carnet",
                ["tipo_empleado"]}
            con los datos del ldap
        """
        self.nombre = data["nombre"]
        self.usuario = data["usuario"]
        self.cargo = data["cargo"]
        self.carnet = data["carnet"]
        self.tipo_acceso = 0 #acceso personal básico
        # 0: basico individual, 1:jefe de area, 2:rrhh, 3:administrador
        self.activo = True
        if "tipo_empleado" in data:
            self.tipo_empleado = data["tipo_empleado"]
            self.tipo_acceso = 1 # defaults a jefe de area
            if self.tipo_empleado.find("rrhh") != -1:
                self.tipo_acceso = 2 #redundante?
        if self.cargo.lower().find("recursos humanos") != -1: #redundante rrhh
            self.rrhh = True
            self.tipo_acceso = 2
    #end fix
    def habilitar(self):
        """habilita en la BD a un usario"""
        if not self.activo:
            LOGGER.error(
                "no se puede habilitar usuario desactivado en LDAP: %s",
                self.usuario)
            return
        with Personal.conn as conn:
            with conn.cursor() as cur:
                LOGGER.info("habilitando usuario %s", self.usuario)
                cur.execute("UPDATE personal SET habilitado=%s WHERE id = %s",
                            (True, self.pid))
                self.habilitado = True
            conn.commit()#trigger notify
    #end habilitar
    def deshabilitar(self):
        """deshabilita un usuario"""
        with Personal.conn as conn:
            with conn.cursor() as cur:
                LOGGER.info("deshabilitando usuario %s", self.usuario)
                cur.execute("UPDATE personal SET habilitado=%s WHERE id = %s",
                            (False, self.pid))
                self.habilitado = False
            conn.commit()#trigger notify
    #end deshabilitar
    def __repr__(self):
        return self.__str__()
    def __str__(self):
        return "{id:%3i,usuario:%15s,nombre:%s,cargo:%s}\n" % (
            self.pid,
            self.usuario,
            self.nombre,
            self.cargo)
    def __unicode__(self):
        return unicode(str(self))
    #end __str__
    def dict(self):
        """
        Retorna un dict simplificado de la instancia,
        para compartir la lista de personal
        """
        return {"id":self.pid,
                "usuario":self.usuario,
                "nombre":self.nombre,
                "cargo":self.cargo,
                "huella":self.num_huellas,
                "rostros":self.num_rostros,
                "tipo_empleado":self.tipo_empleado,
                "tipo_acceso":self.tipo_acceso,
                "habilitado":self.habilitado,
                "activo":self.activo}
    #end dict() TODO: test and use __DICT__
    def obtener_rostros(self):
        """
        Obtener la lista de imágenes para su entrenamiento.

        Returns:
            dict{id:imagen,...} de rostros como imagenes cv2 (array numpy)
        """
        rostros = dict()
        with Personal.conn as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, rostro_imagen
                    FROM rostros
                    WHERE personal_id=%s;""", (self.pid,))
                for res in cur:
                    rostros[res[0]] = cv2.imdecode(
                        np.frombuffer(res[1], np.uint8), 0)
        return rostros
    #end obtener_rostros

    def guardar_rostro(self, imagen_fc):
        """
        Guardar la imagen del rostro

        Args:
            imagen_fc: imagen del rostro a almacenar en cv2
        """
        with Personal.conn as conn:
            with conn.cursor() as cur:
                hoy = datetime.datetime.today().replace(microsecond=0)
                mempng = cv2.imencode('.png', imagen_fc)[1]
                cur.execute("""
                    INSERT INTO rostros(personal_id, rostro_imagen, fechahora)
                    VALUES(%s,%s,%s);""", (
                        self.pid, psycopg2.Binary(mempng), hoy))
            conn.commit()
        self.num_rostros += 1
        #debemos guardar la imagen también en archivo?
    #end guardar_rostro
    def guardar_rostro_temporal(self, image_fc):
        """
        almacena temporalmente un rostro

        Args:
            imagen_fc: imagen del rostro a guardar en la carpeta de mas_pruebas
        """
        hoy = datetime.datetime.today().replace(microsecond=0)
        #_retval,mempng=cv2.imencode('.png',imagen_fc)
        ret = cv2.imwrite('mas_pruebas/%s_%s.png' % (
            self.usuario, hoy.strftime("%Y%m%d-%H%M%S")), image_fc)
        print "guardado? ", ret
    #end guardar_rostro_temporal
    def borrar_rostro(self, image_id):
        """
        Borra un rostro determinado

        Args:
            image_id: id de la imagen a borrar
        """
        borrado = False
        with Personal.conn as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT rostro_imagen
                    FROM rostros
                    WHERE personal_id=%s AND id=%s;""", (self.pid, image_id))
                res = cur.fetchone()
                if res is None:
                    return False
                cur.execute("""
                    DELETE FROM rostros
                    WHERE personal_id=%s AND id=%s;""", (self.pid, image_id))
                if cur.rowcount > 0: # debería ser 1
                    self.num_rostros -= 1
                    borrado = True
            conn.commit()
        return borrado
    #end borrar_rostro
    def borrar_rostros_persona(self):
        """
        Borrar todos los rostros de esta persona
        """
        borrado = False
        with Personal.conn as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    DELETE FROM rostros
                    WHERE personal_id = %s ;""", (self.pid,))
                if cur.rowcount > 0: # si es 0 es que no hay, si es -1 error
                    self.num_rostros = 0
                    borrado = True
            conn.commit()
        return borrado
    #end prugeRostro
    @staticmethod
    def borrar_rostros_sistema():
        """borrar todos los rostros del sistema, requiere reentrenar"""
        #estas completamente seguro? únicamente para motivos de prueba eh?
        borrados = 0
        with Personal.conn as conn:
            with conn.cursor() as cur:
                cur.execute("TRUNCATE TABLE rostros RESTART IDENTITY;")
                borrados = cur.rowcount
            conn.commit()
        for usr in Personal.usuarios:
            Personal.usuarios[usr].num_rostros = 0
        return borrados
    #end borrar_rostros_sistema
   
#end class