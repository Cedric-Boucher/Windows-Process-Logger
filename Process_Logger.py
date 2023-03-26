import psutil
import wmi
import win32process
import win32gui
from pynput import keyboard, mouse
import datetime
import time

########## initialize user activity listener ##########
last_input_time = time.time()

def on_activity(*args):
    global last_input_time
    last_input_time = time.time()

keyboard_listener = keyboard.Listener(on_press=on_activity, on_release=on_activity)
mouse_listener = mouse.Listener(on_move=on_activity, on_click=on_activity)

keyboard_listener.start()
mouse_listener.start()
########## end initialize user activity listener ##########

def get_active_window_process() -> list:
    """
    returns [process_id, exe_name, name_of_process]
    for the process that is in focus by the user, or None
    """
    pid = None
    # check which process is in focus by the user
    window = win32gui.GetForegroundWindow()
    pid = win32process.GetWindowThreadProcessId(window)[1]
    if pid is not None and pid >= 0:
        try: # try getting information about the process
            process = psutil.Process(pid)
            status = process.status()
            if status == "running":
                exe_name = process.name()
                return [pid, exe_name]
            else:
                return None
        except psutil.NoSuchProcess:
            pass
    else:
        return None


def get_active_processes() -> list:
    """
    gets all running processes and returns
    a list of lists, where each element is
    [process_id, exe_name, name_of_process]
    """
    pids = psutil.pids() # get a list of process IDs
    output = list()

    for pid in pids: # for each process ID, add information to output list
        try:
            process = psutil.Process(pid)
            status = process.status()
            if status == "running":
                exe_name = process.name()
                output.append([pid, exe_name])
        except psutil.NoSuchProcess:
            pass            
    
    return output


def check_user_and_locked() -> list:
    """
    checks if computer is locked or unlocked
    and which user is logged in
    (a user can be logged in even if computer is locked)
    returns list: [is_locked (bool), logged_in_user (string) or None]
    """
    # Initialize the WMI module
    c = wmi.WMI()

    # Query for the current user
    user_query = "SELECT * FROM Win32_ComputerSystem"
    user_info = c.query(user_query)[0]

    # Check if the user is logged in or not
    if user_info.UserName == None:
        # print("No user is currently logged in.")
        current_user = None
    else:
        # print("The current user is:", user_info.UserName)
        current_user = str(user_info.UserName)

    # Check if the computer is locked or not
    lock_query = "SELECT * FROM Win32_Process WHERE Name='LogonUI.exe'"
    lock_info = c.query(lock_query)
    if len(lock_info) > 0:
        # print("The computer is currently locked.")
        is_locked = True
    else:
        # print("The computer is currently unlocked.")
        is_locked = False

    return [is_locked, current_user]


def get_last_input_time() -> float:
    """
    returns how many seconds ago was the last user input
    """
    return time.time() - last_input_time


def append_to_log_file(file = "process_log.csv", last_known_active_processes = [], last_known_active_window_process = []) -> None:
    """
    appends data to log file, only if there is any change in data.
    returns [active_processes, active_window_process] to be passed
    as input on the next call

    data format in log (csv) file:
    date(YYYY-MM-DD),time(HH-MM-SS.ZZZZ),PID(int),name(str),focused(bool),is_locked(bool),current_user(str),start/end,initial_run
    """

    # FIXME: there is a lot of redundancy in each line of the csv

    active_window_process = get_active_window_process()
    active_processes = get_active_processes()
    [is_locked, current_user] = check_user_and_locked()

    same_processes = (active_processes == last_known_active_processes)
    same_active_process = (active_window_process == last_known_active_window_process)

    if last_known_active_processes == [] or last_known_active_window_process == []:
        first_run = True
    else:
        first_run = False

    if (not same_active_process) or (not same_processes):
        date = datetime.datetime.now().strftime("%Y-%m-%d")
        time = datetime.datetime.now().strftime("%H-%M-%S.%f")
        with open(file, "a") as file_object:
            if not same_active_process:
                # append changed focused process to log
                if active_window_process == None:
                    file_object.writelines(["{},{},{},{},{},{},{},{},{}\n".format(date, time, active_window_process, active_window_process, True, is_locked, current_user, None, first_run)])
                else:
                    file_object.writelines(["{},{},{},{},{},{},{},{},{}\n".format(date, time, active_window_process[0], active_window_process[1], True, is_locked, current_user, None, first_run)])
            if not same_processes:
                # append changed processes to log
                process_differences = [process for process in active_processes if process not in last_known_active_processes]
                [process_differences.append(process) for process in last_known_active_processes if process not in active_processes]
                # process_differences is the symmetric difference between the two lists of active processes (set theory stuff)
                output_lines = list()
                for process in process_differences:
                    if process != []:
                        if process in active_processes:
                            start_or_end = "start"
                        else:
                            start_or_end = "end"
                        output_lines.append("{},{},{},{},{},{},{},{},{}\n".format(date, time, process[0], process[1], False, is_locked, current_user, start_or_end, first_run))
                file_object.writelines(output_lines)
    
    return [active_processes, active_window_process]


def main() -> None:
    active_processes, active_window_process = append_to_log_file()
    runs = 1
    while True:
        print("\rlog runs: " + str(runs), end="")
        time.sleep(30)
        active_processes, active_window_process = append_to_log_file(last_known_active_processes = active_processes, last_known_active_window_process = active_window_process)
        runs += 1


if __name__ == "__main__":
    main()

# TODO: csv is not the best format for the log, maybe try using flags for different kinds of lines to avoid redundancy?
# TODO: you don't check if is_locked or current_user changes between logs, if no proccesses change, any updates don't get logged

"""
LOG file format:
    lines can start with one of: "F" (focus change), "L" (locked/unlocked), "U" (user change), "P" (process start/end), "I" (initial run of program), "A" (user activity)

    format for each line start:
        F,date(YYYY-MM-DD),time(HH-MM-SS.ZZZZ),PID(int),name(str)
        which means that process with process ID "PID" and name "name" is now in focus, and whatever process that was previously in focus no longer is

        L,date(YYYY-MM-DD),time(HH-MM-SS.ZZZZ),is_locked(bool)
        which simply indicates a change in the locked status of the computer, and is_locked is true if the computer is locked, else false

        U,date(YYYY-MM-DD),time(HH-MM-SS.ZZZZ),current_user(str)
        which indicates a change in the currently logged in user

        P,date(YYYY-MM-DD),time(HH-MM-SS.ZZZZ),PID(int),name(str),start/end
        which indicates that a process "PID" has either started or ended since the last time the script checked for running programs

        A,date(YYYY-MM-DD),time(HH-MM-SS.ZZZZ),time_since_last_user_activity(float)
        which indicates a change in time since last user activity
        if this is an "I" line, time should be 0 (or near 0)
        if no user activity is detected, no new A lines will be added, when user activity is detected, a new A line will be added on the next log cycle

        I,[]
        where [] is any other line format as described above
        the lines written to the log file on startup of the script will have this format, and are otherwise identical to normal lines
        the reason this distinction exists is that lines from the first run can be redundant or contain "outdated" information, and should be treated separately
"""