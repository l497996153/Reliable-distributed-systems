from http.client import HTTPConnection
import json
import time
import os
import random
import sys
import select
import termios
import tty

class Client:
    def __init__(self, client_id, server_addresses):
        self.client_id = client_id
        self.server_addresses = server_addresses
        self.connections = {}
        self.request_num = 1
        self.start_time = time.strftime("%Y%m%d_%H:%M:%S")
        #self.log_file = f"../../logs/client_{self.client_id}_log_{self.start_time}.txt"
        self.log_file = os.path.join(os.path.dirname(__file__), "..",'..', "logs", f"client_{self.client_id}_log_{self.start_time.replace(':','_')}.txt")
        self.success_count = 0
        self.get_counter = None
        self.primary = None

        

    def log(self, text):
        print(text)
        """Print and write log to log file."""
        with open(self.log_file, "a") as f:
            f.write(text + "\n")

    def connect_to_servers(self):
        for replica_id, address in self.server_addresses.items():
            try:
                self.connections[replica_id] = HTTPConnection(address)
                self.log(f"[{self._timestamp()}] {self.client_id}: Connected to server {replica_id} at {address}")
            except Exception as e:
                self.log(f"[{self._timestamp()}] {self.client_id}: Connection to {replica_id} failed: {e}")

        connected = "S1"
        '''for replica_id in list(self.connections.keys()):
            try:
                conn = self.connections[replica_id]
                conn.request("GET", f"/get?client_id={self.client_id}&request_num={self.request_num}")
                resp = conn.getresponse()
                raw = resp.read().decode()
                if resp.status == 200 and raw:
                    try:
                        data = json.loads(raw)
                        if data.get("primary") is True:
                            connected = replica_id
                            self.log(f"[{self._timestamp()}] {self.client_id}: Primary discovered by probe: {discovered}")
                            break
                    except Exception:
                        pass
            except Exception:
                pass
        '''
        # Default to S1
        if connected in self.connections:
            self.primary = connected
            self.log(f"[{self._timestamp()}] {self.client_id}: Primary is {self.primary}")
        else:
            self.log(f"[{self._timestamp()}] {self.client_id}: No primary server connections available")

    def send_request(self, action):
        # Check connections
        if not self.connections:
            self.log(f"[{self._timestamp()}] {self.client_id}: No connections established")
            return False

        # Determine the path based on action
        if action == "increase":
            path = "/increase"
        elif action == "decrease":
            path = "/decrease"
        else:
            self.log(f"[{self._timestamp()}] {self.client_id}: Invalid action for send_request: {action}")
            return False

        # Ensure we have a primary known; if not, try to probe again
        if not self.primary:
            self.connect_to_servers()
        if not self.primary:
            self.log(f"[{self._timestamp()}] {self.client_id}: Primary not found")
            return False

        # send request only to primary
        if self.primary not in self.connections:
            try:
                self.connections[self.primary] = HTTPConnection(self.server_addresses[self.primary])
            except Exception as e:
                self.log(f"[{self._timestamp()}] {self.client_id}: Cannot connect to primary {self.primary}: {e}")
                return False

        sent = self._send_to_replica(self.primary, path, self.request_num, action)
        if sent:
            self.request_num += 1
            return True
        else:
            # Try to reconnect primary once and retry
            self.log(f"[{self._timestamp()}] {self.client_id}: Primary {self.primary} failed; attempting reconnection")
            self.primary = None
            self.connect_to_servers()
            if self.primary and self.primary in self.connections:
                if self._send_to_replica(self.primary, path, self.request_num, action):
                    self.request_num += 1
                    return True
            self.log(f"[{self._timestamp()}] {self.client_id}: Request failed after reconnection")
            return False

    def _send_to_replica(self, replica_id, path, request_num, action):
        # Construct the message payload
        message_data = {
            'client_id': self.client_id,
            'replica_id': replica_id,
            'request_num': request_num,
            'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
        }
        message_json = json.dumps(message_data)

        try:
            # Send POST request
            self.connections[replica_id].request("POST", path, body=message_json,
                                                headers={"Content-Type": "application/json"})
            self.log(f"[{self._timestamp()}] Sent: <{self.client_id}, {replica_id}, request id: {request_num}, {action}>")

            # Receive response
            response = self.connections[replica_id].getresponse()
            raw = response.read().decode()
            if response.status == 200:
                try:
                    data = json.loads(raw) if raw else {}
                except Exception:
                    data = {}
                self.log(f"[{self._timestamp()}] Received: <{self.client_id}, {replica_id}, {data.get('counter')}, reply>")
                return True
            else:
                self.log(f"[{self._timestamp()}] {self.client_id}: Bad response from {replica_id}: {response.status} body={raw}")
                return False
        except Exception as e:
            self.log(f"[{self._timestamp()}] {self.client_id}: Failed to send request to {replica_id}: {e}")
            # attempt to recreate connection lazily
            try:
                self.connections[replica_id] = HTTPConnection(self.server_addresses[replica_id])
            except Exception:
                pass
            return False

    def get_counter_value(self):
        # Check connection
        if not self.connections:
            self.log(f"[{self._timestamp()}] {self.client_id}: No connections established")
            return False

        # Ensure primary known
        if not self.primary:
            self.connect_to_servers()
        if not self.primary:
            self.log(f"[{self._timestamp()}] {self.client_id}: Primary not known")
            return False

        # Request counter only from primary
        if self.primary not in self.connections:
            try:
                self.connections[self.primary] = HTTPConnection(self.server_addresses[self.primary])
            except Exception as e:
                self.log(f"[{self._timestamp()}] {self.client_id}: Cannot connect to primary {self.primary}: {e}")
                return False

        data = self._get_from_replica(self.primary, self.request_num)
        if data:
            self.request_num += 1
            self.get_counter = data
            return data
        else:
            # try connecting once
            self.primary = None
            self.connect_to_servers()
            if self.primary and self.primary in self.connections:
                data = self._get_from_replica(self.primary, self.request_num)
                if data:
                    self.request_num += 1
                    self.get_counter = data
                    return data
            self.log(f"[{self._timestamp()}] {self.client_id}: Failed to get counter from primary {self.primary}")
            return False

    def _get_from_replica(self, replica_id, request_num):
        try:
            # Send GET request
            # self.connection.request("GET", f"/get")
            self.connections[replica_id].request("GET", f"/get?client_id={self.client_id}&request_num={request_num}")
            self.log(f"[{self._timestamp()}] Sent <{self.client_id}, {replica_id}, request id: {self.request_num}, get>")
            response = self.connections[replica_id].getresponse()
            raw = response.read().decode()
            if response.status == 200:
                try:
                    data = json.loads(raw) if raw else {}
                except Exception:
                    data = {}
                self.log(f"[{self._timestamp()}] Received: <{self.client_id}, {replica_id}, {data.get('counter')}, reply>")
                return data
            else:
                self.log(f"[{self._timestamp()}] {self.client_id}: Failed to get counter value from {replica_id}: {response.status} body={raw}")
                return False
        except Exception as e:
            self.log(f"[{self._timestamp()}] {self.client_id}: Get request to {replica_id} failed: {e}")
            self.connections[replica_id] = HTTPConnection(self.server_addresses[replica_id])
            return False

    def _timestamp(self):
        return time.strftime("%Y-%m-%d %H:%M:%S")

