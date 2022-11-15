import enum
import pytest
import time

import implementation
from topo import *
from host import Host, CalledProcessError


@pytest.fixture
def net():
    with implementation.run_network() as _net:
        implementation.configure_basic_routes(_net)
        implementation.configure_nat(
            _net,
            "host0",
            "30463",
            f"{net_pub[241]}:80",
            f"{_net['serv0'].intf().ip}:8000",
        )

        while True:
            try:
                _net["serv0"].run("curl --connect-timeout 2 localhost:8000")
            except CalledProcessError:
                time.sleep(1)
                continue
            else:
                break

        yield _net


@pytest.fixture
def net_with_routing(net):
    implementation.configure_source_routing(net, "host0")
    implementation.configure_fwmark_routing(net, "host0")
    return net


def ipof(hostname, devname):
    def ipof_net(net):
        for intf in net[hostname].intfs.values():
            if intf.name == devname:
                return intf.ip
        raise KeyError(devname)

    ipof_net.__name__ = f"{devname}@{hostname}"
    return ipof_net


def try_connect(net, hostname, addr, port):
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
        (ipof("host0", "host0-eth1"), 30463, True),
        ("10.94.61.241", 80, True),
    ],
)
def test_rp_filter_loose(net_with_routing, addr, port, expect_success):
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
        (ipof("host0", "host0-eth1"), 30463, False),
        ("10.94.61.241", 80, False),
    ],
)
def test_rp_filter_strict(net_with_routing, addr, port, expect_success):
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
        (ipof("host0", "host0-eth1"), 8000, False),
        (ipof("host0", "host0-eth1"), 30463, False),
        ("10.94.61.241", 80, False),
    ],
)
def test_service_no_policy_routing(net, addr, port, expect_success):
    out, success = try_connect(net, "client", addr, port)
    assert success == expect_success
    if success:
        assert "EXAMPLE SERVICE" in out


@pytest.mark.parametrize(
    "addr,port,expect_success",
    [
        (ipof("host0", "host0-eth0"), 30463, True),
        (ipof("host0", "host0-eth1"), 8000, True),
        (ipof("host0", "host0-eth1"), 30463, False),
        ("10.94.61.241", 80, False),
    ],
)
def test_service_no_fwmark_routing(net, addr, port, expect_success):
    implementation.configure_source_routing(net, "host0")
    out, success = try_connect(net, "client", addr, port)
    assert success == expect_success
    if success:
        assert "EXAMPLE SERVICE" in out
