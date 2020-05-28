"""
Logger for AIDA evaluation.
"""
__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "24 December 2019"

import logging
import os
import sys
import traceback

class Logger:
    """
    The logger for AIDA related scripts.
    
    This module is a wrapper around the Python 'logging' module which is internally used to
    record events of interest.
    """
    
    # the dictionary used to store event specifications for recording log events
    # the content of this dictionary are read from file: event_specs_filename
    event_specs = {}
    num_errors = 0
    num_warnings = 0
    
    def __init__(self, log_filename, event_specs_filename, argv, debug_level=logging.DEBUG):
        """
        Initialize the logger object.
        
        Arguments:
            log_filename (str):
                Name of the file to which log output is written
            event_specs_filename (str):
                Name of the file containing events handled by the logger
            argv (list):
                sys.argv as received by the invoking script
            debug_level (logging.LEVEL, OPTIONAL):
                Minimum logging.LEVEL to be reported.
                LEVEL is [CRITICAL|ERROR|WARNING|INFO|DEBUG].
                Default debug level is logging.DEBUG.
                The 'logging' module defines the following weights to different levels:
                    CRITICAL = 50
                    FATAL = CRITICAL
                    ERROR = 40
                    WARNING = 30
                    WARN = WARNING
                    INFO = 20
                    DEBUG = 10
                    NOTSET = 0                
        """
        
        self.log_filename = log_filename
        self.event_specs_filename = event_specs_filename
        self.path_name = os.getcwd()
        self.file_name = argv[0]
        self.arguments = " ".join(argv[1:])
        self.script_codename = self.file_name
        self.debug_level = debug_level
        self.logger_object = logging.getLogger(self.file_name)
        self.configure_logger()
        self.record_program_invokation()
        self.load_event_specs()
        
    def configure_logger(self):
        """
        Set the output file of the logger, the debug level, format of log output, and
        format of date and time in log output.
        """
        logging.basicConfig(filename=self.log_filename, 
                                level=self.debug_level,
                                format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                                datefmt='%m/%d/%Y %I:%M:%S %p')        
    
    def get_logger(self):
        """
        Returns the logger object which can be used for recording events.
        """
        return self.logger_object

    def get_num_errors(self):
        """
        Returns the number of errors encountered.
        """
        return self.num_errors
    
    def get_num_warnings(self):
        """
        Returns the number of warnings encountered.
        """
        return self.num_warnings
    
    def get_stats(self):
        """
        Return a tuple (num_warnings, num_errors)
        """
        return (self.num_warnings, self.num_errors)    

    def load_event_specs(self):
        """
        Load specifications of events that the logger supports.
        """
        with open(self.event_specs_filename, 'r') as event_specs_file:
            lines = event_specs_file.readlines()
        header = lines[0].strip().split(None, 2)
        for line in lines[1:]:
            line_dict = dict(zip(header, line.strip().split(None, 2)))
            self.event_specs[line_dict['code']] = line_dict        

    def record_event(self, event_code, *args):
        """
        Record an event.
        
        The method can be called as:
            record_event(EVENT_CODE)
            record_event(EVENT_CODE, ARG1, ...)
            record_event(EVENT_CODE, WHERE)
            record_event(EVENT_CODE, ARG1, ARG2, ..., ARGN, WHERE)
        
        WHERE is always the last argument, and is optional. It is expected to be a dictionary 
        containing two keys: 'filename' and 'lineno'.
        
        EVENT_CODE is used to lookup an event object which is a dictionary containing the following
        keys: TYPE, CODE and MESSAGE.
        
        TYPE can have one of the following values: CRITICAL, DEBUG, ERROR, INFO, and WARNING.
        
        CODE is a unique ID of an event.
         
        MESSAGE is the message written to the log file. It has zero or more arguments to be filled 
        by ARG1, ARG2, ...
        """
        argslst = []
        where = None
        if len(args):
            argslst = list(args)
            if isinstance(argslst[-1], dict):
                where = argslst.pop()
        if event_code in self.event_specs:
            event_object = self.event_specs[event_code]
            event_type = event_object['type']
            event_message = event_object['message'].format(*argslst)
            if where is not None:
                event_message += " at " + where['filename'] + ":" + str(where['lineno'])
            if event_type.upper() == "CRITICAL":
                self.logger_object.critical(event_message + "\n" + "".join(traceback.format_stack()))
                sys.exit(event_message + "\n" + "".join(traceback.format_stack()))
            elif event_type.upper() == "DEBUG":
                self.logger_object.debug(event_message)
            elif event_type.upper() == "ERROR":
                self.logger_object.error(event_message)
                self.num_errors = self.num_errors + 1
            elif event_type.upper() == "INFO":
                self.logger_object.info(event_message)
            elif event_type.upper() == "WARNING":
                self.logger_object.warning(event_message)
                self.num_warnings = self.num_warnings + 1
            else:
                error_message = "Unknown event type '" + event_type + "' for event: " + event_code
                self.logger_object.error(error_message + "\n" + "".join(traceback.format_stack()))
                sys.exit(error_message + "\n" + "".join(traceback.format_stack()))
        else:
            error_message = "Unknown log event: " + event_code
            self.logger_object.error(error_message + "\n" + "".join(traceback.format_stack()))
            sys.exit(error_message + "\n" + "".join(traceback.format_stack()))

    def record_program_invokation(self):
        """
        Record how this program was invoked.
        """
        debug_message = "Execution begins {current_dir:" + self.path_name + ", script_name:" + self.file_name + ", arguments:" + self.arguments +"}"  
        self.logger_object.info(debug_message)