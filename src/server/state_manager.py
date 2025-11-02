import json
import os
import threading
import time
from typing import Optional
from request_handler import Role

# Maintain the counter value in json
class StateManager:
    def __init__(self, state_file: Optional[str] = None, replica_id: str = "S1", replica_host: str = "0.0.0.0", replica_port: int = 8080):
        self._lock = threading.Lock()
        self._value = 0
        self._primary = []
        self._backup = []
        self._state_file = state_file
        self._replica_id = replica_id
        self._replica_host = replica_host
        self._replica_port = replica_port

        if self._state_file and os.path.exists(self._state_file):
            self._load_state_file()

    def _timestamp(self) -> str:
        return time.strftime("%Y-%m-%d %H:%M:%S")

    def _persist_state_file(self):
        if not self._state_file:
            return
        tmp = f"{self._state_file}.tmp"
        data = {"counter": self._value, "replica_id": self._replica_id}
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, self._state_file)

    def _load_state_file(self):
        try:
            with open(self._state_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                self._value = int(data.get("counter", 0))
        except Exception:
            self._value = 0

    def _load_replica_file(self):
        try:
            with open(self._replica_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                self._primary = data.get("primary", [])
                self._backup = data.get("backup", [])
        except Exception:
            self._primary = []

    def get(self) -> int:
        with self._lock:
            return self._value

    def increase(self) -> int:
        with self._lock:
            before = self._value
            # print(f"\033[96m[{self._timestamp()}] state_{self._replica_id} = {before} before processing <request: increase>\033[0m")
            self._value += 1
            after = self._value
            # print(f"\033[96m[{self._timestamp()}] state_{self._replica_id} = {after} after processing <request: increase>\033[0m")
            self._persist_state_file()
            return self._value

    def decrease(self) -> int:
        with self._lock:
            before = self._value
            # print(f"\033[96m[{self._timestamp()}] state_{self._replica_id} = {before} before processing <request: decrease>\033[0m")
            self._value -= 1
            after = self._value
            # print(f"\033[96m[{self._timestamp()}] state_{self._replica_id} = {after} after processing <request: decrease>\033[0m")
            self._persist_state_file()
            return self._value
        

    def set(self, v: int) -> int:
        # Set the counter to an exact value (used for passive checkpointing)
        with self._lock:
            self._value = int(v)
            self._persist_state_file()
            return self._value