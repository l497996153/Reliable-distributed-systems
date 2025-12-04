#!/bin/bash

# Output CSV header
echo "time_sec,used_mb,free_mb" > mem_usage.csv

# Record the starting time
start=$(date +%s)

while true; do
    # Current timestamp
    now=$(date +%s)
    elapsed=$(( now - start ))

    pages_free=$(vm_stat | awk '/Pages free/ {print $3}' | sed 's/\.//')
    pages_spec=$(vm_stat | awk '/Pages speculative/ {print $3}' | sed 's/\.//')
    pages_active=$(vm_stat | awk '/Pages active/ {print $3}' | sed 's/\.//')
    pages_inactive=$(vm_stat | awk '/Pages inactive/ {print $3}' | sed 's/\.//')
    pages_wired=$(vm_stat | awk '/Pages wired/ {print $4}' | sed 's/\.//')
    pages_comp=$(vm_stat | awk '/Pages occupied by compressor/ {print $5}' | sed 's/\.//')
    page_size=$(vm_stat | head -1 | awk '{print $8}')

    used_mb=$(( (pages_active + pages_wired + pages_comp) * page_size / 1024 / 1024 ))
    avail_mb=$(( (pages_free + pages_spec + pages_inactive) * page_size / 1024 / 1024 ))

    # Save to CSV
    echo "$elapsed,$used_mb,$avail_mb" >> mem_usage.csv

    # Wait 1 second
    sleep 10
done
