import socket
import threading
import json
import os
import logging


class Peer:
    def __init__(self, tracker_ip, tracker_port, peer_id):
        self.tracker_ip = tracker_ip
        self.tracker_port = tracker_port
        self.peer_id = peer_id
        self.files = {}  # {file_name: file_path}
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self.tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_sock.bind(('0.0.0.0', 0))  # Bind to any available port
        self.tcp_sock.listen(5)
        self.tcp_port = self.tcp_sock.getsockname()[1]  # Get assigned port

        self.log_file = f'.peer_{self.peer_id}.log'
        logging.basicConfig(filename=self.log_file, level=logging.INFO, format='%(asctime)s - %(message)s')

        threading.Thread(target=self.listen_for_file_requests, daemon=True).start()
        self.join_network()

    def join_network(self):
        request = {
            'action': 'join',
            'peer_id': self.peer_id,
            'files': list(self.files.keys()),
            'tcp_port': self.tcp_port  # Send TCP port
        }
        self.sock.sendto(json.dumps(request).encode(), (self.tracker_ip, self.tracker_port))
        data, _ = self.sock.recvfrom(1024)
        response = json.loads(data.decode())
        if response.get('status') == 'ok':
            logging.info(f"Peer {self.peer_id} joined the network on TCP port {self.tcp_port}")
            print(f"Peer {self.peer_id} joined the network on TCP port {self.tcp_port}")

    def share_file(self, file_name, file_path):
        if os.path.exists(file_path):
            if file_name not in self.files:
                self.files[file_name] = file_path

            request = {
                'action': 'share_file',
                'peer_id': self.peer_id,
                'file': file_name
            }
            self.sock.sendto(json.dumps(request).encode(), (self.tracker_ip, self.tracker_port))
            logging.info(f"Peer {self.peer_id} updated shared files: {self.files}")
            print(f"Peer {self.peer_id} shared a new files: {file_name}")
        else:
            logging.error(f"File {file_path} does not exist")
            print(f"File {file_path} does not exist")

    def get_file(self, file_name):
        request = {
            'action': 'get_peers',
            'peer_id': self.peer_id,
            'file_name': file_name
        }
        self.sock.sendto(json.dumps(request).encode(), (self.tracker_ip, self.tracker_port))
        data, _ = self.sock.recvfrom(1024)
        response = json.loads(data.decode())

        peers = response.get('peers', [])
        if not peers:
            print(f"No peers found with file {file_name}")
            return

        print("Available Peers: ")
        for i in range(len(peers)):
            print(f"{i+1}: ip: {peers[i][0]}, port: {peers[i][1]}")

        peer_index = int(input("Desired Peer: ")) - 1

        peer_ip, peer_port = peers[peer_index]
        print(f"Connecting to peer at {peer_ip}:{peer_port}")

        try:
            tcp_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tcp_client.connect((peer_ip, peer_port))
            tcp_client.send(file_name.encode())

            with open(file_name, 'wb') as f:
                while True:
                    data = tcp_client.recv(1024)
                    if not data:
                        break
                    f.write(data)
            tcp_client.close()

            new_request = {
                'action': 'got_the_file',
                'peer_id': self.peer_id,
                'file_name': file_name
            }

            self.sock.sendto(json.dumps(new_request).encode(), (self.tracker_ip, self.tracker_port))
            data, _ = self.sock.recvfrom(1024)

            logging.info(f"Downloaded file {file_name} from {peer_ip}:{peer_port}")
            print(f"Downloaded file {file_name} successfully.")
        except Exception as e:
            logging.info(f"Error downloading file {file_name} from {peer_ip}:{peer_port}")
            print(f"Error downloading file {file_name}: {e}")

    def listen_for_file_requests(self):
        while True:
            conn, addr = self.tcp_sock.accept()
            file_name = conn.recv(1024).decode()
            print(f"Sending file {file_name} to {addr}")

            if file_name in self.files:
                with open(self.files[file_name], 'rb') as f:
                    while chunk := f.read(1024):
                        conn.send(chunk)
            conn.close()

    def request_logs(self):
        try:
            with open(self.log_file, 'r') as log_file:
                for line in log_file:
                    if 'download' in line.lower():
                        print(line.strip())
        except Exception as e:
            print(f"Failed to read logs: {e}")

    def leave_network(self):
        request = {
            "action": "leave",
            "peer_id": self.peer_id
        }
        self.sock.sendto(json.dumps(request).encode(), (self.tracker_ip, self.tracker_port))
        print(f"Peer {self.peer_id} is leaving the network.")

    def start(self):
        while True:
            command = input("Enter command (share/get/request logs/exit): ").strip()
            if command.startswith("share"):
                _, file_name, file_path = command.split()
                self.share_file(file_name, file_path)
            elif command.startswith("get"):
                _, file_name = command.split()
                self.get_file(file_name)
            elif command.startswith("request logs"):
                self.request_logs()
            elif command == "exit":
                self.leave_network()
                break
            else:
                print("Please enter a valid command!")


if __name__ == "__main__":
    peer_id = input("Enter peer ID: ").strip()
    peer = Peer('127.0.0.1', 6771, peer_id)
    peer.start()
