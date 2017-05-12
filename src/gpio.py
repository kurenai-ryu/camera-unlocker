#!/opt/.virtualenvs/fingerprint/bin/python2
# -*- coding: utf-8 -*-
# pylint: disable=I0011,C0103

"""
módulo de funciones de I/O
funciones pantalla
funciones LED
funciones PIR
"""
import logging
import os
import wiringpi

LOGGER = logging.getLogger(__name__)
LED_ROJO = 14 
LED_AMARILLO = 15
LED_VERDE = 18

SW1 = 23
SW2 = 24

RELE = 25
AUX = 28

def on(pin):
	wiringpi.digitalWrite(pin, 1)

def off(pin):
	wiringpi.digitalWrite(pin, 0)

def read(pin):
	return bool(wiringpi.digitalRead(pin) == 1)

def leds_off():
	wiringpi.digitalWrite(LED_ROJO, 0)	
	wiringpi.digitalWrite(LED_AMARILLO, 0)	
	wiringpi.digitalWrite(LED_VERDE, 0)	
	wiringpi.digitalWrite(RELE, 0)	


#inicialización aqui:
os.system("gpio -g mode  %i up > /dev/null 2>&1" % SW1) #pullup
os.system("gpio export %i in > /dev/null 2>&1" % SW1) #bcm
os.system("gpio -g mode  %i up > /dev/null 2>&1" % SW2) #pullup
os.system("gpio export %i in > /dev/null 2>&1" % SW2) #bcm
os.system("gpio export %i out > /dev/null 2>&1" % LED_ROJO) #rojo
os.system("gpio export %i out > /dev/null 2>&1" % LED_AMARILLO) #azul
os.system("gpio export %i out > /dev/null 2>&1" % LED_VERDE) #verde
os.system("gpio export %i out > /dev/null 2>&1" % RELE) #verde

res = wiringpi.wiringPiSetupSys()
LOGGER.debug("Configuración GPIO  0=sin error -> %i", res)
leds_off()
