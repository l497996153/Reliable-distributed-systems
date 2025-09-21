import subprocess
import sys
import os
import json


try:
    with open(os.path.join(os.path.dirname(__file__), "command_param.json"), "r") as file:
        config = json.load(file)

except:
    print("Json File Not Found !")

HOST = config["lfd_host"]
PORT = config["lfd_port"]
freq = config["lfd_freq"]
timeout = config["lfd_timeout"]

file_path = os.path.join(os.path.dirname(__file__), "..", "src", "lfd", "heartbeat_client.py")

try:

    subprocess.run([sys.executable, file_path, "--host", HOST, "--port", str(PORT), "--freq", str(freq), "--timeout", str(timeout)])

except KeyboardInterrupt:

    print("LFD Process End.")
