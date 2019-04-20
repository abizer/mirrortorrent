import networkx as nx
import math
import random

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

	missing_data = {}
	suppliable_missing_data = {}

	for n in neighbors:
		missing_data[n] = all_data.difference(G.nodes[n]['data'])

	for key, value in missing_data.items():
		suppliable_data = value.intersection(G.nodes[node]['data'])
		if suppliable_data and (G.nodes[key]['rcv_util'] != G.nodes[key]['bw']): 
			suppliable_missing_data[key] = suppliable_data

	for n in suppliable_missing_data:
		target_bw = math.ceil(bandwidth / len(suppliable_missing_data))
		link_bw = G[node][n]['weight']
		remaining_send_bw = bandwidth - G.nodes[node]['send_util']
		remaining_recv_bw = G.nodes[n]['bw'] - G.nodes[n]['rcv_util']

		sendable_bw = min(target_bw, link_bw, remaining_send_bw, remaining_recv_bw)

		data_to_send = random.sample(suppliable_missing_data[n], sendable_bw)
		send(G, node, n, set(data_to_send))


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
		total_bw += G[node]['bw']
		used_send_bw += G[node]['send_util']
		used_rcv_bw += G[node]['rcv_util']

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

def make_graph(num_nodes, all_data, edges=None):
	"""
	TODO: Add comment here, and find a way to 
	use the edges parameter.
	"""
	G = nx.DiGraph()
	for i in range(num_nodes):
		for j in range(num_nodes):
			if i != j:
				G.add_edge(i, j, weight=1)

	G.nodes[0]['data'] = all_data
	G.nodes[0]['bw'] = 4
	G.nodes[0]['send_util'] = 0
	G.nodes[0]['rcv_util'] = 0

	for i in range(1, len(G.nodes)):
		G.nodes[i]['data'] = set()
		G.nodes[i]['bw'] = 4
		G.nodes[i]['send_util'] = 0
		G.nodes[i]['rcv_util'] = 0

	return G

G = make_graph(100, set([i for i in range(5)]))


time = 0

while not completed(G, G.nodes[0]['data']):
	for node in G.nodes:
		relax_send_equal(G, node, set([i for i in range(5)]))
	print(G.nodes.data())
	time += 1
	reset_utils(G)

time_to_completion = time
