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
    global last_input_time
    return time.time() - last_input_time


def append_to_log_file(file = "process_log.csv") -> None:
    """
    appends data to log file, only if there is any change in data.
    returns [active_processes, active_window_process] to be passed
    as input on the next call

    see FILE FORMAT.txt
    """

    active_window_process = get_active_window_process()
    active_processes = get_active_processes()
    [is_locked, current_user] = check_user_and_locked()
    time_since_user_input = get_last_input_time()

    ########## initialize variables and check for differences ##########
    try:
        same_processes = (active_processes == append_to_log_file.last_known_active_processes)
    except AttributeError:
        append_to_log_file.last_known_active_processes = []
        same_processes = False
    
    try:
        same_active_process = (active_window_process == append_to_log_file.last_known_active_window_process)
    except AttributeError:
        append_to_log_file.last_known_active_window_process = []
        same_active_process = False
    
    try:
        same_locked = (is_locked == append_to_log_file.last_known_locked)
    except AttributeError:
        append_to_log_file.last_known_locked = None
        same_locked = False
    
    try:
        same_user = (current_user == append_to_log_file.last_known_user)
    except AttributeError:
        append_to_log_file.last_known_user = None
        same_user = False

    try:
        same_last_active_time = (time_since_user_input == append_to_log_file.last_known_user_time)
    except AttributeError:
        append_to_log_file.last_known_user_time = 0
        same_last_active_time = False
    ########## end initialize variables and cehck for differences ##########

    date = datetime.datetime.now().strftime("%Y-%m-%d")
    time = datetime.datetime.now().strftime("%H-%M-%S.%f")

    if append_to_log_file.last_known_active_processes == [] or append_to_log_file.last_known_active_window_process == []:
        first_run = True
    else:
        first_run = False

    with open(file, "a") as file_object:
        ########## Focus change ##########
        if not same_active_process:
            # append changed focused process to log
            if active_window_process == None:
                output_text = "F,{},{},{},{}\n".format(date, time, active_window_process, active_window_process)
            else:
                output_text = "F,{},{},{},{}\n".format(date, time, active_window_process[0], active_window_process[1])
            if first_run:
                output_text = "I,"+output_text
            file_object.writelines([output_text])
        ########## end Focus change ##########

        ########## Locked change ##########
        if not same_locked:
            # append lock change to log
            output_text = "L,{},{},{}\n".format(date, time, is_locked)
            if first_run:
                output_text = "I,"+output_text
            file_object.writelines([output_text])
        ########## end Locked change ##########

        ########## User change ##########
        if not same_user:
            # append logged in user change to log
            output_text = "U,{},{},{}\n".format(date, time, current_user)
            if first_run:
                output_text = "I,"+output_text
            file_object.writelines([output_text])
        ########## end User change ##########

        ########## Process changes ##########
        if not same_processes:
            # append process changes to log
            process_differences = [process for process in active_processes if process not in append_to_log_file.last_known_active_processes]
            [process_differences.append(process) for process in append_to_log_file.last_known_active_processes if process not in active_processes]
            # process_differences is the symmetric difference between the two lists of active processes (set theory stuff)
            process_differences = [process for process in process_differences if process != []] # filtering out empty processes
            output_lines = list()
            for process in process_differences:
                if process in active_processes:
                    start_or_end = "start"
                else:
                    start_or_end = "end"
                output_text = "P,{},{},{},{},{}\n".format(date, time, process[0], process[1], start_or_end)
                if first_run:
                    output_text = "I,"+output_text
                output_lines.append(output_text)
            file_object.writelines(output_lines)
        ########## end Process changes ##########

        ########## User activity time change ##########
        if not same_last_active_time:
            # append last active time to log
            output_text = "A,{},{},{}\n".format(date, time, time_since_user_input)
            if first_run:
                output_text = "I,"+output_text
            file_object.writelines([output_text])
        ########## end User activity time change ##########

    return


def main() -> None:
    file = "process_log_test.csv"
    runs = 0
    while True:
        runs += 1
        append_to_log_file(file=file)
        print("\rlog runs: " + str(runs), end="")
        time.sleep(30)


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