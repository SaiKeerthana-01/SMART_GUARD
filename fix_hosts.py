for h in net.hosts:
    h.cmd("echo nameserver 8.8.8.8 > /etc/resolv.conf")
    h.cmd("ip route add default via 10.0.0.254")
    h.cmd("apt-get update")
    h.cmd("apt-get install -y python3 python3-pip")
    h.cmd("pip3 install paho-mqtt")
