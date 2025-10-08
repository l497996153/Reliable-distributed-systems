import argparse
import time
import requests
import os

def log(log_file, text):
    print(text)
    """Print and write log to log file."""
    with open(log_file, "a") as f:
        f.write(text + "\n")

def register_with_gfd(gfd_host, gfd_port, lfd_id, server_id, log_file, timeout=5):
    """向GFD注册LFD信息"""
    gfd_url = f"http://{gfd_host}:{gfd_port}/register"
    payload = {
        "lfd_id": lfd_id,
        "server_id": server_id,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    try:
        r = requests.post(gfd_url, json=payload, timeout=timeout)
        if r.status_code == 200:
            log(log_file, f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Registered with GFD successfully.")
            return True
        else:
            log(log_file, f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] WARN: GFD registration returned {r.status_code}")
    except requests.exceptions.RequestException as e:
        log(log_file, f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ERROR: Failed to register with GFD: {e}")
    return False

def report_status_to_gfd(gfd_host, gfd_port, lfd_id, server_id, status, log_file, timeout=5):
    """向GFD汇报状态"""
    gfd_url = f"http://{gfd_host}:{gfd_port}/status"
    payload = {
        "lfd_id": lfd_id,
        "server_id": server_id,
        "status": status,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    try:
        requests.post(gfd_url, json=payload, timeout=timeout)
    except requests.exceptions.RequestException as e:
        log(log_file, f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] WARN: Failed to report status to GFD: {e}")

def lfd1(host, port, gfd_host, gfd_port, heartbeat_freq, timeout, log_file):
    lfd_id = "LFD1"
    server_id = "S1"
    last_response_time = time.time()
    server_url = f"http://{host}:{port}"

    # 注册到GFD，确保成功
    while not register_with_gfd(gfd_host, gfd_port, lfd_id, server_id, log_file, timeout=timeout):
        log(log_file, f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Retry registering to GFD in 3s...")
        time.sleep(3)

    while True:
        start_time = time.time()
        log(log_file, f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {lfd_id} Sending heartbeat to {server_id}")
        try:
            r = requests.get(f"{server_url}/heartbeat", params={"lfd_id": lfd_id}, timeout=timeout)
            if r.status_code == 200 and r.json().get("ok"):
                last_response_time = time.time()
                log(log_file, f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {lfd_id} Heartbeat acknowledged by {r.json().get('replica_id')}")
                status = "alive"
            else:
                log(log_file, f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] WARN: Unexpected heartbeat response: {r.text}")
                status = "warn"
        except requests.exceptions.RequestException:
            if time.time() - last_response_time > timeout:
                log(log_file, f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ERROR: Heartbeat failed! {server_id} not responding.")
                status = "failed"
            else:
                log(log_file, f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] WARN: Temporary failure, will retry...")
                status = "warn"

        # 向GFD汇报状态
        report_status_to_gfd(gfd_host, gfd_port, lfd_id, server_id, status, log_file)

        elapsed = time.time() - start_time
        time.sleep(max(0, heartbeat_freq - elapsed))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LFD1 Heartbeat Client with GFD reporting")
    parser.add_argument("--host", default="0.0.0.0", help="Local server host (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8080, help="Local server port (default: 8080)")
    parser.add_argument("--gfd_host", default="127.0.0.1", help="GFD host (default: 0.0.0.0)")
    parser.add_argument("--gfd_port", type=int, default=6000, help="GFD port (default: 6000)")
    parser.add_argument("--freq", type=float, default=5.0, help="Heartbeat frequency in seconds")
    parser.add_argument("--timeout", type=float, default=10.0, help="Heartbeat timeout in seconds")
    args = parser.parse_args()

    start_time_filename  = time.strftime("%Y%m%d_%H:%M:%S")
    fld_id = "LFD1"
    log_file = os.path.join(os.path.dirname(__file__), "..",'..', "logs", f"fld_{fld_id}_log_{start_time_filename.replace(':','_')}.txt")

    log(log_file, f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Starting {fld_id} to http://{args.host}:{args.port} with heartbeat_freq={args.freq} and reporting to GFD http://{args.gfd_host}:{args.gfd_port}")
    try:
        lfd1(args.host, args.port, args.gfd_host, args.gfd_port, args.freq, args.timeout, log_file)
    except KeyboardInterrupt:
        print(f"\n\033[91m[{time.strftime('%Y-%m-%d %H:%M:%S')}] LFD1 terminated by user.\033[0m")
