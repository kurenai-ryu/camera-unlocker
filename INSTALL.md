# Instalación

# instalación raspberry

1. Obtener o descargar la imagen de [Raspbian con Pixel](https://www.raspberrypi.org/downloads/raspbian/) correspondiente. El sistema fue probado con la versión Raspbian Jessie Pixel 2017-03-02 (Kernel 4.4.50-v7+ #970)

2. Descomprimir y grabar la imagen(`*.img`) en la tarjeta SD, se puede seguir la guía oficial para ello.
  1. Determine el dispositivo(`/dev`) correspondiente a su lector de tarjeta SD, puede ser por ejemplo `/dev/sdb` o `/dev/mmcblk0`

     > Recuerde no confundir con los discos del sistema (usualmente sda)

     > Recuerde ignorar la numeracion de la partición, es decir no grabe en /dev/sdb0 o sdb1 sino en /dev/sdb (igualmente con /dev/mmcblk0p1 o /dev/mmcblk0p2, grabe en /dev/mmcblk0)

  2. ejecutar el comando 

     ```sh
     sudo dd bs=4M if=2017-03-02-raspbian-jessie.img of=/dev/mmcblk0 status=progress
     ```

     en la carpeta donde descomprimió la imagen, remplace el comando con la imagen  correcta y el dispositivo correcto

3. Se recomienda asignar una IP estática al equipo. Si no se puede levantar el raspberry con teclado y monitor HDMI, se puede hacerlo al momento de grabar la tarjeta SD:
  1. Luego de grabar la imagen en la tarjeta SD, se puede montar nuevamente la misma, en la tarjeta existirán dos particiones, una llamada BOOT que es una FAT de unos 64 MB y otra partición Linux/ext3 de 3.8GB, al montar la partición Linux/ext3 buscar el archivo `./etc/dhcpcd.conf` y agregar las líneas correspondientes a eth0:
    ```sh
    interface eth0

    static ip_address=192.168.1.100/24
    static routers=192.168.1.1
    static domain_name_servers=192.168.1.1 8.8.8.8
    ```

    donde 192.168.1.100 es la ip que se quiere establecer.

    > Cuide de no editar el archivo dhcpcd.conf de su sistema, sino de la tarjeta SD
    >
    > Esta IP de ejemplo: 192.168.1.100 debe ser cambiada en cada lugar de este manual por un valor acorde a su red actual.

  2. Luego habilitar el acceso por SSH, creando un archivo vacio con el nombre `ssh` en la partición BOOT de la tarjeta SD
    ```sh
    sudo touch ./boot/ssh
    ```

  3. (Opcionalmente) si desea tener acceso a una red Wifi, puede crear un archivo en la partición BOOT con el nombre `wpa_supplicant.conf` con la descripción de la red a conectarse:
    ```sh
    network={
        ssid="YOUR_SSID"
        psk="YOUR_PASSWORD"
        key_mgmt=WPA-PSK
    }
    ```
    > Omita este paso, si no desea acceder a una red wifi

4. Colocar la tarjeta SD e iniciar el raspberry. No se debe olvidar alimentar y conectar a la red el Equipo.

5. Verificar que el raspberry tiene conexión de red, y que responde a la dirección IP asignada ( o verificar en el servidor DHCP la dirección IP que fue asignada al raspberry)

6. Ingresar por ssh al raspberry con el usuario pi (la contraseña por defecto es raspberry)
    ```sh
    ssh pi@192.168.1.100
    ```

7. En este punto, es necesario configurar el raspberry, para lo cual se debe ingresar mediante `sudo raspi-config`.
    1. hostname - cambiar el nombre del equipo (muy importante!. por ejemplo `reconocimiento`)
    2. _(Opcional) Change User Password_. preferentemente borre más adelante el usuario `pi`
    3. _Internacionalisation Options_
        2. Cambiar la zona horaria (Obligatorio: por ejemplo a `America/La_Paz`)
        3. Cambiar el idioma del sistema (Obligatorio: instalar locale `es_BO.UTF-8` y seleccionar como locale `C.UTF-8` u [otro](http://www.xappsoftware.com/wordpress/2017/02/07/warning-setting-locale-failed-raspbian-solved/))
        4. Cambiar la distribución del teclado `(Spanish/LatinAmerica)`
        5. Cambiar el Wifi-country a `BO`
    4. Advanced Options:
        1. Expand Filesystem (muy importante! el sistema ya lo hace de antemano)
        2. SPI - habilitar el SPI en el Kernel
        3. Habilitar acceso por SSH ( si no se hizo el paso anterior de crear el archivo `/boot/ssh`)
        4. Serial - deshabilitar login shell en el puerto serial (Opcional)
           Finish
           _(requerirá reiniciar el raspberry)_

8. [Libere espacio](https://github.com/raspberrycoulis/remove-bloat/), eliminando aplicaciones poco utilizadas:
    ```sh
    sudo apt-get remove --purge wolfram-engine libreoffice* scratch minecraft-pi sonic-pi dillo gpicview penguinspuzzle oracle-java8-jdk openjdk-7-jre oracle-java7-jdk openjdk-8-jre -y
    sudo apt-get autoremove -y
    sudo apt-get autoclean -y
    ```

9. Actualize el sistema y descargue las actualizaciones necesarias:
    ```sh
    sudo apt-get update
    sudo apt-get upgrade
    ```
    (utilize los repositorios locales para agilizar el proceso [#ref aqui])

10. Cree un nuevo usuario y contraseña:

 ```sh
  sudo adduser reco
 ```
1.  No olvide colocar una contraseña a este nuevo usuario.

2. Agregue este usuario a los grupos `sudo`, `video`, `gpio` y `dialout`:

    ```sh
    sudo adduser reco sudo
    sudo adduser reco dialout
    sudo adduser reco video
    sudo adduser reco gpio
    ```

3. cambie el inicio de LightDM para que use el nuevo usuario.

   ```sh
   sudo sed -i "s|autologin-user=pi|autologin-user=reco|g" /etc/lightdm/lightdm.conf
   ```

4. en este punto reinicie e ingrese con el nuevo usuario:
   ```sh
       sudo reboot #de la otra sesion
       ssh reco@192.168.1.100 #ingrese nuevamente
   ```
   > recuerde reiniciar y no solamente reingresar por SSH

5. verifique que el sistema esté en hora.

   ```sh
       date
   ```
   si no está en hora, verifique que se encuentra habilitado la sincronización mediante NTP.
   ```sh
       sudo timedatectl
       sudo timedatectl set-ntp 1
   ```

la diferencia de hora aceptable es de unos cuantos segundos, en caso de no sincronizar, configure el demonio ntpd o instale `ntpdate`

> Puede utilizar el servidor NTP de ibmetro: `hora.ibmetro.gob.bo`

13. (opcionalmente) Borre el usuario pi antes de continuar con la instalación.

    ```sh
        sudo systemctl stop autologin@tty1
        sudo deluser pi
    ```

    o desactivelo
    ```sh
    	sudo passwd --lock pi
    ```

## Descargar repositorio

1. cree una carpeta donde se realizará la instalación. por ejemplo para instalar en `/opt/unlocker`

```sh
export USUARIO=$(whoami)
cd /opt
sudo mkdir unlocker
sudo chown $USUARIO:$USUARIO unlocker/

```

2. puede descargar el repositorio actual o clonar el git mediante el comando:

```sh
git clone --branch master https://github.com/kurenai-ryu/camera-unlocker /opt/unlocker
#aqui les pedirán sus credenciales de github
cd /opt/unlocker
```
3. En caso de descargar el codigo mediante ZIP (sin usar `git clone`), vuelva ejecutables los scripts de instalación

```sh
chmod +x install/*.sh
```

4. Cree un archivo de configuración en la carpeta `config` llamado `config/envvars.sh`, puede copiar la muestra de la misma carpeta `config/envvars.sh.ejemplo`
5. modifique los parámetros básicos del archivo:
   * PGHOST nombre del servidor de base de datos, normalmente `localhost`.
   * PGPORT puerto del servidor de base de datos, normalmente 5432
   * PGDATABASE nombre de la base de datos.
   * PGUSER nombre del usuario con acceso a la base de datos.
   * PGPASSWORD contraseña del usuario.
   * HOSTADRR dirección de referencia de la aplicación
   * HOSTPORT puerto donde se levantará la aplicación, inicialmente 5000.

### Instalación de requisitos.

Regrese a la carpeta de instalación

```sh
cd /opt/unlocker
```

Para la instalación de requisitos, puede ejecutar el script de instalación de requisitos.

```sh
install/instalar_requerimientos.sh
```

lo que  instala las librerías necesarias en el rasp berry pi



posteriormente, si no dispone de una base de datos, puede instalar una en el raspberry con el script

```sh
install/instalar_postgres.sh
```

este script, utiliza la información de `envvars.sh` para crear una base de datos, acorde a lo necesario.

FALTA: instalar `bower` y ejecutar `bower install` en `src/www/`

### Prueba del sistema

se recomienda antes de finalizar la instalación, probar la correcta ejecución de la aplicación.

por lo cual se debe cargar las variables de entorno e iniciar la aplicación `src/app.py`

```sh
cd /opt/unlocker
source config.ennvars.sh
python src/app.py
```

lo cual mostrará la información de ejecución en pantalla hasta que encuentre el mensaje 

```sh
INFO -  * Running on http://0.0.0.0:5000/
```

en este momento puede ingresar a la dirección del raspberry, por ejemplo

```
http://192.168.1.100:5000/
```

y debe cargar una pequeña pagina de prueba.



aproveche para crear un nuevo usuario, y tomar fotos del mismo. (verifique el correcto funcionamiento de la camara) y ajuste el brillo y contraste si fuera necesario.

pruebe el sistema haciendo clic en `buscar` y verifique la correcta identificación del rostro.

> En caso de detectar falso positivos. modifique el archivo `config.py`  y reduzca el valor de `POSITIVE_THRESHOLD` 

Recurerde finalizar la aplicación ejecutando en otra terminal `killall python`

### Instalación de Servicio

Luego de tener resultados aceptables en la prueba en la carpeta de la aplicación, ejecute el instalador de servicio

```sh
cd /opt/unlocker
install/instalar_servicio_systemd.sh
```

lo cual creará un script de arranque en `bin/` un servicio en SystemD denominado `unlocker`, de esta forma la aplicación se iniciará al encenderse el raspberry.

* Para reiniciar la aplicación, ejecute el comando

  ```sh
  sudo systemctl restart unlocker
  ```

* Para ver el log de estado ejecute

  ```sh
  journalctl -o cat -f -n -u unlocker
  ```

  (probablemente la primera vez requiera sudo para ver el `journalctl`)

