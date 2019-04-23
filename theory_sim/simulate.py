import networkx as nx
import math
import random
from prettytable import PrettyTable
import logging
import matplotlib.pyplot as plt


logging.basicConfig(filename="example.log", level=logging.DEBUG)
###########################################################################
#                   Graph Utilities.                                      #
###########################################################################
def get_missing_data(G, node, all_data):
    """
    Takes in a node, and all_data that exists to be distributed.
    Computes a map from node.neighbors -> data they are missing.
    Returns the map.
    """
    neighbors = G.neighbors(node)
    missing_data = {}
    for neighbor in neighbors:
        missing_data[neighbor] = all_data.difference(G.nodes[neighbor]["data"])

    return missing_data


def get_suppliable_missing_data(G, node, missing_data):
    """
    Takes in a node, and a map from node.neighbors -> missing data.
    Returns a map from 

    node.neighbors which haven't saturated their rcv_util -> 
                            intersection(missing data, data with node).

    This map is essentially a map from nodes to whom data can be supplied,
    to the data that can be supplied.
    """
    suppliable_missing_data = {}

    for neighbor, neighbor_missingdata in missing_data.items():
        suppliable_data = neighbor_missingdata.intersection(G.nodes[node]["data"])
        if suppliable_data and (G.nodes[neighbor]["rcv_util"] != G.nodes[neighbor]["bw"]):
            suppliable_missing_data[neighbor] = suppliable_data

    return suppliable_missing_data


def send(G, sender, reciever, data):
    """First, ensures the following.

    1. That sender has the data it is going 
    to send.
    2. That receiver does not have that data.
    3. That the sender's outgoing link to reciever 
    can handle the amount of data being sent.
    4. Ensures that the sender's send_util won't
    exceed the bandwidth.
    5. Ensures that the receiver's rcv_util won't
    exceed the bandwidth.

    Then, 'transfers' the data by adding the 
    data to the receiver's data, setting the
    receiver's rcv_util, and setting the sender's
    send_util.
    """
    sender_num = sender
    reciever_num = reciever
    sender = G.nodes[sender]
    reciever = G.nodes[reciever]

    assert data.issubset(sender["data"])
    assert len(data.intersection(reciever["data"])) == 0
    assert len(data) <= G[sender_num][reciever_num]["weight"]
    assert len(data) + sender["send_util"] <= sender["bw"]
    assert len(data) + reciever["rcv_util"] <= reciever["bw"]

    reciever["buffer"].update(data)

    reciever["rcv_util"] += len(data)
    sender["send_util"] += len(data)

    logging.debug(f"{sender_num} is sending {data}(size:{len(data)}) to {reciever_num}")


def get_util_percents(G, all_data):
    """Returns the percentage of the send, recv 
    utilization for the graph. 

    This should be called at the end of a time step.
    """
    total_possible_bw = 0
    used_rcv_bw = 0
    for node in G:
        # At this time step, compute how much data we recieved.
        used_rcv_bw += G.nodes[node]["rcv_util"]

        # Then compute how much data we were missing at the START of this time step.
        # Suppose at the start of this time step, I had 85 units of data.
        # rcv_util now is 5 (so I am getting 5 more units at this time step.)
        # G.nodes[node]["data"] is therefore equal to 90.
        # all_data is 100 units.
        # So 100 - 90 + 5 is how much data I was missing at the beginning.
        max_possible_recv = len(all_data) - len(G.nodes[node]["data"]) + used_rcv_bw

        # My total recieve util could be at most either the data I had to recieve
        # or my total bnadiwdth, and no more.
        total_possible_bw += min(max_possible_recv, G.nodes[node]["bw"])

    return used_rcv_bw / total_possible_bw


def reset_utils(G):
    """Should be called at the end of a time stamp,
    after retrieving the utilization percentages
    in order to reset the utilizations for the
    next time step.
    """
    for node in G:
        G.nodes[node]["send_util"] = 0
        G.nodes[node]["rcv_util"] = 0


def completed(G, all_data):
    """
    Returns whether or not the process is complete.
    The process is complete when all nodes have
    all the data.
    """
    for node in G.nodes:
        if G.nodes[node]["data"] != all_data:
            return False
    return True


def print_data(G):
    t = PrettyTable(["Node", "Total Data"])

    for node in G.nodes:
        t.add_row([node, len(G.nodes[node]["data"])])

    logging.info(t)


def get_max_possible_rate(G, sender, receiver):
    """
    Returns the maximum possible rate at which sender can send
    to receiver. This is calculated as the minimum of {the 
    link bandwidth between the sender and receiver, the
    remaining send bandwidth of the sender, and the remaining
    receive bandwidth of the receiver" 
    :param G: NetworkX Graph.
    :param sender: Node (number) in networkX graph.
    :param receiver: Node (number) in networkX graph.
    :return: 
    """
    link_bw = G[sender][receiver]["weight"]
    remaining_send_bw = G.nodes[sender]["bw"] - G.nodes[sender]["send_util"]
    remaining_recv_bw = G.nodes[receiver]["bw"] - G.nodes[receiver]["rcv_util"]

    return min(link_bw, remaining_recv_bw, remaining_send_bw)


