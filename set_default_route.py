for h in net.hosts:
    h.cmd('ip route add default via 10.0.0.254')
