"""
creates an object that will process and store data from process_log.csv
data will only be processed (through the use of getters) when it is requested,
and once processed will be saved within the object so that any further polls
will be significantly quicker
"""

import os
import csv


class Processed_Logger_Data:
    def __init__(self, log_file, preprocess_all: bool = False) -> None:
        """
        if preprocess_all is True, then all data that can
        be output with getters will be processed in advanced
        """
        assert (os.path.exists(log_file)), "log_file does not exist"

        self.__csv_log_data: list[list] = list()

        # create and save a matrix of the CSV file
        with open(log_file, "r") as log_file_reader:
            log_file_csv_reader = csv.reader(log_file_reader)
            for row in log_file_csv_reader:
                self.__csv_log_data.append(list())
                for element in row:
                    self.__csv_log_data[-1].append(element)

        self.__user_list = list()
        self.__user_list_processed: bool = False

        self.__process_name_list = list()
        self.__process_name_list_processed: bool = False

        if preprocess_all:
            self.__process_user_list()
            self.__process_process_name_list()

        return None

    def __process_user_list(self) -> None:
        """
        does the actual processing for get_users()
        """
        for row in self.__csv_log_data:
            if row[0] == "I":
                row = row[1:] # we don't care if it's the inital run or not for this
            
            if row[0] == "U":
                # this signifies a user line
                if row[1] not in self.__user_list:
                    # row[1] is the user string
                    self.__user_list.append(row[1])

        self.__user_list_processed = True

        return None

    def get_users(self, force_rerun = False) -> list[str]:
        """
        get a list of all users that appear in the log file

        if force_rerun is True, processing will be rerun even if it has already been run
        """
        if not force_rerun and self.__user_list_processed:
            return self.__user_list

        else:
            self.__process_user_list()

        return self.__user_list

    def __process_process_name_list(self) -> None:
        """
        does the actual processing for get_process_names()
        """
        for row in self.__csv_log_data:
            if row[0] == "I":
                row = row[1:] # we don't care if it's the inital run or not for this
            
            if row[0] == "P":
                # this signifies a process line
                if row[2] not in self.__process_name_list:
                    # row[2] is the process string
                    self.__process_name_list.append(row[2])

        self.__process_name_list_processed = True

        return None

    def get_process_names(self, force_rerun = False) -> list[str]:
        """
        get a list of all process names that appear in the log file

        if force_rerun is True, processing will be rerun even if it has already been run
        """
        if not force_rerun and self.__process_name_list_processed:
            return self.__process_name_list

        else:
            self.__process_process_name_list()

        return self.__process_name_list


if __name__ == "__main__":
    data = Processed_Logger_Data("process_log.csv")
    print(data.get_users())
    print(data.get_process_names())
