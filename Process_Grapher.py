import platform
print(platform.system())

with open("process_log_test.csv", "r") as f:
    log_file_content = f.read()


import datetime
import matplotlib.pyplot as plt

def create_process_pie_chart(log_file_content):
    # initialize a dictionary to track the total active time for each process
    process_active_time = {}

    # split the log file content into lines
    lines = log_file_content.split("\n")

    # initialize variables to track the current process and its start time
    current_process = None
    current_process_start_time = None
    current_time = None

    # loop through each line in the log file
    for line in lines:
        if line.startswith("I"):
            # ignore the fact that it's an I line for now
            line = line[2:]
        if line.startswith("T"):
            # update current time
            current_time = datetime.datetime.strptime(line.split(",")[1] + " " + line.split(",")[2], "%Y-%m-%d %H-%M-%S.%f")
        # check the line start character and process accordingly
        if line.startswith("F"):
            # update the current process in focus
            current_process = line.split(",")[2]
        elif line.startswith("P"):
            # extract the process name from the line
            process_name = line.split(",")[2]
            # check if the process has started or ended
            if "start" in line:
                # update the current process and its start time
                current_process = process_name
                current_process_start_time = current_time
            else:
                # calculate the active time for the current process and add it to the dictionary
                if current_process in process_active_time:
                    process_active_time[current_process] += current_time - current_process_start_time
                else:
                    process_active_time[current_process] = current_time - current_process_start_time

    # sort the process active time dictionary by value in descending order
    sorted_active_time = sorted(process_active_time.items(), key=lambda x: x[1], reverse=True)

    # extract the top 5 processes and their active time
    top_processes = [x[0] for x in sorted_active_time[:5]]
    top_active_time = [x[1].total_seconds() / 60 for x in sorted_active_time[:5]]

    # plot the pie chart
    plt.pie(top_active_time, labels=top_processes, autopct="%1.1f%%")
    plt.title("Processes by Total Active Time")
    plt.show()


def pie_chart_focused_processes(log_data):
    process_focused_times = {}
    current_process = None
    current_process_start_time = None

    lines = log_data.split("\n")


    for line in lines:
        if line.startswith("I"):
            line = line[2:]
        line_parts = line.strip().split(',')
        if line.startswith("T"):
            # update current time
            current_time = datetime.datetime.strptime(line_parts[1] + " " + line_parts[2], "%Y-%m-%d %H-%M-%S.%f")


        if line_parts[0] == 'F':
            # A new process has come into focus or the log has ended
            if current_process is not None:
                # Update the total time for the previous process in focus
                end_time = current_time
                focused_time = end_time - current_process_start_time
                if current_process in process_focused_times:
                    process_focused_times[current_process] += focused_time
                else:
                    process_focused_times[current_process] = focused_time

            # Update the current process in focus and its start time
            current_process = line_parts[2]
            current_process_start_time = current_time

    # Add the final focused time to the process_focused_times dictionary
    if current_process is not None:
        focused_time = datetime.datetime.now() - current_process_start_time
        if current_process in process_focused_times:
            process_focused_times[current_process] += focused_time
        else:
            process_focused_times[current_process] = focused_time

    # Create the pie chart
    labels = list(process_focused_times.keys())
    times = list(process_focused_times.values())
    plt.pie([x.total_seconds() for x in times], labels=labels, autopct='%1.1f%%')
    plt.title('Focused Processes')
    plt.show()


create_process_pie_chart(log_file_content)
pie_chart_focused_processes(log_file_content)

