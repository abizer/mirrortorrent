from torf import Torrent
import argparse
from paramiko import SSHClient
from scp import SCPClient
import os



SERVERS = [ # "268.0x00.sh",
           "eun1a.268.0x00.sh", 
           # "eun2a.268.0x00.sh", 
           "euw1b.268.0x00.sh", 
           "sae1a.268.0x00.sh", 
           "use2a.268.0x00.sh", 
           # "usnyc1.268.0x00.sh", 
           # "ussfo2.268.0x00.sh", 
           "usw1a.268.0x00.sh"]

WATCH_FILES = "downloads/"
WATCH_TORRENTS = "watch/"

def make_torrent(content_path, tracker, output_name):
	t = Torrent(path=content_path,
            trackers=[tracker],
            comment='-')
	t.generate()

	torrent_path = output_name + ".torrent"

	if os.path.exists(torrent_path):
  		os.remove(torrent_path)
	t.write(torrent_path)
	return torrent_path

def push(content_path, torrent_path):
	ssh = SSHClient()
	ssh.load_system_host_keys()
	for server in SERVERS:
		ssh.connect(hostname=server, username='ubuntu', key_filename="/Users/mudit2103/.ssh/mirrortorrent.pem")
	
		# SCPCLient takes a paramiko transport as an argument
		scp = SCPClient(ssh.get_transport())
			
		# Uploading the 'test' directory with its content in the
		# '/home/user/dump' remote directory
		# scp.put(content_path, remote_path='~/' + WATCH_FILES)
		scp.put(torrent_path, remote_path='~/' + WATCH_TORRENTS)
		
		scp.close()

if __name__ == "__main__":
	parser = argparse.ArgumentParser()

	parser.add_argument("content", help="path to content")
	parser.add_argument("tracker", help="tracker url, remember to add /announce")
	parser.add_argument("output", help="torrent file name")

	args = parser.parse_args()

	torrent_path = make_torrent(args.content, args.tracker, args.output)
	push(args.content, torrent_path)
	