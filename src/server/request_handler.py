from http.server import BaseHTTPRequestHandler
import json
import time

# The server injects a StateManager instance via a class attribute.
class CounterRequestHandler(BaseHTTPRequestHandler):
    state_manager = None
    replica_id = "S1"

    def log_message(self, fmt, *args):
        # Prepend timestamp as suggested in the guide
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"\033[1;96m[{ts}] {self.address_string()} - {fmt % args}\033[0m")

    def _send_json(self, code: int, payload: dict):
        data = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    # Handle GET
    def do_GET(self):
        if self.path == "/get":
            value = self.state_manager.get()
            self.log_message('Sending <reply> for /get with counter=%d', value)
            self._send_json(200, {"counter": value, "replica_id": self.replica_id})
        elif self.path == "/heartbeat":
            self._send_json(200, {"ok": True, "replica_id": self.replica_id})
        else:
            self._send_json(404, {"error": "not found"})

    # Handle POST
    def do_POST(self):
        if self.path == "/increase":
            value = self.state_manager.increase()
            self.log_message('Sending <reply> for /increase with counter=%d', value)
            self._send_json(200, {"counter": value, "replica_id": self.replica_id})
        elif self.path == "/decrease":
            value = self.state_manager.decrease()
            self.log_message('Sending <reply> for /decrease with counter=%d', value)
            self._send_json(200, {"counter": value, "replica_id": self.replica_id})
        else:
            self._send_json(404, {"error": "not found"})
