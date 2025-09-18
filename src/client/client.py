from http.client import HTTPConnection
import json
import time

class Client:
    def __init__(self, client_id, server_address):
        self.client_id = client_id
        self.server_address = server_address
        self.connection = None
        self.request_num = 1

    def connect_to_server(self):
        self.connection = HTTPConnection(self.server_address)
        try:
            self.connection = HTTPConnection(self.server_address)
            print(f"[{self._timestamp()}] {self.client_id}: Connected to server {self.server_address}")
        except Exception as e:
            print(f"[{self._timestamp()}] {self.client_id}: Connection failed: {e}")

    def send_request(self, action):
        # Check connection
        if not self.connection:
            print(f"[{self._timestamp()}] {self.client_id}: No connection established")
            return False

        # Determine the path based on action
        if action == "increase":
            path = "/increase"
        elif action == "decrease":
            path = "/decrease"
        else:
            print(f"[{self._timestamp()}] {self.client_id}: Invalid action for send_request: {action}")
            return False

        # Construct the message payload
        message_data = {
            'client_id': self.client_id,
            'replica_id': 'S1',  # currently only server S1
            'request_num': self.request_num,
            'timestamp': time.time()
        }
        message_json = json.dumps(message_data)

        try:
            # Send POST request
            self.connection.request("POST", path, body=message_json, headers={"Content-Type": "application/json"})
            response = self.connection.getresponse() 
            data = response.read().decode() 
            print(f"[{self._timestamp()}] {self.client_id}: Sent {action} request #{self.request_num} to {self.server_address}")
            print(f"Server reply: {data}")
            self.request_num += 1 
            return True
        except Exception as e:
            print(f"[{self._timestamp()}] {self.client_id}: Failed to send request: {e}")
            return False

    def get_counter_value(self):
        # Check connection
        if not self.connection:
            print(f"[{self._timestamp()}] {self.client_id}: No connection established")
            return False
        try:
            # Send GET request
            self.connection.request("GET", "/get")
            print(f"[{self._timestamp()}] Sent <{self.client_id}, S1, {self.request_num}, request>")

            response = self.connection.getresponse()
            self.request_num += 1
            if response.status == 200:
                data = response.read().decode()
                print(f"[{self._timestamp()}] {self.client_id}: Counter value received: {data}")
                return data
            else:
                print(f"[{self._timestamp()}] {self.client_id}: Failed to get counter value")
                return False
        except Exception as e:
            print(f"[{self._timestamp()}] {self.client_id}: Get request failed: {e}")
            self.connection = HTTPConnection(self.server_address)
            return False

    def _timestamp(self):
        return time.strftime("%H:%M:%S")

# Example usage
if __name__ == "__main__":
    client = Client("C1", "localhost:8080")
    client.connect_to_server()
    print("\n=== Starting client requests ===")

    actions = ["increase", "increase", "get", "decrease", "get"]
    for action in actions:
        print(f"\n--- Sending {action} request ---")
        reply = None
        if action == "get":
            reply = client.get_counter_value()
        else:
            reply = client.send_request(action)
        if reply:
            print(f"Server reply: {reply}")
        time.sleep(3)