import socket
import threading
import json
import logging


class Tracker:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.peers = {}  # {peer_id: {'files': [file1, file2], 'address': (ip, tcp_port)}}
        self.file_to_peers = {}  # {file_name: [peer1, peer2]}
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.ip, self.port))

        self.log_file = '.tracker.log'
        logging.basicConfig(filename=self.log_file, level=logging.INFO, format='%(asctime)s - %(message)s')

        logging.info(f"Tracker started at {self.ip}:{self.port}")
        print(f"Tracker started at {self.ip}:{self.port}")

    def handle_peer_request(self, data, addr):
        try:
            request = json.loads(data.decode())
            action = request.get('action')

            if action == 'join':
                peer_id = request.get('peer_id')
                files = request.get('files', [])
                tcp_port = request.get('tcp_port')  # Get TCP port

                self.peers[peer_id] = {'files': files, 'address': (addr[0], tcp_port)}  # Store IP & TCP Port
                for file in files:
                    if file not in self.file_to_peers:
                        self.file_to_peers[file] = []
                    self.file_to_peers[file].append(peer_id)

                logging.info(f"Peer {peer_id} joined on TCP port {tcp_port}")
                print(f"Peer {peer_id} joined on TCP port {tcp_port}")

                self.sock.sendto(json.dumps({'status': 'ok'}).encode(), addr)

            elif action == 'share_file':
                peer_id = request.get('peer_id')
                new_file = request.get('file')

                if peer_id in self.peers:
                    self.peers[peer_id]['files'].append(new_file)

                    if new_file not in self.file_to_peers:
                        self.file_to_peers[new_file] = []
                    self.file_to_peers[new_file].append(peer_id)

                    logging.info(f"Peer {peer_id} shared file: {new_file}, status: success")
                    print(f"Peer {peer_id} updated files: {new_file}")
                    self.sock.sendto(json.dumps({'status': 'ok'}).encode(), addr)
                else:
                    logging.info(f"Peer {peer_id} shared file: {new_file}, status: fail")
                    self.sock.sendto(json.dumps({'status': 'error', 'message': 'Peer not found'}).encode(), addr)

            elif action == 'get_peers':
                peer_id = request.get('peer_id')
                file_name = request.get('file_name')
                if file_name in self.file_to_peers:
                    peers_with_file = self.file_to_peers[file_name]
                    peer_addresses = [self.peers[peer_id]['address'] for peer_id in peers_with_file]
                    self.sock.sendto(json.dumps({'peers': peer_addresses}).encode(), addr)
                    logging.info(f"Peer {peer_id} wants peers' names with file: {file_name}, status: success")
                else:
                    logging.info(f"Peer {peer_id} wants peers' names with file: {file_name}, status: fail")
                    self.sock.sendto(json.dumps({'peers': []}).encode(), addr)

            elif action == "got_the_file":
                peer_id = request.get('peer_id')
                file_name = request.get('file_name')
                if peer_id in self.peers:
                    # Update the peer's file list
                    self.peers[peer_id]['files'].append(file_name)

                    # Register new file associations
                    if file_name not in self.file_to_peers:
                        self.file_to_peers[file_name] = []
                    self.file_to_peers[file_name].append(peer_id)

                    logging.info(f"Peer {peer_id} downloaded the file file: {file_name}, status: success")
                    print(f"Peer {peer_id} downloaded the file file: {file_name}")
                    self.sock.sendto(json.dumps({'status': 'ok'}).encode(), addr)
                else:
                    logging.info(f"Peer {peer_id} shared file: {new_file}, status: fail")
                    self.sock.sendto(json.dumps({'status': 'error', 'message': 'Peer not found'}).encode(), addr)

            elif action == "leave":
                peer_id = request.get('peer_id')
                if peer_id in self.peers:
                    for file_name in self.peers[peer_id]['files']:
                        self.file_to_peers[file_name].remove(peer_id)
                        if not self.file_to_peers[file_name]:  # Remove empty file records
                            del self.file_to_peers[file_name]
                    del self.peers[peer_id]
                    logging.info(f"Peer {peer_id} left the network.")
                    print(f"Peer {peer_id} left the network.")
                self.sock.sendto(json.dumps({'status': 'ok'}).encode(), addr)

        except Exception as e:
            logging.error(f"Error handling request from {addr}: {e}")
            print(f"Error handling request from {addr}: {e}")

    def logs_request(self):
        try:
            with open(self.log_file, 'r') as log_file:
                print("Logs from tracker.log:")
                for line in log_file:
                    print(line.strip())
        except Exception as e:
            print(f"Failed to read logs: {e}")

    def all_logs(self):
        try:
            with open(self.log_file, 'r') as log_file:
                for line in log_file:
                    if 'shared' in line:
                        print(line.strip())
        except Exception as e:
            print(f"Failed to read logs: {e}")

    def file_logs(self, file_name):
        # if file_name not in self.file_to_peers.keys():
        #     print("File name does not exist.")
        # else:
            try:
                with open(self.log_file, 'r') as log_file:
                    for line in log_file:
                        if file_name in line:
                            print(line.strip())
            except Exception as e:
                print(f"Failed to read logs: {e}")

    def start(self):
        print(f"Tracker running at {self.ip}:{self.port}")
        threading.Thread(target=self.listen_for_peers).start()

        while True:
            command = input()
            if command.startswith('logs request'):
                self.logs_request()

            elif command.startswith('all-logs'):
                self.all_logs()

            elif command.startswith('file_logs'):
                _, file_name = command.split()
                self.file_logs(file_name)

            else:
                print("Please enter a valid command!")

    def listen_for_peers(self):
        while True:
            data, addr = self.sock.recvfrom(1024)
            threading.Thread(target=self.handle_peer_request, args=(data, addr)).start()


if __name__ == "__main__":
    tracker = Tracker('127.0.0.1', 6771)
    tracker.start()
