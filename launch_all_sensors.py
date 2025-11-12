#!/usr/bin/env python3

import time
from mininet.net import Mininet
from mininet.topo import SingleSwitchTopo
from mininet.cli import CLI
from mininet.log import setLogLevel

def launch_sensors():
    setLogLevel('info')
    topo = SingleSwitchTopo(k=100)
    net = Mininet(topo=topo)
    net.start()
 
    # Wait for network and MQTT broker readiness
    time.sleep(5)

    rooms = [
        "CR101", "CR102", "CR103", "CR104", "CR105", "CR106", "CR107", "CR108", "CR109", "CR110",
        "CR201", "CR202", "CR203", "CR204", "CR205", "CR206", "CR207", "CR208", "CR209", "CR210",
        "LAB1", "LAB2", "LAB3", "LAB4", "LAB5", "LAB6", "LAB7", "LAB8", "LAB9", "LAB10",
        "HALL1", "HALL2", "HALL3", "HALL4", "HALL5", "HALL6", "HALL7", "HALL8", "HALL9", "HALL10",
        "LIB1", "LIB2", "LIB3", "LIB4", "LIB5", "LIB6", "LIB7", "LIB8", "LIB9", "LIB10",
        "OFFICE1", "OFFICE2", "OFFICE3", "OFFICE4", "OFFICE5", "OFFICE6", "OFFICE7", "OFFICE8", "OFFICE9", "OFFICE10",
        "CAFE1", "CAFE2", "CAFE3", "CAFE4", "CAFE5", "CAFE6", "CAFE7", "CAFE8", "CAFE9", "CAFE10",
        "LAB11", "LAB12", "LAB13", "LAB14", "LAB15", "LAB16", "LAB17", "LAB18", "LAB19", "LAB20",
        "CR301", "CR302", "CR303", "CR304", "CR305", "CR306", "CR307", "CR308", "CR309", "CR310",
        "ROOM1", "ROOM2", "ROOM3", "ROOM4", "ROOM5", "ROOM6", "ROOM7", "ROOM8", "ROOM9", "ROOM10"
    ]

    for i in range(100):
        host = net.get(f'h{i+1}')
        host.cmd('ip route add default via 10.0.0.254')
        room = rooms[i]
        cmd = f'python3 /home/mininet/environmental_monitoring/sensors/sensor_simulator_multiroom.py {room} {host.name} &'
        print(f"Launching sensor on h{i+1} for room {room}")
        host.cmd(cmd)

    print("\nAll 100 sensors launched!")
    CLI(net)
    net.stop()

if __name__ == '__main__':
    launch_sensors()
