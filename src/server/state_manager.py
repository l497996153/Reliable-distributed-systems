import json
import os
import threading
import time
from typing import Optional

# Maintain the counter value in json
class StateManager:
    def __init__(self, state_file: Optional[str] = None, replica_id: str = "S1"):
        self._lock = threading.Lock()
        self._value = 0
        self._state_file = state_file
        self._replica_id = replica_id
        if self._state_file and os.path.exists(self._state_file):
            self._load()

    def _timestamp(self) -> str:
        return time.strftime("%Y-%m-%d %H:%M:%S")

    def _persist(self):
        if not self._state_file:
            return
        tmp = f"{self._state_file}.tmp"
        data = {"counter": self._value, "replica_id": self._replica_id}
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, self._state_file)

    def _load(self):
        try:
            with open(self._state_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                self._value = int(data.get("counter", 0))
        except Exception:
            self._value = 0

    def get(self) -> int:
        with self._lock:
            return self._value

    def increase(self) -> int:
        with self._lock:
            before = self._value
            print(f"[{self._timestamp()}] my_state_{self._replica_id} = {before} before processing <request: increase>")
            self._value += 1
            after = self._value
            print(f"[{self._timestamp()}] my_state_{self._replica_id} = {after} after processing <request: increase>")
            self._persist()
            return self._value

    def decrease(self) -> int:
        with self._lock:
            before = self._value
            print(f"[{self._timestamp()}] my_state_{self._replica_id} = {before} before processing <request: decrease>")
            self._value -= 1
            after = self._value
            print(f"[{self._timestamp()}] my_state_{self._replica_id} = {after} after processing <request: decrease>")
            self._persist()
            return self._value
