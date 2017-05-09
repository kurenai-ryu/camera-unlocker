#!/bin/bash
SRC=$(cd $(dirname "$0"); cd ..; pwd)
ENVVARS="${SRC}/config/envvars.sh"
cd $(dirname "$0"); cd ..; #ubicarnos en raiz..

source ${ENVVARS}

echo "instalando postgres...."
sudo apt-get install postgresql -y

echo "modificando tipo de accesso...."
cd /etc/postgresql/*/main

if $(sudo grep -q "host\s*${PGDATABASE}.*" pg_hba.conf); then
  sudo sed -i "s|\(host\s*${PGDATABASE}.*\)|host ${PGDATABASE} all 0.0.0.0/0 md5|" pg_hba.conf
else
  echo "host  ${PGDATABASE}  all  0.0.0.0/0  md5" | sudo tee -a pg_hba.conf
fi
echo "modificando tipo de accesso....[1]"
sudo sed -i "s|#listen_addresses = 'localhost'|listen_addresses = '*'|" postgresql.conf
sudo /etc/init.d/postgresql restart #generic?
echo "creando base de datos...."
sudo -H -u postgres sh -c 'createdb '${PGDATABASE}
echo "creando usuario...."
sudo -H -u postgres sh -c 'psql -c "CREATE USER '${PGUSER}' WITH PASSWORD '"'"${PGPASSWORD}"'"';"'
sudo -H -u postgres sh -c 'psql -c "GRANT ALL PRIVILEGES ON DATABASE '${PGDATABASE}' TO '${PGUSER}' ;"'

cd ${SRC}
