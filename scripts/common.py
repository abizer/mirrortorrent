from torf import Torrent
import argparse
from paramiko import SSHClient
from scp import SCPClient
import os
import csv
import shutil
import warnings
import warnings
warnings.filterwarnings(action='ignore',module='.*paramiko.*')


SERVERS = [("root", "268.0x00.sh"),
           ("ubuntu", "eun1a.268.0x00.sh"), 
           ("ubuntu", "euw1b.268.0x00.sh"), 
           ("ubuntu", "sae1a.268.0x00.sh"), 
           ("ubuntu", "use2a.268.0x00.sh"), 
           ("ubuntu", "usw1a.268.0x00.sh")]

def machine_name(machine_url):
	return machine_url.split(".")[0]

def mkdir_safe(directory_path):
	# If the directory exists, ask user whether it should be deleted.
	if (os.path.isdir(directory_path)):
		print("WARNING: Directory exists and will be deleted. Continue? [y/Y]")
		if input() in ['y', 'Y']:
			shutil.rmtree(directory_path)
		else:
			exit()

	# Create the inner directory.
	os.mkdir(directory_path)