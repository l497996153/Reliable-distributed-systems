import time
import json
from http.client import HTTPConnection

class CheckpointHandler:
    def __init__(self, last_time=None, freq=1.0, state_manager=None, path="/send_checkpoint"):
        self._last_time = time.time() - freq if last_time is None else float(last_time)
        self._freq = float(freq)
        self.state_manager = state_manager
        self._path = path
        self.connections = {}

    def _should_send(self, now_wall):
        # Check if at least freq seconds have elapsed since last send
        return (now_wall - self._last_time) >= self._freq

    def _ensure_connection(self, replica_id, host, port, timeout=2.0):
        # Create or reuse HTTPConnection for replica
        if replica_id not in self.connections:
            self.connections[replica_id] = HTTPConnection(host, port, timeout=timeout)
        return self.connections[replica_id]

    def send_request(self):
        now_wall = time.time()

        # Skip if not enough time has passed
        if not self._should_send(now_wall):
            return {}

        # Update last send timestamp
        self._last_time = now_wall

        results = {}
        primary_id = self.state_manager._primary
        wall_ts = time.strftime("%Y-%m-%d %H:%M:%S")
        self.state_manager._load_replica_file()

        for replica_id, replica_host, replica_port in self.state_manager._backup:
            try:
                conn = self._ensure_connection(replica_id, replica_host, replica_port)

                # Build checkpoint payload
                message_data = {
                    "primary_id": primary_id,
                    "replica_id": replica_id,
                    "timestamp": wall_ts,
                    "counter": self.state_manager.get(),
                }
                body = json.dumps(message_data)

                # Send HTTP POST request
                conn.request(
                    "POST",
                    self._path,
                    body=body,
                    headers={"Content-Type": "application/json"},
                )
                print(f"\033[94m[{wall_ts}] Sent checkpoint: <{primary_id} -> {replica_id}>\033[0m")

                # Read and parse response
                resp = conn.getresponse()
                raw = resp.read().decode("utf-8", errors="replace")
                try:
                    data = json.loads(raw)
                except json.JSONDecodeError:
                    data = {"ok": False, "error": "non-json response", "raw": raw}

                ok = (200 <= resp.status < 300) and bool(data.get("ok", True))
                results[replica_id] = ok
                if not ok:
                    print(f"\033[91m[{wall_ts}] {primary_id}: {replica_id} bad response {resp.status}, body={raw}\033[0m")

            except Exception as e:
                results[replica_id] = False
                print(f"\033[91m[{wall_ts}] {primary_id}: Failed to send checkpoint to {replica_id}: {e}\033[0m")

        return results
