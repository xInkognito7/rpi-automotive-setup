#!/usr/bin/python3
import subprocess
import time
import os

LOG_FILE = "/home/pi/scripts/mfsw_candump.log"
FILTER_IDS = ["5C3", "5C5", "5BF", "661"]

def main():
    # Kurze Wartezeit, bis can0 bereit ist
    time.sleep(3)
    
    cmd = ["candump", "can0"]
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, bufsize=1)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"\n--- LOG SESSION START: {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n")
            f.flush()
            os.fsync(f.fileno())
            
            for line in proc.stdout:
                if any(cid in line for cid in FILTER_IDS):
                    f.write(line)
                    f.flush()
                    os.fsync(f.fileno())
    except Exception as e:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"Error: {e}\n")
            f.flush()
            os.fsync(f.fileno())

if __name__ == "__main__":
    main()
