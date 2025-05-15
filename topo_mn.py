from mininet.topo import Topo
from mininet.net import Mininet
from mininet.link import TCLink
from mininet.cli import CLI
# from mininet.term import makeTerm

import argparse


class MyTopo(Topo):
    def __init__(self, n_hosts=2):
        Topo.__init__(self)

        # Crear switch central y servidor
        server = self.addHost('server')
        s1 = self.addSwitch('s1')
        self.addLink(server, s1)

        # Crear clientes
        for i in range(n_hosts):
            host = self.addHost(f'h{i}')
            self.addLink(host, s1)


def create(n_hosts, loss_rate):
    topo = MyTopo(n_hosts)
    net = Mininet(topo=topo, link=TCLink, autoSetMacs=True,
                  xterms=True, controller=None)
    net.start()

    # Pongo el switch en modo standalone
    for sw in net.switches:
        sw.cmd(f'ovs-vsctl set-fail-mode {sw.name} standalone')

    # Asigno IPs manualmente, asegurándo que `server` tenga la primer IP
    server = net.get('server')
    server.setIP('10.0.0.1/8', intf='server-eth0')
    print("[INFO] IP de server: 10.0.0.1")

    for i in range(n_hosts):
        # Los hosts empiezan desde 10.0.0.2
        host = net.get(f'h{i}')
        host.setIP(f'10.0.0.{i+2}/8', intf=f'h{i}-eth0')
        print(f"[INFO] IP de h{i}: 10.0.0.{i+2}")

    # Agrego pérdida de paquetes con tc netem
    for i in range(n_hosts):
        host = net.get(f'h{i}')
        iface = f'h{i}-eth0'
        host.cmd(f'tc qdisc add dev {iface} root netem loss {loss_rate}%')
        print(f"[INFO] Pérdida del {loss_rate}% aplicada a {iface}")

    server = net.get('server')
    server.cmd(f'tc qdisc add dev server-eth0 root netem loss {loss_rate}%')
    print(f"[INFO] Pérdida del {loss_rate}% aplicada a server-eth0")

    CLI(net)
    net.stop()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Topología Mininet con pérdida')
    parser.add_argument('-nh', '--n_hosts', type=int, default=2,
                        help='Número de hosts')
    parser.add_argument('-lr', '--loss_rate', type=float, default=0,
                        help='Porcentaje de pérdida de paquetes')
    args = parser.parse_args()
    create(args.n_hosts, args.loss_rate)


"""

"""
