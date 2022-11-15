import enum
import pytest
import time

import implementation
from topo import MyNetwork
from host import Host, CalledProcessError


@pytest.fixture
def net_basic():
    '''Network without out any policy routing configuration'''

    with implementation.run_network() as net:
        implementation.configure_basic_routes(net)
        implementation.configure_nat(
            net,
            "host0",
            "30463",
            f"{net.topo.net_pub[241]}:80",
            f"{net['serv0'].intf().ip}:8000",
        )

        while True:
            try:
                net["serv0"].run("curl --connect-timeout 2 localhost:8000")
            except CalledProcessError:
                time.sleep(1)
                continue
            else:
                break

        yield net


@pytest.fixture
def net_with_routing(net_basic):
    '''Network with all policy routing rules configured'''

    net = net_basic
    implementation.configure_source_routing(net, "host0")
    implementation.configure_fwmark_routing(net, "host0")
    return net


def ipof(hostname, devname):
    '''Utility function allows test parameters to refer to a host address
    that will only be known at runtime'''

    def ipof_net(net):
        for intf in net[hostname].intfs.values():
            if intf.name == devname:
                return intf.ip
        raise KeyError(devname)

    ipof_net.__name__ = f"{devname}@{hostname}"
    return ipof_net


def try_connect(net, hostname, addr, port):
    '''Attempt to connect with curl from host hostname to the given
    address and port'''

    # Resolve address if was specified using ipof()
    if callable(addr):
        addr = addr(net)

    try:
        out = net[hostname].run(f"curl --connect-timeout 2 {addr}:{port}")
        success = True
    except Exception:
        out = ""
        success = False

    return out, success


@pytest.mark.parametrize(
    "addr,port,expect_success",
    [
        (ipof("host0", "host0-eth0"), 30463, True),
        (ipof("host0", "host0-eth0"), 8000, True),
        (ipof("host0", "host0-eth1"), 8000, True),
        (ipof("host0", "host0-eth1"), 30463, True),
        ("10.94.61.241", 80, True),
    ],
)
def test_rp_filter_loose(net_with_routing, addr, port, expect_success):
    '''With rp_filter in loose mode and all the routing rules in place, the
    client should be able to access the service on serv0 via the public ip, the
    nodeport on the host public ip, and the nodeport on the host internal ip.
    We should also be able to reach a service running on the host at either
    the public or the internal address.'''

    net = net_with_routing
    net["host0"].setRpFilter(Host.RP_FILTER_LOOSE)

    out, success = try_connect(net, "client", addr, port)
    assert success == expect_success
    if success:
        assert "EXAMPLE SERVICE" in out


@pytest.mark.parametrize(
    "addr,port,expect_success",
    [
        (ipof("host0", "host0-eth0"), 30463, True),
        (ipof("host0", "host0-eth0"), 8000, True),
        (ipof("host0", "host0-eth1"), 8000, True),
        (ipof("host0", "host0-eth1"), 30463, False),
        ("10.94.61.241", 80, False),
    ],
)
def test_rp_filter_strict(net_with_routing, addr, port, expect_success):
    '''With rp_filter in strict mode and all the routing rules in place,
    we should only be able to reach the service via the nodeport of the host
    internal address. We should also be able to reach a service running
    on the host at either the public or the internal address.'''

    net = net_with_routing
    net["host0"].setRpFilter(Host.RP_FILTER_STRICT)

    out, success = try_connect(net, "client", addr, port)
    assert success == expect_success
    if success:
        assert "EXAMPLE SERVICE" in out


@pytest.mark.parametrize(
    "addr,port,expect_success",
    [
        (ipof("host0", "host0-eth0"), 30463, True),
        (ipof("host0", "host0-eth0"), 8000, True),
        (ipof("host0", "host0-eth1"), 8000, False),
        (ipof("host0", "host0-eth1"), 30463, False),
        ("10.94.61.241", 80, False),
    ],
)
def test_service_no_policy_routing(net_basic, addr, port, expect_success):
    '''With rp_filter in loose mode and no policy routing rules configured, we
    should only be able to access services via the host internal address.'''
    net = net_basic
    net["host0"].setRpFilter(Host.RP_FILTER_LOOSE)

    out, success = try_connect(net, "client", addr, port)
    assert success == expect_success
    if success:
        assert "EXAMPLE SERVICE" in out


@pytest.mark.parametrize(
    "addr,port,expect_success",
    [
        (ipof("host0", "host0-eth0"), 30463, True),
        (ipof("host0", "host0-eth0"), 8000, True),
        (ipof("host0", "host0-eth1"), 8000, True),
        (ipof("host0", "host0-eth1"), 30463, False),
        ("10.94.61.241", 80, False),
    ],
)
def test_service_no_fwmark_routing(net_basic, addr, port, expect_success):
    '''With rp_filter in loose mode and only source routing configured, we
    should be able to access all services via the host internal address and
    only locally hosted services via the public network.'''

    net = net_basic
    net["host0"].setRpFilter(Host.RP_FILTER_LOOSE)

    implementation.configure_source_routing(net, "host0")
    out, success = try_connect(net, "client", addr, port)
    assert success == expect_success
    if success:
        assert "EXAMPLE SERVICE" in out
