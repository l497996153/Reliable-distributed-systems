import subprocess
import sys
import os



file_path = os.path.join(os.path.dirname(__file__), "..", "src", "client", "client.py")

try:

    subprocess.run([sys.executable, file_path])

except KeyboardInterrupt:

    print("Client Process End.")