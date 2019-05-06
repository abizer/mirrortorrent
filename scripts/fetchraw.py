from torf import Torrent
import argparse
from paramiko import SSHClient
from scp import SCPClient
import os
import csv
import shutil
import warnings
import warnings
from common import SERVERS, machine_name

def fetchall_vnstat(dirname):
	"""
	SSHes into all the servers one by one, fetching
	the output of vnstat. 

	Creates csvs for each machine. 

	Takes in a directory name. Creates this directory in
	./ouputs. Places the csvs in the inner directory.
	"""

	# ssh init
	ssh = SSHClient()
	ssh.load_system_host_keys()


	directory_path = "raw_outputs/" + dirname
	# If the directory exists, ask user whether it should be deleted.
	if (os.path.isdir(directory_path)):
		print("WARNING: Directory exists and will be deleted. Continue? [y/Y]")
		if input() in ['y', 'Y']:
			shutil.rmtree(directory_path)
		else:
			exit()

	# Create the inner directory.
	os.mkdir("raw_outputs/" + dirname)

	results = {}

	# Iterate through the servers
	# Run `vnstat -5 200` on all of them
	# Fetch, parse, clean the results
	# Create csv files
	for server in SERVERS:
		print("Fetching from server ", server)
		results[machine_name(server[1])] = []
		ssh.connect(hostname=server[1], username=server[0], key_filename="/Users/mudit2103/.ssh/mirrortorrent.pem")
		command = "vnstat -5 200"
		(stdin, stdout, stderr) = ssh.exec_command(command)

		machine = machine_name(server[1])
		filename = directory_path + "/" + machine + ".csv"

		with open(filename, "w") as csvfile:
			csvwriter = csv.writer(csvfile)
			for line in stdout.readlines():
				line = line.replace("|", " ")
				line = line.split()
				if len(line) < 7:
					continue
				csvwriter.writerow(line)
				results[machine_name(server[1])].append(line)

	ssh.close()
	return results


if __name__ == "__main__":
	parser = argparse.ArgumentParser()

	parser.add_argument("dirname", help="directory to be created in ./outputs/ with the csvs")
	args = parser.parse_args()
	fetchall_vnstat(args.dirname)
	