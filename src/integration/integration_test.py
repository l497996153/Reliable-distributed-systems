import subprocess
import time
import os

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__)) 
SRC_DIR = os.path.dirname(CURRENT_DIR)                     

def run_integration_test():
    processes = []

    try:
        server_cmd = ["python", os.path.join(SRC_DIR, "server", "server.py"), "--port", "5000"]
        server_proc = subprocess.Popen(server_cmd)
        processes.append(server_proc)
        print("✅ Server started on port 5000")
        time.sleep(5)

        lfd_cmd = ["python", os.path.join(SRC_DIR, "lfd", "heartbeat_client.py"),
                   "--host", "localhost", "--port", "5000", "--freq", "2", "--timeout", "5"]
        lfd_proc = subprocess.Popen(lfd_cmd)
        processes.append(lfd_proc)
        print("✅ LFD started")
        time.sleep(2)

        client_cmd = ["python", os.path.join(SRC_DIR, "client", "client.py")]
        client_input = "C1\nlocalhost\n5000\nget\nincrease\nincrease\nget\nclose\n"
        client_proc = subprocess.Popen(client_cmd, stdin=subprocess.PIPE,
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                       text=True, cwd=SRC_DIR)
        out, err = client_proc.communicate(client_input, timeout=30)
        print("✅ Client finished interaction")
        print("----- Client Output -----")
        print(out)
        if err:
            print("----- Client Errors -----")
            print(err)

        print("💥 Killing Server...")
        server_proc.terminate()
        time.sleep(6) 

    finally:
        print("🛑 Cleaning up processes...")
        for p in processes:
            try:
                p.terminate()
            except Exception:
                pass


if __name__ == "__main__":
    run_integration_test()
