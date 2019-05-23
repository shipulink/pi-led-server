import subprocess
import ctypes
import os.path

current_dir = os.path.dirname(__file__)
make_file_path = os.path.abspath(os.path.join(current_dir, "makeledlib.sh"))
subprocess.call(["sh " + make_file_path])
lib_abs_path = os.path.abspath(os.path.join(current_dir, "ledlib.so"))

ledlib = ctypes.CDLL(lib_abs_path)

while True:
    ledlib.send_zero
