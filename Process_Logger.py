import psutil
import win32process
import win32gui
import datetime
import time


def get_active_window_process() -> list:
    """
    returns [process_id, exe_name, name_of_process]
    for the process that is in focus by the user, or None
    """
    pid = None
    # check which process is in focus by the user
    window = win32gui.GetForegroundWindow()
    pid = win32process.GetWindowThreadProcessId(window)[1]
    if pid is not None:
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


def append_to_log_file(file = "process_log.csv", last_known_active_processes = [], last_known_active_window_process = []) -> None:
    """
    appends data to log file, only if there is any change in data.
    returns [active_processes, active_window_process] to be passed
    as input on the next call

    data format in log (csv) file:
    date(YYYY-MM-DD),time(HH-MM-SS.ZZZZ),PID(int),name(str),focused(bool),start/end,initial_run
    """
    active_window_process = get_active_window_process()
    active_processes = get_active_processes()

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
                    file_object.writelines(["{},{},{},{},{},{},{}\n".format(date, time, active_window_process, active_window_process, True, None, first_run)])
                else:
                    file_object.writelines(["{},{},{},{},{},{},{}\n".format(date, time, active_window_process[0], active_window_process[1], True, None, first_run)])
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
                        output_lines.append("{},{},{},{},{},{},{}\n".format(date, time, process[0], process[1], False, start_or_end, first_run))
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

