# Torrent Network Implementation

This project is a simplified **torrent network** where users can share and download files from each other using a central tracker.  
It was developed as part of a **Computer Networks** course project.

## Overview

- **`tracker.py`** – Manages connected peers and tracks which files are available on which peers.  
- **`peer.py`** – Allows users to share files, download files, and request activity logs.

The system uses TCP sockets for communication between peers and the tracker.

## Peer Commands
- share – Share a file with the tracker so other peers can download it.
- get – Download a file from another peer through the tracker.
- request logs – Ask the tracker for this peer’s recent activity log.
- exit – Gracefully disconnect the peer from the tracker and close the connection.

## Tracker Commands
- logs request – View recent log requests from peers.
- all-logs – Display all logged activity from all peers.
- file_logs – Show logs related to specific shared or requested files.

## How It Works

1. Start the tracker first:
```
python3 tracker.py
```

2. Run a few peers and share files:
```
python3 peer.py
> share example.txt [ADDR]/example.txt
```

3. On another peer, request the shared file:
```
python3 peer.py
> get example.txt
```

4. View logs from the tracker:
```
> request logs
> all-logs
> file_logs example.txt
```


## Requirements
- Python 3.x
- Basic networking libraries (e.g., socket, threading, etc.) – included in the standard library

## Notes
- This is a simplified academic implementation of a torrent-like protocol for learning purposes.
- It is not intended for real-world file sharing.

## Author
- [Rozhin Taghizadegan](https://github.com/RozhTagh)
