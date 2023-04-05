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
    date = datetime.datetime.now().strftime("%Y-%m-%d")
    time = datetime.datetime.now().strftime("%H-%M-%S.%f")

    ########## initialize variables and check for differences ##########
    try:
        same_datetime = (date == append_to_log_file.last_known_date and time == append_to_log_file.last_known_time)
    except AttributeError:
        append_to_log_file.last_known_date = date
        append_to_log_file.last_known_time = time
        same_datetime = False

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


    if append_to_log_file.last_known_active_processes == [] or append_to_log_file.last_known_active_window_process == []:
        first_run = True
    else:
        first_run = False

    with open(file, "a") as file_object:
        ########## Date/Time change ##########
        if not same_datetime:
            output_text = "T,{},{}\n".format(date, time)
            if first_run:
                output_text = "I,"+output_text
            file_object.writelines([output_text])
        ########## end Date/Time change ##########

        ########## Focus change ##########
        if not same_active_process:
            # append changed focused process to log
            if active_window_process == None:
                output_text = "F,{},{}\n".format(active_window_process, active_window_process)
            else:
                output_text = "F,{},{}\n".format(active_window_process[0], active_window_process[1])
            if first_run:
                output_text = "I,"+output_text
            file_object.writelines([output_text])
        ########## end Focus change ##########

        ########## Locked change ##########
        if not same_locked:
            # append lock change to log
            output_text = "L,{}\n".format(is_locked)
            if first_run:
                output_text = "I,"+output_text
            file_object.writelines([output_text])
        ########## end Locked change ##########

        ########## User change ##########
        if not same_user:
            # append logged in user change to log
            output_text = "U,{}\n".format(current_user)
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
                output_text = "P,{},{},{}\n".format(process[0], process[1], start_or_end)
                if first_run:
                    output_text = "I,"+output_text
                output_lines.append(output_text)
            file_object.writelines(output_lines)
        ########## end Process changes ##########

        ########## User activity time change ##########
        if not same_last_active_time:
            # append last active time to log
            output_text = "A,{}\n".format(time_since_user_input)
            if first_run:
                output_text = "I,"+output_text
            file_object.writelines([output_text])
        ########## end User activity time change ##########

    ########## update last_known flags ##########
    append_to_log_file.last_known_date = date
    append_to_log_file.last_known_time = time
    append_to_log_file.last_known_active_processes = active_processes
    append_to_log_file.last_known_active_window_process = active_window_process
    append_to_log_file.last_known_locked = is_locked
    append_to_log_file.last_known_user = current_user
    append_to_log_file.last_known_user_time = last_input_time
    ########## end update last_known flags ##########

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

