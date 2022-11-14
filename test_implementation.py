import pytest
import time

import implementation
from topo import *

RP_FILTER_LOOSE = 2
RP_FILTER_STRICT = 1
RP_FILTER_DISABLED = 0


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
        implementation.configure_fwmark_routing(_net, "host0")
        implementation.configure_rp_filter(_net, "host0")

        while True:
            try:
                _net["serv0"].run("curl --connect-timeout 2 localhost:8000")
            except Exception:
                time.sleep(1)
                continue
            else:
                break

        yield _net


def ipof(hostname, devname):
    def ipof_net(net):
        for intf in net[hostname].intfs.values():
            if intf.name == devname:
                return intf.ip
        raise KeyError(devname)

    return ipof_net


@pytest.mark.parametrize(
    "addr,port,expect_success",
    [
        (ipof("host0", "host0-eth0"), 30463, True),
        (ipof("host0", "host0-eth1"), 30463, True),
        ("10.94.61.241", 80, True),
    ],
)
def test_rp_filter_loose(net, addr, port, expect_success):
    implementation.configure_rp_filter(net, "host0", value=RP_FILTER_LOOSE)
    if callable(addr):
        addr = addr(net)

    try:
        out = net["client"].run(f"curl --connect-timeout 2 {addr}:{port}")
        success = True
    except Exception:
        out = ""
        success = False

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
def test_rp_filter_strict(net, addr, port, expect_success):
    implementation.configure_rp_filter(net, "host0", value=RP_FILTER_STRICT)
    if callable(addr):
        addr = addr(net)

    try:
        out = net["client"].run(f"curl --connect-timeout 2 {addr}:{port}")
        success = True
    except Exception:
        out = ""
        success = False

    assert success == expect_success
    if success:
        assert "EXAMPLE SERVICE" in out
