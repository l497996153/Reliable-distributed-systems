import argparse
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import time
import os

# 全局状态表：lfd_id -> {server_id, status, last_update}
lfd_status_table = {}
TIMEOUT = 10  # 超过10秒未更新视为failed

# 日志文件
start_time_filename = time.strftime("%Y%m%d_%H:%M:%S")
log_file = os.path.join(os.path.dirname(__file__), "..",'..', "logs", f"gfd_log_{start_time_filename.replace(':','_')}.txt")

def log(text):
    """统一打印并写入日志文件"""
    print(text)
    with open(log_file, "a") as f:
        f.write(text + "\n")

def _timestamp():
    return time.strftime("%Y-%m-%d %H:%M:%S")

def check_timeouts():
    """检查LFD是否超时未汇报"""
    now = time.time()
    for lfd_id, info in lfd_status_table.items():
        last_update = info["last_update"]
        if info["status"] != "failed" and (now - last_update > TIMEOUT):
            info["status"] = "failed"
            log(f"[{_timestamp()}] Timeout: LFD={lfd_id} (server={info['server_id']}) marked as FAILED")

# =================== HTTP 请求处理器 ===================
class GFDHandler(BaseHTTPRequestHandler):
    def _set_headers(self, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()

    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length)
        try:
            data = json.loads(body)
        except Exception:
            self._set_headers(400)
            self.wfile.write(json.dumps({"error": "invalid json"}).encode())
            return

        # 注册
        if self.path == "/register":
            lfd_id = data.get("lfd_id")
            server_id = data.get("server_id")
            timestamp = _timestamp()

            lfd_status_table[lfd_id] = {
                "server_id": server_id,
                "status": "registered",
                "last_update": time.time()
            }
            log(f"[{timestamp}] Registered LFD={lfd_id} (server={server_id})")
            self._set_headers(200)
            self.wfile.write(json.dumps({"msg": "registered"}).encode())

        # 状态汇报
        elif self.path == "/status":
            lfd_id = data.get("lfd_id")
            server_id = data.get("server_id")
            status = data.get("status")
            timestamp = _timestamp()

            prev_status = lfd_status_table.get(lfd_id, {}).get("status")
            lfd_status_table[lfd_id] = {
                "server_id": server_id,
                "status": status,
                "last_update": time.time()
            }
            if prev_status != status:
                log(f"[{timestamp}] Status change: LFD={lfd_id} -> {status}")

            self._set_headers(200)
            self.wfile.write(json.dumps({"msg": "status received"}).encode())

        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "unknown path"}).encode())

    def log_message(self, format, *args):
        """屏蔽默认HTTP日志"""
        return

# =================== 主入口 ===================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GFD Server for LFDs")
    parser.add_argument("--host", default="0.0.0.0", help="GFD host (default 0.0.0.0)")
    parser.add_argument("--port", type=int, default=6000, help="GFD port (default 6000)")
    parser.add_argument("--timeout", type=float, default=10.0, help="LFD heartbeat timeout in seconds")
    args = parser.parse_args()

    TIMEOUT = args.timeout
    log(f"[{_timestamp()}] Starting GFD at {args.host}:{args.port} with timeout={TIMEOUT}s")

    server = HTTPServer((args.host, args.port), GFDHandler)

    server.timeout = 1  # 每1秒处理一次请求或超时
    while True:
        check_timeouts()
        try:
            server.handle_request()
        except KeyboardInterrupt:
            log(f"\n[{_timestamp()}] GFD shutting down...")
            server.server_close()
            break

