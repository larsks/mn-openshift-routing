from subprocess import DEVNULL

from mininet.log import info, error, setLogLevel
from mininet.net import Mininet
from mininet.node import OVSBridge, Host
from mininet.cli import CLI

from topo import *
from host import Host

if __name__ == "__main__":
    setLogLevel("info")

    topo = MyNetwork()
    net = Mininet(topo=topo, switch=OVSBridge, host=Host)
    procs = []

    try:
        net.start()

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
            # Handle "nodePort" access
            f'iptables -t nat -A PREROUTING -p tcp -m addrtype --dst-type LOCAL -m tcp --dport 30463 -j DNAT --to-destination {net["serv0"].intf().ip}:8000',
            # Handle "loadBalancer" access
            f'iptables -t nat -A PREROUTING -d {net_pub[241]} -p tcp --dport 80 -j DNAT --to-destination {net["serv0"].intf().ip}:8000',
            # Masquerade return traffic from services
            f'iptables -t nat -A POSTROUTING -s {net["serv0"].intf().ip} -j MASQUERADE',
            f"ip rule add priority 200 from {net_pub} lookup main suppress_prefixlen 0",
            f"ip rule add priority 200 from {net_pub} lookup 200",
            f"ip rule add priority 210 fwmark 0x2000/0x2000 lookup 200",
            f"ip route add table 200 default via {net_pub.gateway}",
        )

        procs.append(
            net["serv0"].popen("python -m http.server", stdout=DEVNULL, stderr=DEVNULL)
        )

        with open("mark.nft") as fd:
            rules = fd.read().format(**locals())
            net["host0"].run("nft -f-", input=rules.encode())

        CLI(net)
    finally:
        net.stop()
        for proc in procs:
            if proc.poll() is None:
                info(f"*** Terminating: {proc.args}\n")
                proc.kill()
            proc.wait()
