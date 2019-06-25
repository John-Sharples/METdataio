#!/usr/bin/env python3

"""
Program Name: write_stat_sql.py
Contact(s): Venita Hagerty
Abstract:
History Log:  Initial version
Usage: Write stat files (MET and VSDB) to a SQL database.
Parameters: N/A
Input Files: transformed dataframe of MET and VSDB lines
Output Files: N/A
Copyright 2019 UCAR/NCAR/RAL, CSU/CIRES, Regents of the University of Colorado, NOAA/OAR/ESRL/GSD
"""

# pylint:disable=no-member
# constants exist in constants.py

import sys
import os
# from pathlib import Path
import logging
import time
from datetime import timedelta
import pymysql
import numpy as np   # without this, pylint throws a maximum recursion error
import pandas as pd

import constants as CN


class WriteStatSql:
    """ Class to write stat files (MET and VSDB) to a SQL database
        Returns:
           N/A
    """

    def __init__(self, connection):
        # Connect to the database
        self.conn = pymysql.connect(host=connection['db_host'],
                                    port=connection['db_port'],
                                    user=connection['db_user'],
                                    passwd=connection['db_password'],
                                    db=connection['db_name'],
                                    local_infile=True)

        self.cur = self.conn.cursor()

    def write_sql_data(self, load_flags, load_files, stat_data):
        """ write stat files (MET and VSDB) to a SQL database.
            Returns:
               N/A
        """

        logging.debug("[--- Start write_sql_data ---]")

        write_time_start = time.perf_counter()

        try:
            self.cur.execute("SHOW GLOBAL VARIABLES LIKE 'local_infile';")
            result = self.cur.fetchall()
            logging.debug("local_infile is %s", result[0][1])

            # write out records for data files, but first:
            # check for duplicates if flag on - delete if found
            # put dat file keys into lines in dataframe

            next_file_id = self.get_next_id(CN.DATA_FILE, CN.DATA_FILE_ID)

            for full_file in load_files:
                # split path and filename
                split_file = full_file.rpartition('/')
                # add filename and path to the appropriate columns
                # add load date and mod date to columns
                # look for existing record
                self.cur.execute(CN.Q_FILE, [split_file[0], split_file[2]])

                result = self.cur.fetchone()
                # If you find a match, check the force_dup_file tag/flag
                if self.cur.rowcount > 0:
                    print("found file")
                    if not load_flags['force_dup_file']:
                        stat_data = stat_data.drop(stat_data[stat_data.data_file_id == \
                                                             load_files.index(full_file) + 1])
                        logging.warning("!!! Duplicate file %s without FORCE_DUP_FILE tag",
                                        full_file)
                    else:
                        data_file_records.loc[stat_data.data_file_id == \
                                              load_files.index(full_file) + 1,
                                              CN.DATA_FILE_ID] = result[0]

            # write out the data files. Put the keys into stat_data

            # reset the index in case any records were dropped
            stat_data.reset_index(drop=True, inplace=True)

            # find the unique headers for this current load job
            # for now, including VERSION to make pandas code easier - unlike MVLoad
            stat_headers = stat_data[CN.STAT_HEADER_KEYS].drop_duplicates()
            stat_headers.reset_index(drop=True, inplace=True)

            # At first, we do not know if the headers already exist, so we have no keys
            stat_headers[CN.STAT_HEADER_ID] = CN.NO_KEY

            # get the next valid header id. Set it to zero (first valid id) if no records yet
            next_header_id = self.get_next_id(CN.STAT_HEADER, CN.STAT_HEADER_ID)

            # if the flag is set to check for duplicate headers, get ids from existing headers
            if load_flags["stat_header_db_check"]:

                # For each header, query with unique fields to try to find a match in the database
                for row_num, data_line in stat_headers.iterrows():
                    self.cur.execute(CN.Q_HEADER, data_line.values[:-1].tolist())

                    result = self.cur.fetchone()
                    # If you find a match, put the key into the stat_headers dataframe
                    if self.cur.rowcount > 0:
                        stat_headers.loc[stat_headers.index[row_num], CN.STAT_HEADER_ID] = result[0]

            # For new headers add the next id to the row number/index to make a new key
            stat_headers.loc[stat_headers.stat_header_id == CN.NO_KEY, CN.STAT_HEADER_ID] = \
                        stat_headers.index + next_header_id

            # get just the new headers with their keys
            new_headers = stat_headers[stat_headers[CN.STAT_HEADER_ID] > (next_header_id - 1)]

            # Write any new headers out to a CSV file, and then load them into database
            if not new_headers.empty:
                # later in development, may wish to delete this file to clean up after writing
                tmpfile = os.getenv('HOME') + '/METdbLoadHeaders.csv'
                new_headers[CN.STAT_HEADER_FIELDS].to_csv(tmpfile, na_rep='-9999',
                                                          index=False, header=False, sep=CN.SEP)
                self.cur.execute(CN.L_HEADER.format(tmpfile, CN.STAT_HEADER, CN.SEP))

            # put the header ids back into the dataframe of all the line data
            stat_data = pd.merge(left=stat_data, right=stat_headers)

            # find all of the line types in the data
            line_types = stat_data.line_type.unique()

            # process one kind of line data at a time
            for line_type in line_types:

                # use the UC line type to index into the list of table names
                line_table = CN.LINE_TABLES[CN.UC_LINE_TYPES.index(line_type)]

                # Only variablw length lines have a line_data_id
                # more needs to be done on this
                if line_type in CN.VAR_LINE_TYPES:
                    # Get next valid line data id. Set it to zero (first valid id) if no records yet
                    next_line_id = \
                        self.get_next_id(line_table, CN.LINE_HEADER_ID)

                # get the line data of just this type and re-index
                line_data = stat_data[stat_data[CN.LINE_TYPE] == line_type]
                line_data.reset_index(drop=True, inplace=True)

                # write the lines out to a CSV file, and then load them into database
                # for debugging, unique. may want to reuse same name later - and delete
                tmpfile = os.getenv('HOME') + '/METdbLoadLines' + line_type + '.csv'
                line_data[CN.LINE_DATA_COLS[line_type]].to_csv(tmpfile, na_rep='-9999',
                                                               index=False, header=False,
                                                               sep=CN.SEP)
                self.cur.execute(CN.L_HEADER.format(tmpfile, line_table, CN.SEP))

            self.conn.commit()

        except (RuntimeError, TypeError, NameError, KeyError):
            logging.error("*** %s in write_sql_data ***", sys.exc_info()[0])

        finally:
            self.cur.close()
            self.conn.close()

        write_time_end = time.perf_counter()
        write_time = timedelta(seconds=write_time_end - write_time_start)

        logging.info("    >>> Write time: %s", str(write_time))

        logging.debug("[--- End write_sql_data ---]")

    def get_next_id(self, table, field):
        """ given a field for a table, find the max field value and return it plus one.
            Returns:
               next valid id to use in an id field in a table
        """
        # get the next valid id. Set it to zero (first valid id) if no records yet
        try:
            next_id = 0
            query_for_id = "SELECT MAX(" + field + ") from " + table
            self.cur.execute(query_for_id)
            result = self.cur.fetchone()
            if result[0] is not None:
                next_id = result[0] + 1
            return next_id

        except (RuntimeError, TypeError, NameError, KeyError):
            logging.error("*** %s in write_sql_data get_next_id ***", sys.exc_info()[0])
