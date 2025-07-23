import threading
import time
from processor.stream_manager import StreamManager

if __name__ == "__main__":
    stream_manager = StreamManager("config/config.json")
    stream_thread = threading.Thread(target=stream_manager.start)
    stream_thread.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("[STREAM MANAGER] Shutting down...")
        stream_manager.stop()
        stream_thread.join()
        print("[STREAM MANAGER] Fully exited.")
