#!/bin/bash
SRC=$(cd $(dirname "$0"); cd ..; pwd)
ENVVARS="${SRC}/config/envvars.sh"
cd $(dirname "$0"); cd ..; #ubicarnos en raiz..

source ${ENVVARS}
: ${AP_INTERFACE:="wlan0"}
: ${AP_ADDRESS:="10.3.2.1"}
: ${AP_SSID:="SISTEMA"}
: ${AP_PASS:="control17"}
: ${AP_INVISIBLE:=0}

echo "asignando Ip estática al Wifi..."


# if $(sudo grep -q "interface\s*${AP_INTERFACE}" /etc/dhcpcd.conf); then
#  sudo sed -i '/interface '${AP_INTERFACE}'/{$!{N;s|interface '${AP_INTERFACE}'\n\s*static.*|interface '${AP_INTERFACE}'\nstatic ip_address='${AP_ADDRESS}'|;ty;P;D;:y}}' /etc/dhcpcd.conf
# else
#  echo -e "\ninterface ${AP_INTERFACE}\nstatic ip_address=${AP_ADDRESS}/24" | sudo tee -a /etc/dhcpcd.conf
# fi

if $(sudo grep -q "interface\s*${AP_INTERFACE}" /etc/dhcpcd.conf); then
  sudo sed -i '/interface '${AP_INTERFACE}'/{$!{N;s|interface '${AP_INTERFACE}'\n\s*static.*|denyinterfaces '${AP_INTERFACE}'|;ty;P;D;:y}}' /etc/dhcpcd.conf
fi

if $(sudo grep -q "denyinterfaces\s*${AP_INTERFACE}" /etc/dhcpcd.conf); then
  echo "ya deshabilitado"
else
  echo "denyinterfaces ${AP_INTERFACE}" | sudo tee "/etc/dhcpcd.conf"
fi

if $(sudo grep -q "iface ${AP_INTERFACE} inet manual" /etc/network/interfaces); then
  echo "configurando /etc/network/interfaces"
  sudo sed -i '/iface '${AP_INTERFACE}' inet manual/{$!{N;s|iface '${AP_INTERFACE}' inet manual\n\s*wpa.*|iface '${AP_INTERFACE}' inet static\n address '${AP_ADDRESS}'\n netmask 255.255.255.0|;ty;P;D;:y}}' /etc/network/interfaces
fi

sudo service dhcpcd restart
sudo ifdown wlan0; sudo ifup wlan0

sudo apt-get install hostapd -y

if [ -f "/etc/hostapd/hostapd.conf" ]; then
  echo "reconfigurando /etc/hostapd/hostapd.conf..."
  sudo sed -i 's|\(interface=.*\)|interface='${AP_INTERFACE}'|' /etc/hostapd/hostapd.conf
  sudo sed -i 's|\(ssid=.*\)|ssid='${AP_SSID}'|' /etc/hostapd/hostapd.conf
  sudo sed -i 's|\(ignore_broadcast_ssid=.*\)|ignore_broadcast_ssid='${AP_INVISIBLE}'|' /etc/hostapd/hostapd.conf
  sudo sed -i 's|\(wpa_passphrase=.*\)|wpa_passphrase='${AP_PASS}'|' /etc/hostapd/hostapd.conf
else
  echo -e "interface=${AP_INTERFACE}\n#driver=nl80211\nssid=${AP_SSID}\nhw_mode=g\nchannel=6\nieee80211n=1\nwmm_enabled=1\nht_capab=[HT40][SHORT-GI-20][DSSS_CCK-40]\nmacaddr_acl=0\nauth_algs=1\nignore_broadcast_ssid=${AP_INVISIBLE}\nwpa=2\nwpa_key_mgmt=WPA-PSK\nwpa_passphrase=${AP_PASS}\nrsn_pairwise=CCMP" | sudo tee "/etc/hostapd/hostapd.conf"
fi

sudo sed -i 's|#DAEMON_CONF=.*|DAEMON_CONF="/etc/hostapd/hostapd.conf"|' /etc/default/hostapd
sudo sed -i 's|DAEMON_CONF=.*|DAEMON_CONF=/etc/hostapd/hostapd.conf|' /etc/init.d/hostapd
#probar aqui con  sudo /usr/sbin/hostapd /etc/hostapd/hostapd.conf
# para ver mensajes de error (posible configuración de un modulo externo)

sudo apt-get install dnsmasq -y
if [ -f "/etc/dnsmasq.conf.orig" ]; then
  echo "original encontrado, omitiendo copia"
else
  sudo mv /etc/dnsmasq.conf  /etc/dnsmasq.conf.orig
fi
export AP_DHCP_1=$(echo $AP_ADDRESS|cut -d"." -f1-3).50
export AP_DHCP_2=$(echo $AP_ADDRESS|cut -d"." -f1-3).150
echo -e "interface=${AP_INTERFACE}\nlisten-address=${AP_ADDRESS}\nbind-interfaces\nserver=8.8.8.8\ndomain-needed\nbogus-priv\ndhcp-range=${AP_DHCP_1},${AP_DHCP_2},12h" | sudo tee /etc/dnsmasq.conf

if $(sudo grep -q "After=" /lib/systemd/system/dnsmasq.service); then
  echo "ya modificado el After"
  #sed '/\[Unit\]/{$!{N;s|\[Unit\]\nAfter=.*|[Unit]]\nAfter=dhcpcd.service|;ty;P;D;:y}}' /lib/systemd/system/dnsmasq.service
else
  sudo sed -i 's|\[Unit\]|[Unit]\nAfter=dhcpcd.service|' /lib/systemd/system/dnsmasq.service
fi

if [ -f "/usr/share/dbus-1/system-services/fi.epitest.hostap.WPASupplicant.service" ]; then
  sudo mv /usr/share/dbus-1/system-services/fi.epitest.hostap.WPASupplicant.service ~/
fi


sudo systemctl daemon-reload
#sudo service hostapd reload
#sudo service dnsmasq reload
sudo systemctl restart hostapd
sudo systemctl restart dnsmasq
#requiere reiniciar?


#compartir internet:
sudo sh -c "echo 1 > /proc/sys/net/ipv4/ip_forward"
sudo sed -i 's|#net.ipv4.ip_forward=.*|net.ipv4.ip_forward=1|'  /etc/sysctl.conf
sudo iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
sudo iptables -A FORWARD -i eth0 -o wlan0 -m state --state RELATED,ESTABLISHED -j ACCEPT
sudo iptables -A FORWARD -i wlan0 -o eth0 -j ACCEPT
sudo iptables -t nat -A PREROUTING -i wlan0 -p tcp --dport 80 -j REDIRECT --to-port ${HOSTPORT}
#sudo iptables-t mangle-N internet iptables-t mangle-A PREROUTING-i wlan0-p tcp-m tcp--dport 80 -j internet iptables-t mangle-A internet-j MARK--set-mark 99
#sudo iptables -t nat -A PREROUTING -i wlan0 -p tcp -m mark --mark 99 -m tcp --dport 80 -j DNAT --to-destination 192.168.10.1
sudo sh -c "iptables-save > /etc/iptables.ipv4.nat"
if $(sudo grep -q "iptables-restore" /etc/rc.local ); then
  echo "ya modificado el restore"
else
  sudo sed -i "s|exit 0|iptables-restore < /etc/iptables.ipv4.nat\nexit 0|" /etc/rc.local
fi
sudo apt-get install iptables-persistent -y #al ultimo para guardar!

