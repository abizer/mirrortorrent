#!/usr/bin/env python3

import networkx as nx
import math
import random
from prettytable import PrettyTable
import logging
#import matplotlib.pyplot as plt

from mtsim.graph import make_boring_graph, make_highlow_graph
from mtsim.relaxations import relax_dummy, relax_send_equal, relax_send_greedy
from mtsim.utils import *

logging.basicConfig(filename="example.log", level=logging.DEBUG)

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
