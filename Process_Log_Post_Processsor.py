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

        if preprocess_all:
            pass # run all preprocessing methods
