from utils.ipc import IPCClient
import time
import json
from datetime import datetime

def main():
    client = IPCClient()
    print("Testing OS Actions via IPC with Latency Tracking...")
    
    # 1. Test Volume Up (Finger Clockwise - ID 1)
    print("Sending: Finger Clockwise (Volume Up)...")
    event = {
        "gesture_type": "finger_gesture",
        "hand_sign_id": 2, # Point
        "finger_gesture_id": 1, # Clockwise
        "confidence": 1.0,
        "timestamp": datetime.now().timestamp()
    }
    client.send_event(event) # Send twice to ensure rate limit allows one
    time.sleep(1.1) 
    
    event["timestamp"] = datetime.now().timestamp()
    client.send_event(event)

    # 2. Test Media Play (Hand Open - ID 0)
    print("Sending: Hand Open (Media Play)...")
    event = {
        "gesture_type": "hand_sign",
        "hand_sign_id": 0, # Open
        "finger_gesture_id": 0,
        "confidence": 1.0,
        "timestamp": datetime.now().timestamp()
    }
    client.send_event(event)

    print("Done. Check logs for latency measurements.")

if __name__ == '__main__':
    main()
