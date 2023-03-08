######## method of getting all running proccesses, slow AF ########
"""
import wmi

f = wmi.WMI()

print("pid Process name")

for process in f.Win32_Process():
    print(f"{process.ProcessId} {process.Name}")
print(len(f.Win32_Process()))
"""

######## method of getting active focused proccess ########
"""
import psutil

def get_active_window_process():
    pid = None
    import win32process
    import win32gui
    window = win32gui.GetForegroundWindow()
    pid = win32process.GetWindowThreadProcessId(window)[1]

    if pid is not None:
        return psutil.Process(pid)

print(get_active_window_process())

"""

######## method of getting all running processes, better and faster ########
import psutil

# Get a list of process IDs
pids = psutil.pids()

# Print the list of process IDs
for pid in pids:
    try:
        process = psutil.Process(pid)
        name = process.name()
        status = process.status()
        memory_info = process.memory_info()

        # Do something with the information
        print(f"PID {pid}: {name} ({status}) - Memory: {memory_info.rss / (1024*1024)} MB")
    except psutil.NoSuchProcess:
        pass
print(len(pids))
