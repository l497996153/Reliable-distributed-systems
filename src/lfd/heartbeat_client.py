import argparse
import time
import requests
import os

def log(log_file, text):
    print(text)
    """Print and write log to log file."""
    with open(log_file, "a") as f:
        f.write(text + "\n")
        
def lfd1(host, port, heartbeat_freq, timeout, log_file):
    fld_id = "LFD1"
    server_id = "S1"
    last_response_time = time.time()
    server_url = f"http://{host}:{port}"

    while True:
        start_time = time.time()
        log(log_file, f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] LFD1 Sending heartbeat to {server_id}")
        # print(f"[{time.strftime("%Y-%m-%d %H:%M:%S")}] LFD1 Sending heartbeat to {server_url}/heartbeat")
        try:
            r = requests.get(f"{server_url}/heartbeat", params={"fld_id": fld_id}, timeout=timeout)
            if r.status_code == 200 and r.json().get("ok"):
                last_response_time = time.time()
                log(log_file, f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] LFD1 Heartbeat acknowledged by {r.json().get('replica_id')}")
                # print(f"[{time.strftime("%Y-%m-%d %H:%M:%S")}] LFD1 Heartbeat acknowledged by {r.json().get('replica_id')} at {time.ctime()}")
            else:
                log(log_file, f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] LFD1 WARN: Unexpected heartbeat response: {r.text}")
                # print(f"[{time.strftime("%Y-%m-%d %H:%M:%S")}] LFD1 WARN: Unexpected heartbeat response: {r.text}")
        except requests.exceptions.RequestException:
            if time.time() - last_response_time > timeout:
                log(log_file, f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] LFD1 ERROR Heartbeat failed! {server_id} not responding.")
                # print(f"[{time.strftime("%Y-%m-%d %H:%M:%S")}] LFD1 ERROR Heartbeat failed! Server {server_url} not responding.")
            else:
                log(log_file, f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] LFD1 WARN Temporary failure, will retry...")
                # print(f"[{time.strftime("%Y-%m-%d %H:%M:%S")}] LFD1 WARN Temporary failure, will retry...")

        elapsed = time.time() - start_time
        time.sleep(max(0, heartbeat_freq - elapsed))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LFD1 Heartbeat Client")
    parser.add_argument("--host", default="0.0.0.0", help="Host (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8080, help="Port (default: 8080)")
    parser.add_argument("--freq", type=float, default=5.0, help="Heartbeat frequency in seconds")
    parser.add_argument("--timeout", type=float, default=10.0, help="Heartbeat timeout in seconds")
    args = parser.parse_args()
    start_time_filename  = time.strftime("%Y%m%d_%H:%M:%S")
    fld_id = 1
    log_file = os.path.join(os.path.dirname(__file__), "..",'..', "logs", f"fld_{fld_id}_log_{start_time_filename}.txt")
    log(log_file, f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Starting LFD1 to {args.host}:{args.port} with heartbeat_freq={args.freq}")
    # print(f"[{time.strftime("%Y-%m-%d %H:%M:%S")}] Starting LFD1 to {args.host}:{args.port} with heartbeat_freq={args.freq}s")
    lfd1(args.host, args.port, args.freq, args.timeout, log_file)
