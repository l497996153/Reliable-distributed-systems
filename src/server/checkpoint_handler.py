import json
from os import path
import time

class CheckpointHandler:
    def __init__(self, last_time, freq, state_manager):
        self._last_time = last_time
        self._freq = freq
        self.state_manager = state_manager
        self.connections = {}

    def send_request(self, curr_time):
        if self._last_time + self._freq >= curr_time:
            return
        
        primary_id = self.state_manager._primary
        for replica_id in self.state_manager._backup:
            # Construct the message payload
            message_data = {
                "primary_id": primary_id,
                'replica_id': replica_id,
                'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
            }
            message_json = json.dumps(message_data)

            try:
                # Send POST request
                self.connections[replica_id].request("POST", path, body=message_json, 
                                                    headers={"Content-Type": "application/json"})
                print(f"\033[94m[{time.strftime('%Y-%m-%d %H:%M:%S')}] Sent: <{primary_id} sent checkpoint to {replica_id}>\033[0m")
                
                # Receive response
                response = self.connections[replica_id].getresponse() 
                data = response.read().decode()
                # Convert data from string to json
                data = json.loads(data) 
                    
                # Send checkpoint requests to backups
                self._last_time = curr_time
                return True
            
            except Exception as e:
                print(f"\033[91m[{time.strftime('%Y-%m-%d %H:%M:%S')}] {primary_id}: Failed to send request with {replica_id}: {e}\033[0m")
                # Send checkpoint requests to backups
                self._last_time = curr_time
                return False

        