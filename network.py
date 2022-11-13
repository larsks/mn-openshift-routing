import ipaddress


class Network:
    '''Convenience wrapper for an ipaddress.IPv4Network'''

    def __init__(self, cidr, start=10):
        self.net = ipaddress.IPv4Network(cidr)
        self.start = start
        self.addrs = self.addrs_iter()

    def __str__(self):
        return str(self.net)

    def __getitem__(self, n):
        return self.net[n]

    def addrs_iter(self):
        for i in range(self.start, self.net.num_addresses):
            yield self.net[i]

    @property
    def gateway(self):
        return self.net[1]

    @property
    def gateway_cidr(self):
        return f'{self.gateway}/{self.net.prefixlen}'

    def next(self):
        return next(self.addrs)

    def next_cidr(self):
        return f'{self.next()}/{self.net.prefixlen}'

