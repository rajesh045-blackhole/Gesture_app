from utils.ipc import IPCClient
import time

def main():
    client = IPCClient()
    print("Sending 5 test events...")
    for i in range(5):
        event = {"gesture_id": i, "confidence": 0.9}
        client.send_event(event)
        print(f"Sent: {event}")
        time.sleep(0.5)
    print("Done.")

if __name__ == '__main__':
    main()
