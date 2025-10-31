# reliable-distributed-systems
Implementation of fault-tolerant distributed counter with active/passive replication, heartbeat failure detection, and automatic recovery. 

## Usage
### GFD
`python3 src/gfd/gfd.py`
- `--host`: GFD host (default 0.0.0.0)
- `--port`: GFD port (default 6000)
- `--timeout`: LFD heartbeat timeout in seconds (default 10.0)
- `--replica-file`: Path to replica file (default ../server/replica.json)

### LFD
`python3 src/lfd/heartbeat_client.py`
- `--host`: Local server host (default: 0.0.0.0)
- `--port`: Local server port (default: 8080)
- `--gfd_host`: GFD host (default: 0.0.0.0)
- `--gfd_port`: GFD port (default: 6000)
- `--freq`: Heartbeat frequency in seconds (default: 5.0)
- `--timeout`: Heartbeat timeout in seconds (default: 10.0)
- `--lfd_id`: LFD ID (default: LFD1)
- `--server_id`: Server ID

### Server
`python3 src/server/server.py`
- `--host`: Server Host (default: 0.0.0.0)
- `--port`: Server Port (default: 8080)
- `--replica-id`: Replica (default: S1)
- `--state-file`: Optional JSON file for persistence (default: None)
- `--replica-file`: Optional JSON file for replica checks (default: ./replica.json)
- `--checkpoint-freq`: Send periodic checkpoints (default: 5)

### Client
`python3 src/client/client.py`
- Stdin
