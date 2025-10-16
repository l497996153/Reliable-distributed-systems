import subprocess
import sys
import os
import json



try:
    with open(os.path.join(os.path.dirname(__file__), "command_param.json"), "r") as file:
        config = json.load(file)

except:
    print("Json File Not Found !")

HOST = config["server_host_2"]
PORT = config["server_port_2"]
replica_id = config["server_replica_id_2"]
state_file = config["server_state_file_2"]

file_path = os.path.join(os.path.dirname(__file__), "..", "src", "server", "server.py")

try:
    subprocess.run([sys.executable, file_path, "--host", HOST, "--port", str(PORT), "--replica-id", replica_id, "--state-file", state_file])

except KeyboardInterrupt:

    print("Server Process End.")


