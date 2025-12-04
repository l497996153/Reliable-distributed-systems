import os
import pandas as pd
import matplotlib.pyplot as plt

BASE_DIR = os.path.dirname(__file__)
cpu_csv = os.path.join(BASE_DIR, "cpu_usage.csv")
disk_csv = os.path.join(BASE_DIR, "disk_usage.csv")
mem_csv = os.path.join(BASE_DIR, "mem_usage.csv")

def plot_cpu_usage():
    df = pd.read_csv(cpu_csv)
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    df['cpu_user_percent'] = pd.to_numeric(df['cpu_user_percent'], errors='coerce')
    plt.figure(figsize=(8, 4))
    plt.plot(df['timestamp'], df['cpu_user_percent'], label='CPU user %', color='tab:blue', marker='o')
    plt.title("CPU Usage (User %) Over Time")
    plt.xlabel("Time")
    plt.ylabel("User CPU %")
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.legend()
    out_path = os.path.join(BASE_DIR, "cpu_usage.png")
    plt.tight_layout()
    plt.savefig(out_path)
    print(f"Saved {out_path}")

def plot_disk_usage():
    df = pd.read_csv(disk_csv)
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    df = df.dropna(subset=['timestamp']).sort_values('timestamp')
    for col in ['total', 'used', 'available']:
        df[col] = pd.to_numeric(df[col].str.extract(r'([\d\.]+)', expand=False), errors='coerce')
    df['percent'] = pd.to_numeric(df['percent'].str.replace('%', '', regex=False), errors='coerce')

    fig, ax1 = plt.subplots(figsize=(8, 4))
    ax1.plot(df['timestamp'], df['used'], label='Used', color='tab:red', marker='o')
    ax1.plot(df['timestamp'], df['available'], label='Available', color='tab:green', marker='o')
    ax1.set_xlabel("Time")
    ax1.set_ylabel("GB")
    ax1.grid(True, linestyle='--', alpha=0.5)
    ax1.legend(loc='upper left')

    ax2 = ax1.twinx()
    ax2.plot(df['timestamp'], df['percent'], label='Used %', color='tab:purple', linestyle='--')
    ax2.set_ylabel("Used %")
    ax2.legend(loc='upper right')

    plt.title("Disk Usage Over Time")
    out_path = os.path.join(BASE_DIR, "disk_usage.png")
    plt.tight_layout()
    plt.savefig(out_path)
    print(f"Saved {out_path}")

def plot_mem_usage():
    df = pd.read_csv(mem_csv)
    df['time_sec'] = pd.to_numeric(df['time_sec'], errors='coerce')
    df['used_mb'] = pd.to_numeric(df['used_mb'], errors='coerce')
    df['free_mb'] = pd.to_numeric(df['free_mb'], errors='coerce')

    plt.figure(figsize=(8, 4))
    plt.plot(df['time_sec'], df['used_mb'], label='Used (MB)', color='tab:orange', marker='o')
    plt.plot(df['time_sec'], df['free_mb'], label='Free (MB)', color='tab:green', marker='o')
    plt.title("Memory Usage Over Time")
    plt.xlabel("Time (sec)")
    plt.ylabel("MB")
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.legend()
    out_path = os.path.join(BASE_DIR, "mem_usage.png")
    plt.tight_layout()
    plt.savefig(out_path)
    print(f"Saved {out_path}")

def main():
    plot_cpu_usage()
    plot_disk_usage()
    plot_mem_usage()
    plt.show()

if __name__ == "__main__":
    main()
