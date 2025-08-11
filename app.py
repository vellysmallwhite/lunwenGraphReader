import os
import sys
import time

def main() -> None:
    message = os.getenv("AGENT_MESSAGE", "agent-crawler placeholder running...")
    interval = float(os.getenv("LOG_INTERVAL_SEC", "5"))
    try:
        while True:
            print(message, flush=True)
            time.sleep(interval)
    except KeyboardInterrupt:
        print("Shutting down.", flush=True)
        sys.exit(0)

if __name__ == "__main__":
    main()

