#!/opt/.virtualenvs/fingerprint/bin/python2
# -*- coding: utf-8 -*-
"""
Conexión general a base de datos.

"""
#requerimientos:
# [sudo apt-get install] libpq-dev
# [sudo] pip install psycopg2 -o- sudo apt-get install python-psycopg2
# [sudo] pip install cv2 -o. sudo apt-get install python-opencv
# [sudo] pip install numpy


import sys
import logging

import psycopg2

import config
#import personal

LOGGER = logging.getLogger(__name__)

class Conexion(object):
    """
    Conexión a la base de datos y al LDAP.
    """
    conn = None # conexión general
    local = None
    identificador = ""
    @staticmethod
    def iniciar(es_servidor=False):
        """
        Constructor de la conexíón.

        utiliza las datos de config.py

        Si cae la conexión, no podemos hacer nada.
        sin base de datos, no se puede realizar registros.
        """
        conn_string = "host=%s port=%s dbname=%s user=%s password=%s"%(
            config.PGHOST,
            config.PGPORT,
            config.PGDATABASE,
            config.PGUSER,
            config.PGPASSWORD)
        #print conn_string #debug
        try:
            Conexion.conn = psycopg2.connect(conn_string)
        except psycopg2.Error:
            LOGGER.debug("Error main conn: %s", sys.exc_info()[0])
            LOGGER.error("Sin conexión a BD principal Finalizando todo...")
            print "sin BD principal finalizando...(END)"
            exit()

        Conexion._crear_estructura() # cuidado
        Conexion.identificador = Conexion.opcion("machine-name", "raspi")
        #personal.Personal.conectar(es_servidor) # conexion propia
    #end iniciar
    @staticmethod
    def _crear_estructura():
        """Cuidado! puede dañar el sistema """
        with Conexion.conn as conn:
            with conn.cursor() as cur:
                cur.execute(""" CREATE TABLE IF NOT EXISTS personal(
                                    id SERIAL PRIMARY KEY,
                                    usuario VARCHAR(40) not null ,
                                    tipo INTEGER DEFAULT '0',
                                    habilitado BOOLEAN DEFAULT FALSE,
                                    ingreso TIMESTAMP DEFAULT NOW());

                                CREATE TABLE IF NOT EXISTS rostros(
                                    id SERIAL PRIMARY KEY,
                                    personal_id INTEGER,
                                    rostro_imagen BYTEA,
                                    fechahora TIMESTAMP DEFAULT NOW());
                                CREATE TABLE IF NOT EXISTS opciones(
                                    id SERIAL PRIMARY KEY,
                                    nombre VARCHAR(50),
                                    valor TEXT);
                                CREATE OR REPLACE FUNCTION notify_trigger()
                                    RETURNS trigger AS $$
                                    DECLARE
                                        id bigint;
                                    BEGIN
                                        IF TG_OP = 'INSERT'
                                        OR TG_OP = 'UPDATE' THEN
                                            id = NEW.id;
                                        ELSE
                                            id = OLD.id;
                                        END IF;
                                     PERFORM pg_notify(
                                        CAST(TG_TABLE_NAME AS text),
                                        CAST(TG_OP AS text) || ' ' || id);
                                     RETURN NEW;
                                    END;
                                    $$ LANGUAGE plpgsql;
                                DROP TRIGGER IF EXISTS
                                    personal_trigger ON personal;
                                CREATE TRIGGER
                                    personal_trigger
                                    AFTER insert or update or delete
                                    ON personal
                                    FOR EACH ROW
                                        execute procedure notify_trigger();
                                DROP TRIGGER IF EXISTS
                                    rostros_trigger ON rostros;
                                CREATE TRIGGER
                                    rostros_trigger
                                    AFTER insert or update or delete
                                    ON rostros
                                    FOR EACH ROW
                                        execute procedure notify_trigger();
                            """)
            conn.commit()

        #verificar datos iniciales
        if Conexion.opcion("camera-refresh") is None:
            Conexion.escribir_opcion("camera-refresh", "100")
        if Conexion.opcion("machine-name") is None:
            Conexion.escribir_opcion("machine-name", "OFICINA")
    #end _crear_estructura
    @staticmethod
    def opcion(nombre, default=None):
        """ Lee una opción en la BD Principal"""
        with Conexion.conn as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT valor
                    FROM opciones
                    WHERE nombre = %s
                    LIMIT 1;""", (nombre,))
                res = cur.fetchone()
                if res is None:
                    return default
                else:
                    return res[0]
    #end opcion
    @staticmethod
    def lista_opciones():
        """ Listado de las opciones locales [exceptuando root]"""
        opciones = []
        with Conexion.conn as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT nombre, valor
                    FROM opciones
                    WHERE nombre NOT LIKE '%root%'
                    ORDER BY nombre ASC;""")
                opciones = [
                    {
                        "nombre":res[0],
                        "valor":res[1]
                    } for res in cur]
        return opciones
    @staticmethod
    def escribir_opcion(nombre, valor):
        """ Escribir una opción en la BD Principal"""
        with Conexion.conn as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT valor
                    FROM opciones
                    WHERE nombre = %s
                    LIMIT 1;""", (nombre,))
                res = cur.fetchone()
                if res is None:
                    cur.execute("""
                        INSERT INTO opciones(nombre,valor)
                        VALUES(%s,%s)""", (nombre, valor))
                else:
                    cur.execute("""
                        UPDATE opciones
                        SET valor=%s
                        WHERE nombre = %s ;""", (valor, nombre))
            conn.commit()
    #end escribir_opcion
#end class
