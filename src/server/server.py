import argparse
from http.server import HTTPServer
from request_handler import CounterRequestHandler
from state_manager import StateManager
import time

class SingleThreadedHTTPServer(HTTPServer):
    allow_reuse_address = True

def main():
    # Parse args
    parser = argparse.ArgumentParser(description="Counter Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8080, help="Port (default: 8080)")
    parser.add_argument("--replica-id", default="S1", help="Replica (default: S1)")
    parser.add_argument("--state-file", default=None, help="Optional JSON file for persistence")
    args = parser.parse_args()

    state = StateManager(state_file=args.state_file, replica_id=args.replica_id)

    CounterRequestHandler.state_manager = state
    CounterRequestHandler.replica_id = args.replica_id

    # Start listening
    server = SingleThreadedHTTPServer((args.host, args.port), CounterRequestHandler)
    print(f"\033[94m[{time.strftime('%Y-%m-%d %H:%M:%S')}] Listening on http://{args.host}:{args.port} as {args.replica_id}\033[0m")
    print(f"\033[94m[{time.strftime('%Y-%m-%d %H:%M:%S')}] Endpoints: POST /increase, POST /decrease, GET /get, GET /heartbeat\033[0m")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print(f"\n\033[91m[{time.strftime('%Y-%m-%d %H:%M:%S')}] server has died...\033[0m")
    finally:
        server.server_close()

if __name__ == "__main__":
    main()
