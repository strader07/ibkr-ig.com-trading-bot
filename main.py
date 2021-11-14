 
from threading import Thread
from gui import main
import time
import threading
import sys

try:
    from munch import munchify  # noqa
except ImportError:
    _HAS_MUNCH = False
else:
    _HAS_MUNCH = True


if __name__ == "__main__":
    th = Thread(target=main)
    th.start()

    from ig_engine import EngineIG
    engine_ig = EngineIG()
    th = Thread(target=engine_ig.run_cycle, name="IG_THREAD")
    th.start()

    while True:
        try:
            from ib_engine import EngineIBKR
            engine_ib = EngineIBKR()
            engine_ib.run_cycle()
            break
        except:
            th_names = [th.name for th in threading.enumerate()]
            if "Thread-1" not in th_names:
                sys.exit()
            print("IBKR connect issue. Retrying in 5 seconds...")
            time.sleep(5)
