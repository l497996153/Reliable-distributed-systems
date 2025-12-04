import argparse
import time
import requests
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
import subprocess
import sys
import platform
import json
import threading
import multiprocessing

# -------------------- Global Variables --------------------
lfd_id = None
server_id = None
host = None
port = None
server_port = None
gfd_host = None
gfd_port = None
heartbeat_freq = None
timeout = None
log_file = None

delay_config = {
    "lfd_delay": 0,
    "server_delay": 0,
}
delay_lock = threading.Lock()

# ------------------- CPU Burn 进程管理 -------------------
burn_processes = []

def cpu_burner():
    """ 占满一个 CPU 核心的进程 """
    print(f"CPU burner process {os.getpid()} started")
    while True:
        pass

def start_cpu_burn():
    """ 启动所有 CPU burn 进程 """
    global burn_processes
    if burn_processes:
        print("CPU burn already running.")
        return

    num_cores = os.cpu_count()
    print(f"Starting {num_cores} CPU burners...")
    
    for _ in range(num_cores):
        p = multiprocessing.Process(target=cpu_burner)
        p.start()
        burn_processes.append(p)

def stop_cpu_burn():
    """ 停止全部 CPU burn 进程 """
    global burn_processes
    print("Stopping all CPU burners...")
    for p in burn_processes:
        p.terminate()
        p.join()
    burn_processes = []
    print("CPU burn stopped.")


# -------------------- Utils --------------------
def log(text):
    print(text)
    """Print and write log to log file."""
    with open(log_file, "a") as f:
        f.write(text + "\n")

def register_with_gfd():
    """向GFD注册LFD信息"""
    gfd_url = f"http://{gfd_host}:{gfd_port}/register"
    payload = {
        "lfd_id": lfd_id,
        "server_id": server_id,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "lfd_host": host,
        "lfd_port": port
    }
    try:
        r = requests.post(gfd_url, json=payload, timeout=timeout)
        if r.status_code == 200:
            log(f"\033[32m[{time.strftime('%Y-%m-%d %H:%M:%S')}] Registered with GFD successfully.\033[0m")
            return True
        else:
            log(f"\033[33m[{time.strftime('%Y-%m-%d %H:%M:%S')}] WARN: GFD registration returned {r.status_code}\033[0m")
    except requests.exceptions.RequestException as e:
        log(f"\033[31m[{time.strftime('%Y-%m-%d %H:%M:%S')}] ERROR: Failed to register with GFD: {e}\033[0m")
    return False

def report_status_to_gfd(status):
    """向GFD汇报状态"""
    gfd_url = f"http://{gfd_host}:{gfd_port}/status"
    payload = {
        "lfd_id": lfd_id,
        "server_id": server_id,
        "status": status,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "lfd_host": host,
        "lfd_port": port
    }
    try:
        requests.post(gfd_url, json=payload, timeout=timeout)
    except requests.exceptions.RequestException as e:
        log(f"\033[33m[{time.strftime('%Y-%m-%d %H:%M:%S')}] WARN: Failed to report status to GFD: {e}\033[0m")

