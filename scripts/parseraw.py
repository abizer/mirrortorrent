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

def parseraw_dir(dirname, start, end):
	input_dirname = "raw_outputs/" + dirname
	filepaths = [f for f in os.listdir(input_dirname) if isfile(join(input_dirname, f))]

	mkdir_safe(directory_path)



	for path in filepaths:
		parseraw_file(dirname + "/" + path, start, end)



def parseraw_file(filepath, start, end):
	start_seen = False

	inp_prefix = "raw_outputs/"
	out_prefix = "parsed_outputs/"

	with open(inp_prefix + filepath) as csvfile, open(out_prefix + filepath, "w") as opfile:
		csvreader = csv.reader(csvfile)
		csvwriter = csv.writer(opfile)
		for row in csvreader:
			time = row[0]
			if time == start:
				start_seen = True

			if start_seen:
				csvwriter.writerow(parseraw_row(row))

			if time == end:
				return


def parseraw_row(row):
	"""
	Takes in a row like as follows:
	'05:10', '30.38', 'KiB', '54.45', 'KiB', '84.83', 'KiB', '2.32', 'kbit/s']

	Returns a list of 

	[time, rx, tx, total, speed] where everything is canonicalized to be
	MiB / Mbit/s, and time is kept as is.
	"""
	time = row[0]
	rx = row[1]
	rx_unit = row[2]
	tx = row[3]
	tx_unit = row[4]
	total = row[5]
	total_unit = row[6]
	speed = row[7]
	speed_unit = row[8]

	rx = canonicalize(rx, rx_unit)
	tx = canonicalize(tx, tx_unit)
	total = canonicalize(total, total_unit)
	speed = canonicalize(speed, speed_unit)

	return [time, rx, tx, total, speed]

	

def canonicalize(item, unit):
	conversions = {'B': 0.00000095367, 
				'KiB': 0.000976562, 
				'GiB': 1024,
				'MiB': 1,
				'kbit/s': 0.001,
				'Mbit/s': 1,
				'bit/s': 0.000001,
				'Gbit/s': 1000}
	
	item = float(item)
	return item * conversions[unit]




if __name__ == "__main__":
	parser = argparse.ArgumentParser()

	parser.add_argument("dirname", help="directory to be created in ./outputs/ with the csvs")
	parser.add_argument("start", help="string exactly of the format 16:30 or 05:45 specifying the first entry to grab")
	parser.add_argument("end", help="string exactly of the format 16:30 or 05:45 specifying the last entry (inclusive) to grab")
	args = parser.parse_args()
	parseraw_dir(args.dirname, args.start, args.end)
	