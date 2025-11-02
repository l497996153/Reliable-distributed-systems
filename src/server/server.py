import argparse
from http.server import HTTPServer
from request_handler import CounterRequestHandler, Role
from state_manager import StateManager
from checkpoint_handler import CheckpointHandler
import time
import json

class SingleThreadedHTTPServer(HTTPServer):
    allow_reuse_address = True

def clear_json(f):
    with open(f, "w", encoding="utf-8") as f:
        json.dump({}, f)

def main():
    # Parse args
    parser = argparse.ArgumentParser(description="Counter Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8080, help="Port (default: 8080)")
    parser.add_argument("--replica-id", default="S1", help="Replica (default: S1)")
    parser.add_argument("--state-file", default=None, help="Optional JSON file for persistence (default: None)")
    parser.add_argument("--replica-file", default="./replica.json", help="Optional JSON file for replica checks (default: ./replica.json)")
    parser.add_argument("--checkpoint-freq", type=int, default=5,
                        help="Send periodic checkpoints (default: 5)")
    args = parser.parse_args()

    state = StateManager(state_file=args.state_file, replica_file=args.replica_file, replica_id=args.replica_id, replica_host=args.host, replica_port=args.port)
    checkpoint_handler = CheckpointHandler(time.time(), args.checkpoint_freq, state)

    # Setup role for current replica
    role = state.setPrimary()

    CounterRequestHandler.state_manager = state
    CounterRequestHandler.replica_id = args.replica_id
    CounterRequestHandler.role = role

    # Start listening
    server = SingleThreadedHTTPServer((args.host, args.port), CounterRequestHandler)
    server.timeout = 0.1
    print(f"\033[94m[{time.strftime('%Y-%m-%d %H:%M:%S')}] Listening on http://{args.host}:{args.port} as {args.replica_id}\033[0m")
    print(f"\033[94m[{time.strftime('%Y-%m-%d %H:%M:%S')}] Endpoints: POST /increase, POST /decrease, GET /get, GET /heartbeat\033[0m")

    if role == Role.BACKUP:
        print(f"\033[94m[{time.strftime('%Y-%m-%d %H:%M:%S')}] This replica now is a backup server \033[0m")
    else:
        print(f"\033[94m[{time.strftime('%Y-%m-%d %H:%M:%S')}] This replica now is a primary server \033[0m")

    try:
        # Writeup said that the checkpoint_count is 1 at first.
        while True: 
            # Send checkpoint request to other backups
            if role == Role.PRIMARY:
                checkpoint_handler.send_request()
                # Writeup said that the checkpoint_count will be increased after sending the checkpoint request.
            server.handle_request()
    except KeyboardInterrupt:
        # clear_json(args.replica_file)
        print(f"\n\033[91m[{time.strftime('%Y-%m-%d %H:%M:%S')}] server has died...\033[0m")
    finally:
        # clear_json(args.replica_file)
        server.server_close()

if __name__ == "__main__":
    main()
