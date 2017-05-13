#!/bin/bash
SRC="/opt/unlocker"
ENVVARS="/opt/unlocker/config/envvars.sh"
PYTHON="/usr/bin/python2"

if [ ! -f ${ENVVARS} ]
then
    echo "cargando configuracion de ejemplo..."
    cp "${SRC}/config/envvars.sh.ejemplo" ${ENVVARS}
fi
source "${ENVVARS}"
cd ${SRC}
${PYTHON} src/app.py

