import os
import psutil

print("os.cpu_count():", os.cpu_count())
print("psutil.cpu_count(logical=False):", psutil.cpu_count(logical=False))
