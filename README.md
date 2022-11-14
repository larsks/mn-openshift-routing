## Getting started

### Run the mininet virtual machine

- Grab the [mininet virtual machine image](http://mininet.org/download/). At the time of this writing the most recent release is 2.30, and the image you want is [this one][].

  [this one]: https://github.com/mininet/mininet/releases/download/2.3.0/mininet-2.3.0-210211-ubuntu-20.04.1-legacy-server-amd64-ovf.zip

- Extract the file `mininet-vm-x86_64.vmdk` from the image:

  ```
  unzip mininet*zip mininet-vm-x86_64.vmdk
  ```

- Convert the disk image for use with libvirt/qemu:

  ```
  qemu-img convert -f vmdk -O raw mininet-vm-x86_64.vmdk mininet-vm-x86_64.img
  ```

- Boot a virtual machine from the image:

  ```
  virt-install -r 4096 -n mininet --os-variant ubuntu20.04 \
    --disk pool=default,size=10,format=qcow2,backing_store=$PWD/mininet-vm-x86_64.img,backing_format=raw \
    -w network=default \
    --import
  ```

  Once the image is up, you can log in as user `mininet` with password `mininet`.

### Configure the mininet virtual machine

- Enable the `ip_forward` sysctl

  ```
  sysctl net.ipv4.ip_forward=1 | tr -d ' ' > /etc/sysctl.d/ip_forward.conf
  ```

- Install some required packages:

  ```
  apt update
  apt install -y git nftables curl
  update-alternatives --set iptables /usr/sbin/iptables-nft
  ```

### Run the simulation

- Check out this repository on the mininet vm.

- Run the `implementation.py` script as root:

  ```
  sudo python implementation.py
  ```

This will start up the virtual network and bring you to the `mininet>` interactive prompt.

## Dramatis personae

The simulation defines the following resources.

### Hosts

- `client` -- this represents a machine "outside the cluster network", e.g., your home desktop.
- `host0` -- this represents an OpenShift cluster node
- `serv0` -- this represents a containerized service running on the cluster

### Networks

- `client` -- the client lives on this network
- `vpn` -- the client is able to connect to the internal address of cluster nodes over the VPN network.
- `host` -- the cluster nodes live on this network
- `service` -- containerized cluster services live on this network
- `internet` -- the client accesses cluster public addresses over this network

### Routers

- `r_client` -- the client connects to the internet through this router.
- `r_host` -- the default gateway for the cluster nodes
- `r_pub` -- the default gateway for the public network

## Using mininet

### At the mininet prompt

At the interactive `mininet>` prompt, you can:

- Run a command on a virtual host by entering the hostname and a shell comand:

  ```
  mininet> host0 ip route
  default via 10.30.6.1 dev host0-eth0
  10.30.6.0/23 dev host0-eth0 proto kernel scope link src 10.30.6.10
  10.94.61.0/24 dev host0-eth1 proto kernel scope link src 10.94.61.10
  172.30.0.0/16 dev host0-eth2 proto kernel scope link src 172.30.0.1
  ```

  Commands are run as `root` inside the network namespace that represents the host.

- Use the `dump` and `links` commands to get information about the virtual network.

### At the shell prompt

This repository includes a helper script `runin.sh` that makes it easy to run commands inside a virtual host namespace from the terminal. For example, the equivalent to the above `host0 ip route` command would be:

```
./runin.sh host0 ip route
```

This is particularly useful when you want to run `tcpdump` while executing things like `curl` from the `mininet>` prompt:

```
./runin.sh host0 tcpdump -nn -i any
```
