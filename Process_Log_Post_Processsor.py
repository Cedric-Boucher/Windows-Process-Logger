"""
creates an object that will process and store data from process_log.csv
data will only be processed (through the use of getters) when it is requested,
and once processed will be saved within the object so that any further polls
will be significantly quicker
"""

import os
import csv


class Processed_Logger_Data:
    def __init__(self, log_file, preprocess_all: bool = False):
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

        if preprocess_all:
            pass # run all preprocessing methods

    def get_users(self, force_rerun = False) -> list[str]:
        """
        get a list of all users that appear in the log file

        if force_rerun is True, processing will be rerun even if it has already been run
        """
        if not force_rerun and len(self.__user_list) > 0:
            return self.__user_list

        for row in self.__csv_log_data:
            if row[0] == "I":
                row = row[1:] # we don't care if it's the inital run or not for this
            
            if row[0] == "U":
                # this signifies a user line
                if row[1] not in self.__user_list:
                    # row[1] is the user string
                    self.__user_list.append(row[1])

        # after having gone through every row and adding all the data,
        return self.__user_list

