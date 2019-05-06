from torf import Torrent
import argparse
from paramiko import SSHClient
from scp import SCPClient
import os
from os.path import isfile, join
import csv
import shutil
import warnings
import warnings
from common import SERVERS, machine_name, mkdir_safe
import matplotlib.pyplot as plt
import numpy as np

def load_dir(dirname):
	input_dirname = "parsed_outputs/" + dirname
	filepaths = [f for f in os.listdir(input_dirname) if isfile(join(input_dirname, f))]

	directory_path = "graphs/" + dirname
	# If the directory exists, ask user whether it should be deleted.
	if (os.path.isdir(directory_path)):
		print("WARNING: Directory exists and will be deleted. Continue? [y/Y]")
		if input() in ['y', 'Y']:
			shutil.rmtree(directory_path)
		else:
			exit()

	data = {}

	for path in filepaths:
		data[path] = parseraw_file(dirname + "/" + path)
	return data
	

def make_all_graphs(all_data, dirname, title, indices=[1, 2, 4]):
	experiments = {
		1: 'Recieved Data MiB',
		2: 'Trasmitted Data MiB',
		3: 'Total Data MiB',
		4: 'Average Rate Mbit/s'
	}

	all_values = list(all_data.values())
	a_machine_values = all_values[0]

	# The 0th item contains the times.	
	times = [x[0] for x in a_machine_values]
	number_of_items = len(a_machine_values[0]) - 1


	plt.figure(figsize=(8.3,11.7))
	plt.subplots_adjust(left=None, bottom=None, right=None, top=None, wspace=None, hspace=0.4)


	counter = 1
	for i in indices:
		data = {}

		for k, v in all_data.items():
			# Collect the i-th column from v.
			data[k] = [float(val[i]) for val in v]

		y_label = experiments[i]
		plt.subplot(len(indices), 1, counter)
		make_graph(data, times, y_label)

		if counter == 1:
			plt.title(title, loc='center', pad=40)

		counter += 1


	
	mkdir_safe('graphs/' + dirname)

# x = np.arange(10)

# fig = plt.figure()
# ax = plt.subplot(111)

# for i in xrange(5):
#     ax.plot(x, i * x, label='$y = %ix$'%i)

# # Shrink current axis by 20%
# box = ax.get_position()
# ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])

# # Put a legend to the right of the current axis
# ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))

# plt.show()

	
	plt.savefig('graphs/' + dirname + '/graph.png')

	


def parseraw_file(filepath):
	inp_prefix = "parsed_outputs/"

	with open(inp_prefix + filepath) as csvfile:
		csvreader = csv.reader(csvfile)
		rows = []
		for row in csvreader:
			rows.append(row)

		return rows


def make_graph(data, labels, y_label):
	"""
	Data is a dictionary of the form
	 {
		'machine_name': [rx1, rx2, rx3, ...],
		'machine_name2': [rx1, rx2, rx3, ...],
		...
	 }

	Labels is a list having the same length as 
	the lists that are the values of data. 

	it contains the times which are to be marked
	on the x-axes.
	"""
	print(data)

	for name, vals in data.items():
		plt.plot(labels, vals, label=name)

	plt.ylabel(y_label)
	plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.2),
          ncol=3, fancybox=True, shadow=True)





if __name__ == "__main__":
	parser = argparse.ArgumentParser()

	parser.add_argument("dirname", help="directory to be created in ./graphs/ with the graph")
	parser.add_argument("title", help="directory to be created in ./outputs/ with the csvs")
	args = parser.parse_args()

	all_data = load_dir(args.dirname)
	make_all_graphs(all_data, args.dirname, args.title)

	
	