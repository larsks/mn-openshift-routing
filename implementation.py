from subprocess import DEVNULL
from contextlib import contextmanager

from mininet.log import info, error, setLogLevel
from mininet.net import Mininet
from mininet.node import OVSBridge, Host
from mininet.cli import CLI

from topo import *
from host import Host


@contextmanager
def run_network():
    topo = MyNetwork()
    net = Mininet(topo=topo, switch=OVSBridge, host=Host)
    net.start()
    procs = [
        net["serv0"].popen(
            "python -m http.server", stdout=DEVNULL, stderr=DEVNULL, cwd="./htdocs"
        )
    ]

    yield net

    net.stop()

    for proc in procs:
        if proc.poll() is None:
            info(f"*** Terminating: {proc.args}\n")
            proc.kill()
        proc.wait()


def configure_basic_routes(net):
    net["serv0"].run_many(
        f"ip route add default via {net_service.gateway}",
    )
    net["client"].run_many(
        f"ip route add default via {net_client.gateway}",
        f"ip route add {net_host} via {net['r_host'].intfs[1].ip}",
    )

    net["r_pub"].run_many(
        f'ip route add {net["r_client"].intf().ip} dev r_pub-eth1',
        f'ip neigh add {net_pub[241]} lladdr {net["host0"].intfs[1].mac} dev r_pub-eth0',
    )

    net["r_client"].run_many(
        f'ip route add {net_pub} via {net["r_pub"].intfs[1].ip}',
        f"iptables -t nat -A POSTROUTING -s {net_client} -j MASQUERADE",
    )

    net["host0"].run_many(
        f"ip route add default via {net_host.gateway}",
        f"ip route add table 200 default via {net_pub.gateway}",
    )


def configure_nat(net, hostname, nodeport, pub_addr, serv_addr):
    host = net[hostname]

    pub_ip, pub_port = pub_addr.split(":")
    serv_ip, _ = serv_addr.split(":")

    host.run_many(
        # Handle "nodePort" access
        f"iptables -t nat -A PREROUTING -p tcp --dport {nodeport} -j DNAT --to-destination {serv_addr}",
        # Handle "loadBalancer" access
        f"iptables -t nat -A PREROUTING -d {pub_ip} -p tcp --dport {pub_port} -j DNAT --to-destination {serv_addr}",
        # Masquerade return traffic from services
        f"iptables -t nat -A POSTROUTING -s {serv_ip} -j MASQUERADE",
    )


def configure_source_routing(net, hostname):
    host = net[hostname]

    host.run_many(
        f"ip rule add priority 200 from {net_pub} lookup main suppress_prefixlen 0",
        f"ip rule add priority 210 from {net_pub} lookup 200",
    )


def configure_fwmark_routing(net, hostname):
    nft_rules = f"""
    table ip public-ingress {{
        chain PREROUTING {{
            type filter hook prerouting priority mangle; policy accept;

            # set fwmark on packets coming from the serviceNetwork CIDR that
            # have the connection mark set
            ct mark and 0x2000 == 0x2000 ip saddr {net_service} counter mark set ct mark

            # set connection mark on packets destined for the public network CIDR
            ct state new meta l4proto tcp ip daddr {net_pub} counter ct mark set 0x2000
        }}
    }}"""

    host = net[hostname]

    host.run_many(
        f"ip rule add priority 220 fwmark 0x2000/0x2000 lookup 200",
    )

    host.run("nft -f-", input=nft_rules.encode())


if __name__ == "__main__":
    setLogLevel("info")

    with run_network() as net:
        net["host0"].setRpFilter(Host.RP_FILTER_LOOSE)
        configure_basic_routes(net)
        configure_nat(
            net,
            "host0",
            "30463",
            f"{net_pub[241]}:80",
            f"{net['serv0'].intf().ip}:8000",
        )
        configure_source_routing(net, "host0")
        configure_fwmark_routing(net, "host0")

        CLI(net)
