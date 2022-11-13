import itertools

from mininet.topo import Topo
from mininet.log import info, error, setLogLevel

from network import Network

net_vpn = Network("10.255.12.192/27")
net_host = Network("10.30.6.0/23")
net_internet = Network("192.168.100.0/24")
net_cluster = Network("10.128.0.0/14")
net_service = Network("172.30.0.0/16")
net_pub = Network("10.94.61.0/24")
net_client = Network("192.168.110.0/24")


class MyNetwork(Topo):
    def build(self):

        # Routers
        #
        # These are hosts with multiple interfaces that are responsible for
        # routing traffic between differents networks.
        r_host = self.addHost("r_host", ip=net_host.gateway_cidr)
        r_pub = self.addHost("r_pub", ip=net_pub.gateway_cidr)
        r_client = self.addHost("r_client", ip=net_client.gateway_cidr)

        # Switches
        #
        # These connect hosts that share the same newtork.
        dpid = (str(x) for x in itertools.count(100))
        s_client = self.addSwitch("s_client", dpid=next(dpid))
        s_host = self.addSwitch("s_host", dpid=next(dpid))
        s_pub = self.addSwitch("s_pub", dpid=next(dpid))
        s_service = self.addSwitch("s_service", dpid=next(dpid))
        s_internet = self.addSwitch("s_internet", dpid=next(dpid))
        s_vpn = self.addSwitch("s_vpn", dpid=next(dpid))

        self.addLink(r_client, s_client)
        self.addLink(r_host, s_host)
        self.addLink(r_pub, s_pub)
        self.addLink(r_host, s_vpn, params1=dict(ip=net_vpn.next_cidr()))

        # "client" is your home device. It access the remote cluster over the
        # public network or over the VPN.
        client = self.addHost("client", ip=net_client.next_cidr())
        self.addLink(client, s_client)
        self.addLink(client, s_vpn, params1=dict(ip=net_vpn.next_cidr()))

        # "host0" is a cluster node.
        host0 = self.addHost("host0", ip=net_host.next_cidr())
        self.addLink(host0, s_host)
        self.addLink(host0, s_pub, params1=dict(ip=net_pub.next_cidr()))

        # "serv0" represents a service running in a namespace on "host0".
        serv0 = self.addHost("serv0", ip=net_service.next_cidr())
        self.addLink(serv0, s_service)
        self.addLink(host0, s_service, params1=dict(ip=net_service.gateway_cidr))

        self.addLink(r_client, s_internet, params1=dict(ip=net_internet.next_cidr()))
        self.addLink(r_pub, s_internet, params1=dict(ip=net_internet.next_cidr()))


topos = {"mynet": MyNetwork}
