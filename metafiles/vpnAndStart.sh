#!/bin/bash

echo "Current IP is:"
curl https://ipinfo.io/ip

echo -n "Should I start VPN (y/n)? "
read answer
if [ "$answer" != "${answer#[Yy]}" ] ;then
        cd /etc/openvpn/
        curl https://ipinfo.io/ip
        sudo openvpn --config ch116.nordvpn.com.tcp.ovpn --daemon
        echo "New IP is:"
        curl https://ipinfo.io/ip
fi
echo "starting bot"
cd ~/oldShatterhand/oldShatterhand
python3 main_driver.py &
echo "started bot. Running python3 processes:"
ps -ef | grep python3
echo ".end"
