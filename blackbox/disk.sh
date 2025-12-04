#!/bin/bash

OUTPUT_FILE="disk_usage.csv"

if [ ! -f "$OUTPUT_FILE" ]; then
    echo "timestamp,total,used,available,percent" > "$OUTPUT_FILE"
fi

while true; do
    usage=$(df -h / | awk 'NR==2 {print $2","$3","$4","$5}')

    timestamp=$(date +"%Y-%m-%d %H:%M:%S")

    echo "$timestamp,$usage" >> "$OUTPUT_FILE"

    # Wait 10 seconds
    sleep 10
done