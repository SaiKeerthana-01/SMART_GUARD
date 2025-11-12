#!/bin/bash
for i in $(seq 1 100); do
    echo "Installing on host h$i..."

    sudo mnexec -a h$i -- sh -c "echo 'nameserver 8.8.8.8' > /etc/resolv.conf"
    sudo mnexec -a h$i -- apt-get update
    sudo mnexec -a h$i -- apt-get install -y python3 python3-pip
    sudo mnexec -a h$i -- pip3 install paho-mqtt
done
echo "Installation finished on all hosts."
