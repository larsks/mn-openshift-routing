'''A hacky script for visualizing the network topology. In order to run this
you will need to install:

- networkx
- pygraphviz
- pydot
- mininet

Run the script to produce the file "topo.dot", and then use your favorite
graphviz tool to produce a visuzliation. E.g.:

    neato -t svg -o topo.svg topo.dot
'''

import networkx as nx
from networkx.drawing.nx_pydot import write_dot
import topo

net = topo.MyNetwork()
net.build()

G = net.g.convertTo(nx.graph.Graph)
pos = nx.nx_agraph.graphviz_layout(G)
nx.draw(G, pos=pos)
write_dot(G, 'topo.dot')
