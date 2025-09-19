import subprocess
import sys
import os

# Server Parameter
HOST = "0.0.0.0"
PORT = 8080
freq = 8
timeout = 12

# Client Parameter
# (1) Launch the server replica, S1.

file_path = os.path.join(os.path.dirname(__file__), "..", "src", "lfd", "heartbeat_client.py")

try:

    subprocess.run([sys.executable, file_path, "--host", HOST, "--port", str(PORT), "--freq", str(freq), "--timeout", str(timeout)])

except KeyboardInterrupt:

    print("LFD Process End.")
