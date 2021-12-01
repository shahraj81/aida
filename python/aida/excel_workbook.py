"""
File handler for reading tab-separated files.
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "2 January 2020"

from aida.object import Object

import pandas as pd

class WorksheetHeader(Object):
    def __init__(self, logger, columns):
        super().__init__(logger)
        self.logger = logger
        self.line = '\t'.join(columns)
        self.columns = columns
    
    def __str__(self, *args, **kwargs):
        return self.get('line')

class WorksheetEntry(Object):
    def __init__(self, logger, where):
        super().__init__(logger)
        self.where = where

    def get_line(self):
        return '\t'.join([str(self.get(c)) for c in self.get('header').get('columns')])

class Worksheet(Object):
    def __init__(self, logger, filename, sheet_name, data_frame):
        super().__init__(logger)
        self.filename = filename
        self.sheet_name = sheet_name
        self.data_frame = data_frame
        self.header = WorksheetHeader(self.get('logger'),
                                      list(self.get('data_frame').columns.values))
        self.entries = []
        self.load_entries()

    def load_entries(self):
        for i, row in self.get('data_frame').iterrows():
            where = {'filename': ':'.join([self.get('filename'),
                                           self.get('sheet_name')]),
                     'lineno': i+1
                     }
            entry = WorksheetEntry(self.get('logger'), where)
            entry.set('header', self.get('header'))
            for j, column in row.iteritems():
                entry.set(j.strip(), column)
            self.get('entries').append(entry)

    def __iter__(self):
        return iter(self.get('entries'))

class ExcelWorkbook(Object):
    def __init__(self, logger, filename):
        super().__init__(logger)
        self.filename = filename
        self.logger = logger
        self.worksheets = {}
        self.load_file()

    def load_file(self):
        sheets = pd.read_excel(self.get('filename'), sheet_name=None)
        for sheet_name, df in sheets.items():
            self.get('worksheets')[sheet_name] = Worksheet(self.get('logger'), self.get('filename'), sheet_name, df)

    def __iter__(self):
        return iter(self.get('worksheets'))