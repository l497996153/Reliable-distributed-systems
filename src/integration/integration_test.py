import subprocess
import time
import os
import sys
from pathlib import Path

# ---------- 路径设置 ----------
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.dirname(CURRENT_DIR)

def run_integration_test_m1():
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


def run_integration_test_m2():
    processes = []
    replicas = []
    lfds = []

    try:
        # ---------- 1️⃣ 启动 GFD ----------
        gfd_cmd = [
            sys.executable,
            os.path.join(SRC_DIR, "gfd", "gfd.py"),
            "--host", "127.0.0.1",
            "--port", "6000",
            "--timeout", "10"
        ]
        gfd_proc = subprocess.Popen(gfd_cmd)
        processes.append(gfd_proc)
        print("✅ GFD started on port 6000")
        time.sleep(2)

        # ---------- 2️⃣ 启动 3 个 Replica ----------
        replica_ports = [8080, 8081, 8082]
        for i, port in enumerate(replica_ports, 1):
            cmd = [
                sys.executable,
                os.path.join(SRC_DIR, "server", "server.py"),
                "--host", "127.0.0.1",
                "--port", str(port),
                "--replica-id", f"S{i}"
            ]
            try:
                proc = subprocess.Popen(cmd)
                replicas.append(proc)
                processes.append(proc)
                print(f"✅ Replica S{i} started on port {port}")
            except Exception as e:
                print(f"❌ Failed to start Replica S{i}: {e}")
        time.sleep(3)

        # ---------- 3️⃣ 启动 LFD ----------
        for i, port in enumerate(replica_ports, 1):
            cmd = [
                sys.executable,
                os.path.join(SRC_DIR, "lfd", "heartbeat_client.py"),
                "--lfd_id", f"LFD{i}",
                "--server_id", f"S{i}",
                "--host", "127.0.0.1",
                "--port", str(port),
                "--gfd_host", "127.0.0.1",
                "--gfd_port", "6000",
                "--freq", "2",
                "--timeout", "5"
            ]
            try:
                proc = subprocess.Popen(cmd)
                lfds.append(proc)
                processes.append(proc)
                print(f"✅ LFD{i} started for S{i}")
            except Exception as e:
                print(f"❌ Failed to start LFD{i}: {e}")
        time.sleep(5)

        # ---------- 4️⃣ 启动 Client (C1) ----------
        client_cmd = [
            sys.executable,
            os.path.join(SRC_DIR, "client", "client.py")
        ]
        client_input = (
            "C1\n"
            "127.0.0.1\n8080\n"
            "127.0.0.1\n8081\n"
            "127.0.0.1\n8082\n"
            "get\nincrease\nincrease\nget\ndecrease\nget\nclose\n"
        )

        client_proc = subprocess.Popen(
            client_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=SRC_DIR
        )
        out, err = client_proc.communicate(client_input, timeout=40)
        print("✅ Client finished interaction")
        print("----- Client Output -----")
        print(out)
        if err:
            print("----- Client Errors -----")
            print(err)

        # ---------- 5️⃣ 模拟 S2 故障 ----------
        print("💥 Killing Replica S2 to test fault detection ...")
        if len(replicas) > 1:
            replicas[1].terminate()
        time.sleep(5)

        # ---------- 6️⃣ 再次启动客户端 ----------
        print("🔁 Re-running client after S2 failure ...")
        client_input2 = (
            "C2\n"
            "127.0.0.1\n8080\n"
            "127.0.0.1\n8081\n"
            "127.0.0.1\n8082\n"
            "increase\nget\nclose\n"
        )
        client_proc2 = subprocess.Popen(
            client_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=SRC_DIR
        )
        out2, err2 = client_proc2.communicate(client_input2, timeout=40)
        print("----- Client Output After Failure -----")
        print(out2)
        if err2:
            print("----- Client Errors After Failure -----")
            print(err2)

    finally:
        # ---------- 清理 ----------
        print("\n🛑 Cleaning up processes ...")
        for p in processes:
            try:
                p.terminate()
            except Exception:
                pass
        print("✅ All processes terminated.")


if __name__ == "__main__":
    run_integration_test_m2()