#!/usr/bin/env python3
"""Monitor false positives by running detector without actions."""

import sys
import time
import socket
import json
import signal
from collections import defaultdict

SOCKET_PATH = '/tmp/gestured.sock'

class FalsePositiveMonitor:
    def __init__(self, duration_sec=60):
        self.duration_sec = duration_sec
        self.counts = defaultdict(int)
        self.start_time = None
        self.running = True
        
    def run(self):
        print(f"Starting False Positive Monitor for {self.duration_sec} seconds...")
        print("Please perform NO gestures during this time.")
        
        # Connect to detector socket as if we are executor
        # CAUTION: This means we need to STOP the real executor first.
        
        if getattr(socket, 'AF_UNIX', None) is None:
             print("Unix sockets not supported")
             return

        import os
        if os.path.exists(SOCKET_PATH):
            os.remove(SOCKET_PATH)
            
        server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        server.bind(SOCKET_PATH)
        server.listen(1)
        server.settimeout(5.0) # Check for timeout every 5s to allow processing loop
        
        self.start_time = time.time()
        
        try:
            print("Current Status: Waiting for detector connection...")
            while self.running:
                try:
                    conn, _ = server.accept()
                    self._handle_client(conn)
                except socket.timeout:
                    if time.time() - self.start_time > self.duration_sec:
                        self.running = False
                except KeyboardInterrupt:
                    self.running = False
                    
        finally:
            server.close()
            if os.path.exists(SOCKET_PATH):
                os.remove(SOCKET_PATH)
        
        self._report()

    def _handle_client(self, conn):
        print("Detector connected. Monitoring...")
        import struct
        try:
            while self.running:
                if time.time() - self.start_time > self.duration_sec:
                    self.running = False
                    break
                    
                header = conn.recv(4)
                if not header: break
                msg_len = struct.unpack('>I', header)[0]
                data = conn.recv(msg_len)
                if not data: break
                
                event = json.loads(data.decode('utf-8'))
                
                # Check for NON-IDLE detections
                # Assuming ID -1 or 0 for "Open Hand" might be idle depending on config.
                # In our config:
                # Hand Open: 0
                # Hand Closed: 1
                # Point: 2
                
                # Finger:
                # Stationary: 0
                
                gesture_type = event.get('gesture_type')
                hand_id = event.get('hand_sign_id')
                finger_id = event.get('finger_gesture_id')
                
                # Logic: Any recognized active gesture is a potential false positive if user is doing nothing.
                # Hand Open (0) is often the default "rest" pose in MediaPipe if showing hands.
                # But it triggers "Play". This is a known risk.
                
                # Log everything except maybe "No Detection" if we had that event.
                # Detector sends event ONLY for multi_hand_landmarks presence? 
                # Yes, in detector run loop: "if results.multi_hand_landmarks:"
                
                # So ANY event is a detection of a hand.
                label = f"{gesture_type} | Hand:{hand_id} Finger:{finger_id}"
                self.counts[label] += 1
                
        except Exception as e:
            print(f"Connection error: {e}")
        finally:
            conn.close()

    def _report(self):
        print("\n" + "="*40)
        print("FALSE POSITIVE REPORT")
        print("="*40)
        print(f"Duration: {self.duration_sec} seconds")
        print(f"Total Detections: {sum(self.counts.values())}")
        print("-" * 20)
        for label, count in self.counts.items():
            print(f"{label}: {count}")
        print("="*40)

if __name__ == '__main__':
    monitor = FalsePositiveMonitor(duration_sec=10) # Short default for testing
    monitor.run()