class _RawInput:
    def __enter__(self):
        if sys.stdin.isatty():
            self._fd = sys.stdin.fileno()
            self._old = termios.tcgetattr(self._fd)
            tty.setcbreak(self._fd)
        else:
            self._fd = None
        return self
    def __exit__(self, exc_type, exc, tb):
        if self._fd is not None:
            termios.tcsetattr(self._fd, termios.TCSADRAIN, self._old)

def _esc_pressed(timeout=0.0):
    if not sys.stdin.isatty():
        return False
    r, _, _ = select.select([sys.stdin], [], [], timeout)
    if r:
        ch = sys.stdin.read(1)
        return ch == '\x1b'  # ESC
    return False

# Example usage
if __name__ == "__main__":

    client_id = input("Enter Client ID: ")
    print("\nEnter server addresses:")
    server_addresses = {}
    for replica_id in ['S1', 'S2', 'S3']:
        ip = input(f"  {replica_id} IP address: ").strip()
        port = input(f"  {replica_id} port: ").strip()
        server_addresses[replica_id] = f"{ip}:{port}"
    print("\nConnecting to servers...")
    client = Client(client_id, server_addresses)
    client.connect_to_servers()
    """
    actions = ["get", "increase", "increase", "get", "decrease", "get"]
    for action in actions:
        # print(f"\n--- Sending {action} request ---")
        reply = None
        if action == "get":
            reply = client.get_counter_value()
        else:
            reply = client.send_request(action)
        # if reply:
            # print(f"Server reply: {reply}")
        time.sleep(3)
    """
    try:
        with _RawInput():
            while True:
                if _esc_pressed(0):
                    print("Exiting loop.")
                    break
                action = random.choice(("get", "increase", "decrease"))  #random choose action input("Enter the action (get, increase, decrease, or close): ")
                reply = None
                if action == "get":
                    reply = client.get_counter_value()
                elif (action == "increase" or action == "decrease"):
                    reply = client.send_request(action)
                else:
                    print("Invalid Input !")
                time.sleep(10)
    
    except (KeyboardInterrupt):
        print("\nClient Exit")
        
    finally:
        print("Client Disconnected.")