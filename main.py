from machine import SDCard
import os

try:
    sd = SDCard(slot=2)
    os.mount(sd, "/sd")
    # "import sd" is fail in MicroPython
    os.chdir("/sd")
except:
    print("SD card not found")

with open("__init__.py", "r") as f:
    exec(f.read())
