#!/usr/bin/env bash

OUT_FILE="cpu_usage.csv"
INTERVAL=10

echo "timestamp,cpu_user_percent,cpu_sys_percent,cpu_idle_percent" > "$OUT_FILE"

while true; do
    line=$(top -l 1 -n 0 | grep "CPU usage")

    user=$(echo "$line" | awk -F'[:,% ]+' '{print $3}')
    sys=$(echo "$line"  | awk -F'[:,% ]+' '{print $6}')
    idle=$(echo "$line" | awk -F'[:,% ]+' '{print $9}')

    timestamp=$(date +"%Y-%m-%d %H:%M:%S")
    echo "$timestamp,$user,$sys,$idle" >> "$OUT_FILE"

    sleep "$INTERVAL"
done