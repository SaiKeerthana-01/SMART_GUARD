from mininet.net import Mininet
from mininet.topo import SingleSwitchTopo

def install_packages_on_hosts(net):
    # Loop through all 100 hosts
    for host in net.hosts:
        print(f'Installing on {host.name}...')
        host.cmd("echo 'nameserver 8.8.8.8' > /etc/resolv.conf")
        host.cmd('apt-get update')
        host.cmd('apt-get install -y python3 python3-pip')
        host.cmd('pip3 install paho-mqtt')

if __name__ == "__main__":
    # Create topology with 100 hosts
    topo = SingleSwitchTopo(k=100)
    net = Mininet(topo=topo)
    net.start()
    install_packages_on_hosts(net)
    print("\nAll hosts configured!")
    net.stop()
