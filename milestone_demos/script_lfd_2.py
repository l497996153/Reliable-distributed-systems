import subprocess
import sys
import os
import json


try:
    with open(os.path.join(os.path.dirname(__file__), "command_param.json"), "r") as file:
        config = json.load(file)

except:
    print("Json File Not Found !")

id = config['id_LFD_2']
lfd_id = config['lfd_id_2']
server_id= config['server_id_2']
HOST = config["lfd_server_host_2"]
PORT = config["lfd_server_port_2"]
GFD_HOST = config["lfd_gfd_host_2"]
GFD_PORT = config["lfd_gfd_port_2"]
freq = config["lfd_freq_2"]
timeout = config["lfd_timeout_2"]

file_path = os.path.join(os.path.dirname(__file__), "..", "src", "lfd", "heartbeat_client.py")

try:

    subprocess.run([sys.executable, file_path, "--lfd_id", lfd_id, "--server_id", server_id, "--host", HOST, "--port", str(PORT), "--gfd_host", str(GFD_HOST), "--gfd_port",  str(GFD_PORT),"--freq", str(freq), "--timeout", str(timeout)])

except KeyboardInterrupt:

    print("LFD Process End.")
