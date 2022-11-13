import mininet.node

from mininet.util import decode
from subprocess import PIPE

class CalledProcessError(Exception):
    def __init__(self, *_args, args=None, kwargs=None, out=None, err=None, exitcode=None):
        self.args = args
        self.kwargs = kwargs
        self.out = out
        self.err = err
        self.exitcode = exitcode

        super().__init__(*_args)

    def __str__(self):
        return f'\n[exit] {self.exitcode}\n[out] {self.out}\n[err] {self.err}\n'

class Host(mininet.node.Host):
    def run(self, *args, **kwargs):
        shell = not isinstance(args[0], list)
        out, err, exitcode = self.pexec(*args, **kwargs, shell=shell)
        if exitcode != 0:
            raise CalledProcessError(args=args, kwargs=kwargs, out=out, err=err, exitcode=exitcode)
        return out

    def pexec( self, *args, input=None, **kwargs):
        """Execute a command using popen
           returns: out, err, exitcode"""
        popen = self.popen( *args, stdin=PIPE, stdout=PIPE, stderr=PIPE,
                            **kwargs )
        # Warning: this can fail with large numbers of fds!
        out, err = popen.communicate(input=input)
        exitcode = popen.wait()
        return decode( out ), decode( err ), exitcode

    def run_many(self, *cmdlines, **kwargs):
        for cmdline in cmdlines:
            self.run(cmdline, **kwargs)

    def setDefaultRoute(self, nexthop):
        return self.run(f'ip route add default via {nexthop}')

