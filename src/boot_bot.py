import subprocess
import sys
import os
import time

p = subprocess.Popen(
    "exec python3 bot.py", shell=True, stdout=sys.stdout, stderr=sys.stderr
)

while True:
    if os.path.exists("./reboot"):
        os.remove("./reboot")
        p.kill()
        p = subprocess.Popen("exec python3 bot.py", shell=True)
    elif os.path.exists("./shutdown"):
        os.remove("./shutdown")
        p.kill()
        break
    time.sleep(5)
