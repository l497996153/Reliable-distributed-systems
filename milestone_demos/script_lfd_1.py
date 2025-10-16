import subprocess
import sys
import os
import json


try:
    with open(os.path.join(os.path.dirname(__file__), "command_param.json"), "r") as file:
        config = json.load(file)

except:
    print("Json File Not Found !")

id = config['id_LFD_1']
HOST = config["lfd_server_host_1"]
PORT = config["lfd_server_port_1"]
GFD_HOST = config["lfd_gfd_host_1"]
GFD_PORT = config["lfd_gfd_port_1"]
freq = config["lfd_freq_1"]
timeout = config["lfd_timeout_1"]

file_path = os.path.join(os.path.dirname(__file__), "..", "src", "lfd", "heartbeat_client.py")

try:

    subprocess.run([sys.executable, file_path, "--host", HOST, "--port", str(PORT), "--gfd_host", str(GFD_HOST), "--gfd_port",  str(GFD_PORT),"--freq", str(freq), "--timeout", str(timeout)])

except KeyboardInterrupt:

    print("LFD Process End.")
