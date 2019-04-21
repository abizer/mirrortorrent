import networkx as nx
import math
import random
from prettytable import PrettyTable

DEBUG = True

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
	for n in neighbors:
		missing_data[n] = all_data.difference(G.nodes[n]['data'])

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

	for key, value in missing_data.items():
		suppliable_data = value.intersection(G.nodes[node]['data'])
		if suppliable_data and (G.nodes[key]['rcv_util'] != G.nodes[key]['bw']): 
			suppliable_missing_data[key] = suppliable_data

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

	assert data.issubset(sender['data'])
	assert len(data.intersection(reciever['data'])) == 0
	assert len(data) <= G[sender_num][reciever_num]['weight']
	assert len(data) + sender['send_util'] <= sender['bw']
	assert len(data) + reciever['rcv_util'] <= reciever['bw']

	reciever['data'].update(data)

	reciever['rcv_util'] += len(data)
	sender['send_util'] += len(data)


def get_util_percents(G):
	"""Returns the percentage of the send, recv 
	utilization for the graph. 

	This should be called at the end of a time step.

	TODO: As it stands, this doesn't really make
	complete sense. For instance, is a node HAS
	all the data, its recv util will be 0, and so
	we might mis-report.
	"""
	total_bw = 0 
	used_send_bw = 0
	used_rcv_bw = 0
	for node in G:
		total_bw += G.nodes[node]['bw']
		used_send_bw += G.nodes[node]['send_util']
		used_rcv_bw += G.nodes[node]['rcv_util']

	return used_send_bw/total_bw, used_rcv_bw/total_bw

def reset_utils(G):
	"""Should be called at the end of a time stamp,
	after retrieving the utilization percentages
	in order to reset the utilizations for the
	next time step.
	"""
	for node in G:
		G.nodes[node]['send_util'] = 0
		G.nodes[node]['rcv_util'] = 0

def completed(G, all_data):
	"""
	Returns whether or not the process is complete.
	The process is complete when all nodes have
	all the data.
	"""
	for node in G.nodes:
		if G.nodes[node]['data'] != all_data:
			return False
	return True

def print_data(G):
	t = PrettyTable(['Node', 'Total Data'])

	for node in G.nodes:
		t.add_row([node, len(G.nodes[node]['data'])])
		
	print(t)

###############################################################################
#                         Relax methods                                       #
###############################################################################
def relax_dummy(G, node):
	node['data'] = [i for i in range(500)]

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
	neighbors = G.neighbors(node)
	bandwidth = G.nodes[node]['bw']

	missing_data = get_missing_data(G, node, all_data)
	suppliable_missing_data = get_suppliable_missing_data(G, node, missing_data)

	# print(node, suppliable_missing_data)

	for n in suppliable_missing_data:
		target_bw = math.ceil(bandwidth / len(suppliable_missing_data))
		link_bw = G[node][n]['weight']
		remaining_send_bw = bandwidth - G.nodes[node]['send_util']
		remaining_recv_bw = G.nodes[n]['bw'] - G.nodes[n]['rcv_util']

		sendable_bw = min(target_bw, link_bw, remaining_send_bw, remaining_recv_bw)

		data_to_send = random.sample(suppliable_missing_data[n], min(sendable_bw, len(suppliable_missing_data[n])))
		send(G, node, n, set(data_to_send))

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

	G.nodes[0]['data'] = all_data
	G.nodes[0]['bw'] = bandwidths[0]
	G.nodes[0]['send_util'] = 0
	G.nodes[0]['rcv_util'] = 0

	for i in range(1, len(G.nodes)):
		G.nodes[i]['data'] = set()
		G.nodes[i]['bw'] = bandwidths[i]
		G.nodes[i]['send_util'] = 0
		G.nodes[i]['rcv_util'] = 0

	return G

def make_boring_graph(num_nodes, all_data, bandwidth, link_cap):
	bandwidths = [bandwidth for i in range(num_nodes)]
	edges = {k: [link_cap for k in range(num_nodes)] for k in range(num_nodes)}

	G = make_graph(num_nodes, all_data, bandwidths, edges)
	return G






if __name__ == "__main__":
	all_data = set([i for i in range(500)])


	G = make_boring_graph(100, all_data, 4, 100)
	time = 0

	while not completed(G, G.nodes[0]['data']):
		for node in G.nodes:
			relax_send_equal(G, node, all_data)
		# print(G.nodes.data())
		time += 1
		print(get_util_percents(G))
		reset_utils(G)

		if DEBUG:
			print_data(G)
		

	time_to_completion = time

	print("Completion time was", time_to_completion)
