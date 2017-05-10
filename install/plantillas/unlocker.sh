#!/bin/bash
SRC=$(cd $(dirname "$0"); pwd)
ENVVARS="${SRC}/config/envvars.sh"
PYTHON="python"

if [ ! -f ${ENVVARS} ]
then
    echo "cargando configuracion de ejemplo..."
    cp "${SRC}/config/envvars.sh.ejemplo" ${ENVVARS}
fi
source "${ENVVARS}"
cd ${SRC}
${PYTHON} src/app.py

