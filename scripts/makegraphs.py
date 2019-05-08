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
from scipy.interpolate import interp1d

def smoothen(x, y):

	x=np.array(x)
	y=np.array(y)

	x_new = np.linspace(x.min(), x.max(),500)

	f = interp1d(x, y, kind='quadratic')
	y_smooth = f(x_new)

	return x_new, y_smooth

	# plt.plot (x_new,y_smooth)
	# plt.scatter (x, y)



def load_dir(dirname):
	input_dirname = "parsed_outputs/" + dirname
	filepaths = [f for f in os.listdir(input_dirname) if isfile(join(input_dirname, f))]

	directory_path = "graphs/" + dirname
	# If the directory exists, ask user whether it should be deleted.
	# if (os.path.isdir(directory_path)):
	# 	print("WARNING: Directory exists and will be deleted. Continue? [y/Y]")
	# 	if input() in ['y', 'Y']:
	# 		shutil.rmtree(directory_path)
	# 	else:
	# 		exit()

	data = {}

	for path in filepaths:
		data[path] = parseraw_file(dirname + "/" + path)
	return data
	

def make_all_graphs(all_data, dirname, title, savedir, indices=[1, 2, 4]):
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


	plt.figure(figsize=(8.3, 11.7))
	plt.subplots_adjust(left=None, bottom=None, right=None, top=None, wspace=0, hspace=0.4)

	# Done to fix the order of the keys...
	alldata_keys = list(all_data.keys())

	counter = 1
	for i in indices:
		data = []

		for k in alldata_keys:
			v = all_data[k]
			# Collect the i-th column from v.
			data.append((k, [float(val[i]) for val in v]))

		y_label = experiments[i]
		plt.subplot(len(indices), 1, counter)
		make_graph(data, times, y_label)

		if counter == 1:
			plt.title(title, loc='center', pad=20)
			plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.4),
          ncol=6, fancybox=True, shadow=True)

		counter += 1


	print("savedir is ", savedir)
	mkdir_safe('graphs/' + savedir)
	plt.savefig('graphs/' + savedir + '/graph.png')

	


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
	Data is a list of the form
	 [
		('machine_name': [rx1, rx2, rx3, ...]),
		('machine_name2': [rx1, rx2, rx3, ...]),
		...
	 ]

	Labels is a list having the same length as 
	the lists that are the values of data. 

	it contains the times which are to be marked
	on the x-axes.
	"""
	print(data)

	for x in data:
		name, vals = x

		labels = [i*5 for i in range(len(labels))]
		smooth_labels, smooth_vals = smoothen(labels, vals)
		smooth_vals = smooth_vals.clip(min=0)

		plt.plot(smooth_labels, smooth_vals, label=name)

	plt.ylabel(y_label)
	plt.xlabel("minutes")
	





if __name__ == "__main__":
	parser = argparse.ArgumentParser()

	parser.add_argument("dirname", help="directory to be created in ./graphs/ with the graph")
	parser.add_argument("title", help="directory to be created in ./outputs/ with the csvs")
	parser.add_argument("savedir", help="place result here", nargs='?', default=None)
	args = parser.parse_args()

	print(args.savedir)

	all_data = load_dir(args.dirname)
	make_all_graphs(all_data, args.dirname, args.title, args.savedir if args.savedir else args.dirname)

	
	