def draw_graph(G, filename):
    """
    Draw the graph and save it.
    Probably don't call it on anything with more than ~8 nodes otherwise
    it doesn't look good.
    """
    pos = nx.spring_layout(G)
    nx.draw(G, pos)
    labels = nx.get_edge_attributes(G, "weight")
    nx.draw_networkx_edge_labels(G, pos, edge_labels=labels)
    nx.draw_networkx_labels(G, pos, labels=nx.get_node_attributes(G, "bw"))

    plt.savefig(filename)
    plt.close("all")

def commit_buffer(G):
    """
    Commits the buffer placed in all nodes in the graph
    to the actual data.
    :param G: NetworkX Graph
    :return: None
    """
    for node in G.nodes():
        G.nodes[node]["data"].update(G.nodes[node]["buffer"])


###############################################################################
#                         Relax methods                                       #
###############################################################################
def relax_dummy(G, node, all_data):
    node["data"] = [i for i in range(500)]


def relax_send_equal(G, node, all_data):
    """
    This relax method is a send-based relaxation.
    
    The node passed in, N, checks its neighbors to 
    see what data they don't yet have, and intersects
    that with the data that N has.

    N then 'equally' shares its available bandwidth
    with all the nodes that still need data.

    The context for this method only makes sense
    when considering a graph with link bandwidths
    to all neighbors.
    """
    bandwidth = G.nodes[node]["bw"]

    missing_data = get_missing_data(G, node, all_data)
    suppliable_missing_data = get_suppliable_missing_data(G, node, missing_data)

    # print(node, suppliable_missing_data)

    for n in suppliable_missing_data:
        # The target bandwidth here is 'equally' splitting its
        # bandwidth to each of the neighbors to whom data can be
        # supplied
        target_bw = math.ceil(bandwidth / len(suppliable_missing_data))
        max_possible = get_max_possible_rate(G, node, n)
        sendable_bw = min(target_bw, max_possible)
        data_to_send = random.sample(
            suppliable_missing_data[n],
            min(sendable_bw, len(suppliable_missing_data[n])),
        )
        send(G, node, n, set(data_to_send))


def relax_fully_random(G, node, all_data):
    """
    A totally random relaxation.
    
    Randomly pick a target bandwidth by picking an integer between
    [0, remaining send bandwidth], and send either that much data
    or data equivalent to the maximum possible rate 
    (whichever is greater).
    
    Note that ultimately, this style of random selection will lead to
    `node` either fully or almost exhausting its send bandwidth. 
    """
    missing_data = get_missing_data(G, node, all_data)
    suppliable_missing_data = get_suppliable_missing_data(G, node, missing_data)

    for n in suppliable_missing_data:
        target_bw = random.randint(0, G.nodes[node]["bw"] - G.nodes[node]["send_util"])
        max_possible = get_max_possible_rate(G, node, n)

        sendable_bw = min(target_bw, max_possible)
        data_to_send = random.sample(
            suppliable_missing_data[n],
            min(sendable_bw, len(suppliable_missing_data[n])),
        )
        send(G, node, n, set(data_to_send))


def relax_send_greedy(G, node, all_data):
    """
    For every node, figure out which nodes `node` can send to at the best rates.
    For instance, suppose that `node` has 5 neighbors, and it can send to them at 
    rates [20, 10, 15, 30, 50] –– first, it will send as much as possible to the
    50-node, then if still possible, it will send to the 30-node, and so on. 
    """
    missing_data = get_missing_data(G, node, all_data)
    suppliable_missing_data = get_suppliable_missing_data(G, node, missing_data)

    neighbors = G.neighbors(node)
    outgoing_caps = [(n, get_max_possible_rate(G, node, n)) for n in neighbors]
    outgoing_caps.sort(key=lambda x: -x[1])

    for n, rate in outgoing_caps:
        remaining_outgoing_cap = G.nodes[node]["bw"] - G.nodes[node]["send_util"]
        if remaining_outgoing_cap == 0:
            break

        if n not in suppliable_missing_data:
            # Cannot supply to n –– ignore it.
            continue

        sendable_bw = min(remaining_outgoing_cap, rate)
        data_to_send = random.sample(
            suppliable_missing_data[n],
            min(sendable_bw, len(suppliable_missing_data[n])),
        )

        send(G, node, n, set(data_to_send))


def RELAX_X_TEMPLATE(G, node, add_data):
    """
    To write more relax methods, make methods of this form.
    """
    pass


##################################################################################
#                         Graph topologies                                       #
##################################################################################
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


######################################################################
#                   Simulation                                       #
######################################################################
if __name__ == "__main__":
    all_data = set([i for i in range(4)])
    # G = make_boring_graph(100, all_data, 4, 100)
    G = make_boring_graph(
        5, all_data, 4, 1
    )

    time = 0
    # draw_graph(G, "temp.png")
    while not completed(G, G.nodes[0]["data"]):
        for node in G.nodes:
            relax_send_equal(G, node, all_data)
            # print(G.nodes.data())
        time += 1
        logging.info(get_util_percents(G, all_data))
        print(get_util_percents(G, all_data))
        reset_utils(G)
        commit_buffer(G)
        print_data(G)

    time_to_completion = time

    print("Completion time was", time_to_completion)
