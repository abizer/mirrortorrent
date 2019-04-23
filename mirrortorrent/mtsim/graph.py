"""
Methods for building graph topologies for the simulation
"""

import networkx as nx
import math
import random

def make_graph(num_nodes, all_data, bandwidths, edges):
    """
    num_nodes: Number of nodes in the graph.
    all_data: A set of the data that is to be transferred.
    bandwidths: A list whose len is num_nodes. Contains the
                bandwidth that the node can support.
    edges: A map containing keys 0...num_nodes-1, and values
           that are lists of size num_nodes, containing the
           link capacities from key->index. 
           Note that edges[x][x] is always ignored. 
    """
    assert len(bandwidths) == num_nodes
    assert len(edges) == num_nodes

    G = nx.DiGraph()
    for i in range(num_nodes):
        for j in range(num_nodes):
            if i != j:
                G.add_edge(i, j, weight=edges[i][j])

    G.nodes[0]["data"] = all_data
    G.nodes[0]["buffer"] = set()
    G.nodes[0]["bw"] = bandwidths[0]
    G.nodes[0]["send_util"] = 0
    G.nodes[0]["rcv_util"] = 0

    for i in range(1, len(G.nodes)):
        G.nodes[i]["data"] = set()
        G.nodes[i]["buffer"] = set()
        G.nodes[i]["bw"] = bandwidths[i]
        G.nodes[i]["send_util"] = 0
        G.nodes[i]["rcv_util"] = 0

    return G


def make_boring_graph(num_nodes, all_data, bandwidth, link_cap):
    """
    Makes a boring graph with `num_nodes` nodes. The bandwidth 
    and link capacities of all nodes are `bandwidth` and `link_cap`
    respectively.
    """
    bandwidths = [bandwidth for i in range(num_nodes)]
    edges = {k: [link_cap for k in range(num_nodes)] for k in range(num_nodes)}

    G = make_graph(num_nodes, all_data, bandwidths, edges)
    return G


def make_highlow_graph(
    all_data, num_high_bw_nodes, num_low_bw_nodes, high_bw, low_bw, high_cap, low_cap
):
    """Creates a graph with some (high_bandwidth, high_link_capacity) nodes
    and some (low_bandwidth, low_link_capacity) nodes.

    These nodes are all interconnected.
    """
    num_high_bw_nodes = num_high_bw_nodes
    num_low_bw_nodes = num_low_bw_nodes

    bandwidths = [high_bw for x in range(num_high_bw_nodes)]
    bandwidths += [low_bw for x in range(num_low_bw_nodes)]

    edges = {}
    for i in range(num_high_bw_nodes + num_low_bw_nodes):
        edges[i] = [high_cap for x in range(num_high_bw_nodes)]
        edges[i] += [low_cap for x in range(num_low_bw_nodes)]

    return make_graph(num_high_bw_nodes + num_low_bw_nodes, all_data, bandwidths, edges)


def MAKE_X_GRAPH():
    """
    To create a new topology, write a method here that takes in arguments and
    ultimately calls `make_graph` and returns it.
    """
    pass

