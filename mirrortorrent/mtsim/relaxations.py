"""
Methods for choosing what data to transfer where.

"""

import math
import random
from .utils import *

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
