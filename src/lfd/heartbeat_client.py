import argparse
import time
import requests

def lfd1(host, port, heartbeat_freq, timeout):
    last_response_time = time.time()
    server_url = f"http://{host}:{port}"

    while True:
        start_time = time.time()
        print(f"[LFD1] Sending heartbeat to {server_url}/heartbeat")
        try:
            r = requests.get(f"{server_url}/heartbeat", timeout=timeout)
            if r.status_code == 200 and r.json().get("ok"):
                last_response_time = time.time()
                print(f"[LFD1] Heartbeat acknowledged by {r.json().get('replica_id')} at {time.ctime()}")
            else:
                print(f"[LFD1 WARN] Unexpected heartbeat response: {r.text}")

        except requests.exceptions.RequestException:
            if time.time() - last_response_time > timeout:
                print(f"[LFD1 ERROR] Heartbeat failed! Server {server_url} not responding.")
            else:
                print(f"[LFD1 WARN] Temporary failure, will retry...")

        elapsed = time.time() - start_time
        time.sleep(max(0, heartbeat_freq - elapsed))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LFD1 Heartbeat Client")
    parser.add_argument("--host", default="0.0.0.0", help="Host (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8080, help="Port (default: 8080)")
    parser.add_argument("--freq", type=float, default=5.0, help="Heartbeat frequency in seconds")
    parser.add_argument("--timeout", type=float, default=10.0, help="Heartbeat timeout in seconds")
    args = parser.parse_args()

    print(f"[INFO] Starting LFD1 to {args.host}:{args.port} with heartbeat_freq={args.freq}s")
    lfd1(args.host, args.port, args.freq, args.timeout)
