import subprocess
import sys
import os



# Server Parameter
HOST = "0.0.0.0"
PORT = 8080
replica_id = 'S1'
state_file = ''

# Client Parameter
# (1) Launch the server replica, S1.

file_path = os.path.join(os.path.dirname(__file__), "..", "src", "server", "server.py")

try:
    subprocess.run([sys.executable, file_path, "--host", HOST, "--port", str(PORT), "--replica-id", replica_id, "--state-file", state_file])

except KeyboardInterrupt:

    print("Server Process End.")


