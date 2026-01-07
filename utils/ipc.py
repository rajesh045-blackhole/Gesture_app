import socket
import os
import json
import struct
import logging

SOCKET_PATH = '/tmp/gestured.sock'

class IPCServer:
    def __init__(self, socket_path=SOCKET_PATH):
        self.socket_path = socket_path
        self.sock = None
        self._setup_socket()

    def _setup_socket(self):
        if os.path.exists(self.socket_path):
            os.remove(self.socket_path)
        
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.bind(self.socket_path)
        self.sock.listen(1)
        logging.info(f"IPC Server listening on {self.socket_path}")

    def listen(self):
        while True:
            conn, _ = self.sock.accept()
            try:
                while True:
                    # Read message length (4 bytes)
                    raw_len = conn.recv(4)
                    if not raw_len:
                        break
                    msg_len = struct.unpack('>I', raw_len)[0]
                    # Read message data
                    data = conn.recv(msg_len)
                    if not data:
                        break
                    yield json.loads(data.decode('utf-8'))
            except Exception as e:
                logging.error(f"IPC Error: {e}")
            finally:
                conn.close()

class IPCClient:
    def __init__(self, socket_path=SOCKET_PATH):
        self.socket_path = socket_path
        self.sock = None
        self._connect()

    def _connect(self):
        try:
            self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.sock.connect(self.socket_path)
            logging.info(f"Connected to IPC Server at {self.socket_path}")
        except Exception as e:
            logging.error(f"Could not connect to IPC Server: {e}")
            self.sock = None

    def send_event(self, event_data):
        if not self.sock:
            self._connect()
            if not self.sock:
                return

        try:
            data = json.dumps(event_data).encode('utf-8')
            msg_len = struct.pack('>I', len(data))
            self.sock.sendall(msg_len + data)
        except Exception as e:
            logging.error(f"Error sending event: {e}")
            self.sock.close()
            self.sock = None
