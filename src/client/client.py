from http.client import HTTPConnection
import json
import time
import os
import threading

class Client:
    def __init__(self, client_id, server_addresses):
        self.client_id = client_id
        self.server_addresses = server_addresses
        self.connections = {}
        self.request_num = 1
        self.start_time = time.strftime("%Y%m%d_%H:%M:%S")
        #self.log_file = f"../../logs/client_{self.client_id}_log_{self.start_time}.txt"
        self.log_file = os.path.join(os.path.dirname(__file__), "..",'..', "logs", f"client_{self.client_id}_log_{self.start_time.replace(':','_')}.txt")
        self.received_replies = {}  # {request_num: replica_id} check duplication
        self.success_count = 0
        self.get_counter = None
        self.reply_lock = threading.Lock()

        

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

        threads = []
        self.success_count = 0
        # send_request to all replica 
        for replica_id in self.connections.keys():
            thread = threading.Thread(
                target=self._send_to_replica,
                args=(replica_id, path, self.request_num, action)
            )
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()
        
        if self.success_count > 0:
            self.request_num += 1
            return True
        else:
            self.log("All replicas failed...")
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
            self.log(f"[{self._timestamp()}] Sent: <{self.client_id}, {replica_id}, {request_num}, {action}>")
            
            # Receive response
            response = self.connections[replica_id].getresponse() 
            data = response.read().decode()
            # Convert data from string to json
            data = json.loads(data) 
            self.log(f"[{self._timestamp()}] Received: <{self.client_id}, {replica_id}, {data['counter']}, reply>")
            
            with self.reply_lock:
                self.success_count += 1
                if request_num not in self.received_replies:
                    # first response record
                    self.received_replies[request_num] = replica_id
                else:
                    # duplicated response, mark it
                    self.log(f"[{self._timestamp()}] request_num {request_num}: Discard duplicate reply from {replica_id}")
        except Exception as e:
            self.log(f"[{self._timestamp()}] {self.client_id}: Failed to send request with {replica_id}: {e}")
            return False

    def get_counter_value(self):
        # Check connection
        if not self.connections:
            self.log(f"[{self._timestamp()}] {self.client_id}: No connections established")
            return False

        threads = []
        self.success_count = 0
        
        for replica_id in self.connections.keys():
            thread = threading.Thread(
                target=self._get_from_replica,
                args=(replica_id, self.request_num)
            )
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        if self.success_count > 0:
            self.request_num += 1
            return self.get_counter
        else:
            self.log("All replicas failed...")
            return False

    def _get_from_replica(self, replica_id, request_num):
        try:
            # Send GET request
            # self.connection.request("GET", f"/get")
            self.connections[replica_id].request("GET", f"/get?client_id={self.client_id}&request_num={request_num}")
            self.log(f"[{self._timestamp()}] Sent <{self.client_id}, {replica_id}, request id: {self.request_num}, get>")

            response = self.connections[replica_id].getresponse()
            if response.status == 200:
                data = response.read().decode()
                data = json.loads(data)
                # print(f"[{self._timestamp()}] {self.client_id}: Counter value received: {data}")
                # For the first milestone, hardcode this to S1.
                self.log(f"[{self._timestamp()}] Received: <{self.client_id}, {replica_id}, {data['counter']}, reply>")
                with self.reply_lock:
                    self.success_count += 1
                    if request_num not in self.received_replies:
                        # first response record
                        self.received_replies[request_num] = replica_id
                        self.get_counter = data
                    else:
                        # duplicated reocrd, mark it
                        self.log(f"[{self._timestamp()}] request_num {request_num}: Discard duplicate reply from {replica_id}")
            else:
                print(f"[{self._timestamp()}] {self.client_id}: Failed to get counter value from {replica_id}")
                return False
        except Exception as e:
            self.log(f"[{self._timestamp()}] {self.client_id}: Get request to {replica_id} failed: {e}")
            self.connections[replica_id] = HTTPConnection(self.server_addresses[replica_id])
            return False

    def _timestamp(self):
        return time.strftime("%Y-%m-%d %H:%M:%S")

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

        while True:

            action_input = input("Enter the action (get, increase, decrease, or close): ")
            reply = None

            if action_input == "get":
                reply = client.get_counter_value()
            elif (action_input == "increase" or action_input == "decrease"):
                reply = client.send_request(action_input)
            elif (action_input == "close"):
                break
            else:
                print("Invalid Input !")
    
    except (KeyboardInterrupt):
        print("\nClient Exit")
        
    finally:
        print("Client Disconnected.")