# -------------------- LFD Heartbeat --------------------
def lfd1():
    last_response_time = time.time()
    server_url = f"http://{host}:{server_port}"

    lfd_has_registered = False
    has_logged_failure = False

    while True:
        start_time = time.time()
        log(f"\033[35m[{time.strftime('%Y-%m-%d %H:%M:%S')}] {lfd_id}: Sending heartbeat to {server_id}\033[0m")
        try:
            r = requests.get(f"{server_url}/heartbeat", params={"lfd_id": lfd_id}, timeout=timeout)
            if r.status_code == 200 and r.json().get("ok"):
                last_response_time = time.time()
                has_logged_failure = False
                log(f"\033[35m[{time.strftime('%Y-%m-%d %H:%M:%S')}] {lfd_id}: Heartbeat acknowledged by {r.json().get('replica_id')}\033[0m")
                if not lfd_has_registered:
                    log(f"\033[32m[{time.strftime('%Y-%m-%d %H:%M:%S')}] {lfd_id}: add replica {server_id}.\033[0m")
                    while not register_with_gfd():
                        log(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Retry registering to GFD in 3s...")
                        time.sleep(3)
                    lfd_has_registered = True
                status = "alive"
            else:
                log(f"\033[33m[{time.strftime('%Y-%m-%d %H:%M:%S')}] WARN: Unexpected heartbeat response: {r.text}\033[0m")
                status = "warn"
        except requests.exceptions.RequestException:
            if time.time() - last_response_time > timeout:
                log(f"\033[31m[{time.strftime('%Y-%m-%d %H:%M:%S')}] ERROR: Timeout! {server_id} does not respond.\033[0m")
                status = "failed"
                if not has_logged_failure:
                    log(f"\033[31m[{time.strftime('%Y-%m-%d %H:%M:%S')}] {lfd_id}: delete replica {server_id} \033[0m")
                    has_logged_failure = True
            else:
                log(f"\033[33m[{time.strftime('%Y-%m-%d %H:%M:%S')}] WARN: Does not receive respond from {server_id}, will retry...\033[0m")
                status = "warn"

        # 向GFD汇报状态
        report_status_to_gfd(status)

        elapsed = time.time() - start_time
        time.sleep(max(0, heartbeat_freq - elapsed))

        with delay_lock:
            lfd_delay = delay_config.get("lfd_delay", 0)
        if lfd_delay > 0:
            time.sleep(lfd_delay)

# -------------------- Recovery --------------------
def recover_server_locally(server_id):

    server_index = server_id[-1]
    script_path = os.path.join(
        os.path.dirname(__file__),
        "..", "..", "milestone_demos",
        f"script_server_{server_index}.py"
    )

    system = platform.system()

    if system == "Windows":

        subprocess.Popen(["cmd", "/c", "start", "python", script_path])

    elif system == "Darwin":  # macOS
        print("mac os detected")
        command = f'python {script_path}'
        apple_script = f'''
        tell application "Terminal"
            activate
            do script "{command}"
        end tell
        '''
        subprocess.Popen(["osascript", "-e", apple_script])

    elif system == "Linux":
        subprocess.Popen([
            "gnome-terminal", "--", "python3", script_path
        ])

    else:
        print(f"[ERROR] Unsupported OS: {system}")

class LFDHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        data = json.loads(body)
        path = self.path

        if path == "/recover":
            server_id_req = data.get("server_id")
            log(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] LFD: Recovery requested for {server_id_req}")
            recover_server_locally(server_id_req)
            self.send_response(200)
            self.end_headers()
            log(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] LFD: Recovery action executed for {server_id_req}")
            return


def run_server():
    global host, port
    server = HTTPServer((host, 9000), LFDHandler)
    server.serve_forever()

def input_thread():
    while True:
        cmd = input().strip()

        with delay_lock:
            if cmd == "slow":
                delay_config["lfd_delay"] = 2
                delay_config["server_delay"] = 2
                print(">> Delays set to 2 seconds")

            elif cmd == "burn":
                delay_config["lfd_delay"] = 1000
                delay_config["server_delay"] = 1000
                start_cpu_burn()

            elif cmd == "normal":
                delay_config["lfd_delay"] = 0
                delay_config["server_delay"] = 0
                stop_cpu_burn()
                print(">> All delays cleared and CPU burn stopped")

            else:
                print("Commands: slow | burn | normal")

# -------------------- Main --------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LFD Heartbeat Client with GFD reporting")
    parser.add_argument("--lfd_id", default="LFD1", help="LFD Id")
    parser.add_argument("--server_id", default="S1", help="Server Id")
    parser.add_argument("--host", default="0.0.0.0", help="Local server host")
    parser.add_argument("--port", type=int, default=8081, help="Local lfd port")
    parser.add_argument("--server_port", type=int, default=8080, help="Local server port")
    parser.add_argument("--gfd_host", default="0.0.0.0", help="GFD host")
    parser.add_argument("--gfd_port", type=int, default=6000, help="GFD port")
    parser.add_argument("--freq", type=float, default=5.0, help="Heartbeat frequency in seconds")
    parser.add_argument("--timeout", type=float, default=10.0, help="Heartbeat timeout in seconds")
    args = parser.parse_args()

    # -------------------- Set Global Variables --------------------
    lfd_id = args.lfd_id
    server_id = args.server_id
    host = args.host
    port = args.port
    server_port = args.server_port
    gfd_host = args.gfd_host
    gfd_port = args.gfd_port
    heartbeat_freq = args.freq
    timeout = args.timeout

    start_time_filename  = time.strftime("%Y%m%d_%H:%M:%S")
    log_file = os.path.join(os.path.dirname(__file__), "..",'..', "logs", f"lfd_{lfd_id}_log_{start_time_filename.replace(':','_')}.txt")

    log(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Starting {lfd_id} to http://{host}:{port} with heartbeat_freq={heartbeat_freq} and reporting to GFD http://{gfd_host}:{gfd_port}")

    # 启动 heartbeat 线程
    threading.Thread(target=lfd1, daemon=True).start()
    threading.Thread(target=run_server, daemon=True).start()

    # 启动 HTTP 服务器处理 /recover
    # server = HTTPServer((host, port), LFDHandler)
    # try:
    #     server.serve_forever()
    # except KeyboardInterrupt:
    #     print(f"\n\033[91m[{time.strftime('%Y-%m-%d %H:%M:%S')}] {lfd_id} terminated by user.\033[0m")
    try:
        input_thread()
    except KeyboardInterrupt:
        print(f"\n\033[91m[{time.strftime('%Y-%m-%d %H:%M:%S')}] {lfd_id} terminated by user.\033[0m")
