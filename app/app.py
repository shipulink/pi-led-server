import subprocess
import ctypes
import os.path

subprocess.call(["sh makeledlib.sh"])
lib_abs_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "ledlib.so"))

ledlib = ctypes.CDLL(lib_abs_path)

while True:
    ledlib.send_zero
