"""
Utility methods for the graphs
"""

import logging
from prettytable import PrettyTable

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
    receiver'sp rcv_util, and setting the sender's
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

    logging.debug(f"{sender_num} is sending {data} (size:{len(data)}) to {reciever_num}")


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


# def draw_graph(G, filename):
#     """
#     Draw the graph and save it.
#     Probably don't call it on anything with more than ~8 nodes otherwise
#     it doesn't look good.
#     """
#     pos = nx.spring_layout(G)
#     nx.draw(G, pos)
#     labels = nx.get_edge_attributes(G, "weight")
#     nx.draw_networkx_edge_labels(G, pos, edge_labels=labels)
#     nx.draw_networkx_labels(G, pos, labels=nx.get_node_attributes(G, "bw"))

#     plt.savefig(filename)
#     plt.close("all")


def commit_buffer(G):
    """
    Commits the buffer placed in all nodes in the graph
    to the actual data.
    :param G: NetworkX Graph
    :return: None
    """
    for node in G.nodes():
        G.nodes[node]["data"].update(G.nodes[node]["buffer"])

