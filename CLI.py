from src.app_init import init
from time import time as current_time
from os import chdir, path as os_path
from src.config.setup_logger import setup_logging

CURRENT_DIR = os_path.dirname(os_path.abspath(__file__))


if __name__ == "__main__":
    chdir(CURRENT_DIR)
    setup_logging()
    update_older: callable
    update_newer: callable
    update_older, update_newer = init(".")
    while True:
        start_time = current_time()
        update_older()
        update_newer()
        print("\nFinish.")
        print("runtime: %s seconds" % (current_time() - start_time))
        c = input("Press Enter to continue or -1 to exit...\n")
        if c == "-1":
            break
