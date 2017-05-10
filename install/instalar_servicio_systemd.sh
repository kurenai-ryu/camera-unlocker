#!/bin/bash
SRC=$(cd $(dirname "$0"); cd ..; pwd)
NAME="unlocker"

SERVICE="/etc/systemd/system/${NAME}.service"
LOCAL="${SRC}/install/plantillas/${NAME}.service"
APP="${SRC}/bin/${NAME}.sh"
PYTHON=$(which python2)
sudo apt-get install systemd -y #JIC

echo "agregando usuario a systemd-journal (requiere reingresar)"
sudo usermod -a -G systemd-journal $(whoami)

mkdir -p "${SRC}/bin"
mkdir -p "${SRC}/logs" #por culpa del gitignore

echo "copiando archivos de arranque... ${SRC}"
cp "${SRC}/install/plantillas/${NAME}.sh" ${APP}
chmod +x ${APP}
echo "ajustando directorios..."
sed -i 's|\(SRC=.*\)|SRC="'${SRC}'"|' ${APP}
sed -i 's|\(ENVVARS=.*\)|ENVVARS="'${SRC}'/config/envvars.sh"|' ${APP}
sed -i 's|\(PYTHON=.*\)|PYTHON="'${PYTHON}'"|' ${APP}


echo "Copiando archivo de servicio..."
sudo cp ${LOCAL} ${SERVICE}


echo "ajustando directorio..."
sudo sed -i 's|\(ExecStart=.*\)|ExecStart='${APP}'|' ${SERVICE}

echo "habilitando servicios"
sudo systemctl enable ${NAME}
sudo systemctl reload-or-restart ${NAME}


systemctl status ${NAME}
echo ""
echo "verifique el estado mediante 'sudo systemctl status ${NAME}'"
echo "y el log mediante 'journalctl -o cat -f -n -u ${NAME}'"

