import numpy as np
import os
import json
import matplotlib.pyplot as plt
import re

from inspect import currentframe, getouterframes

class Object(object):
    """
    This class represents an AIDA object which is envisioned to be the parent of most of the AIDA related classes.
    
    At a high level this class is a wrapper around a single dictionary object which provides support for complex getters.
    """

    def __init__(self, **kwargs):
        """
        Initializes this instance, and sets the logger for newly created instance.

        Arguments:
            logger (aida.Logger):
                the aida.Logger object
        """
        for key in kwargs:
            self.set(key, kwargs[key])

    def get(self, *args, **kwargs):
        """
        Gets the value for the key using the given args.

        If method get_{key} is defined for this object, call that method with
        args as its arguments, and return what it returns, otherwise if there
        is an attribute whose name matches the value stored in key then return
        it. None is returned otherwise.
        """
        key = args[0]
        if key is None:
            self.record_event('KEY_IS_NONE', self.get('code_location'))
        method = self.get_method("get_{}".format(key))
        if method is not None:
            args = args[1:]
            return method(*args, **kwargs)
        else:
            value = getattr(self, key, None)
            return value

    def get_method(self, method_name):
        """
        Returns the method whose name matches the value stored in method_name,
        None otherwise.
        """
        try:
            method = getattr(self, method_name)
            if not hasattr(method, "__call__"):
                raise AttributeError()
        except AttributeError:
            method = None
        return method
    
    def get_code_location(self):
        """
        Returns the filename and line number where this method is called.

        Used for recording an event in the logger.

        The return value is a dictionary with the following two keys:
            filename
            lineno
        """
        caller_frame_info = getouterframes(currentframe(), 2)[2]
        where = {'filename': caller_frame_info.filename, 'lineno': caller_frame_info.lineno}
        return where

    def record_event(self, event_code, *args):
        if self.get('logger') is not None:
            self.get('logger').record_event(event_code, *args)

    def set(self, key, value):
        setattr(self, key, value)

class Container(Object):
    """
    The AIDA container class.

    Internally, the instance of this class stores objects in a dictionary.
    """

    def __init__(self, **kwargs):
        """
        Initializes this instance, and sets the logger for newly created instance.

        This is where the empty store is initialized.

        Arguments:
            logger (aida.Logger):
                the aida.Logger object
        """
        self.store = {}
        super().__init__(**kwargs)

    def __iter__(self):
        """
        Returns the iterator over the store.
        """
        return iter(self.store)

    def get(self, *args, **kwargs):
        """
        Gets the value for the key using the given args, if found. Returns None otherwise.

        The value is looked up first in the parent object, returned if found. Otherwise,
        the value is looked up in the store, again returned if found. Otherwise, the
        key is added, to the store, with its value set to the default value provided
        or None, if no default value was provided.
        """
        key = args[0]
        default = kwargs['default'] if 'default' in kwargs else None
        value = super().get(*args, **kwargs)
        if value:
            return value
        elif key in self.store:
            return self.store[key]
        else:
            if value is None and default is not None:
                value = default
                self.add(key=key, value=value)
            return value

    def set(self, key, value):
        """
        Sets the value of the key in the store if key is found in the store, otherwise,
        the object's setter is called.
        """
        if key in self.store:
            self.store[key] = value
        else:
            super().set(key, value)

    def exists(self, key):
        """
        Returns True if key is found in the store, False otherwise.
        """
        return key in self.store

    def add(self, value, key=None):
        """
        Adds the value to the store and map it to the key if provided, otherwise,
        use the length of the store as the key.
        """
        if key is None:
            self.store[len(self.store)] = value
        else:
            self.store[key] = value

    def add_member(self, member):
        """
        Add a member to the container using the member.get('ID') as the key corresponding
        to which the member is stored.
        """
        if member.get('ID') not in self:
            self.add(key=member.get('ID'), value=member)
        else:
            self.record_event('DUPLICATE_VALUE', member.get('ID'), member.get('where'))

    def keys(self):
        """
        Returns a new view of the store's keys.
        """
        return self.store.keys()

    def values(self):
        """
        Returns a new view of the store's values.
        """
        return self.store.values()

    def __len__(self):
        return len(self.store)
    
    def to_dict(self):
        d = {}
        for k,v in self.store.items():
            if isinstance(v, Container):
                d[k] = v.to_dict()
            else:
                d[k] = v
        return d

class Entry(Object):
    """
    The Entry represents a line in a tab separated file.
    """

    def __init__(self, **kwargs):
        """
        Initializes this instance.

        Arguments:
            logger (aida.Logger):
                the aida.Logger object.
            keys (list of str):
                the list representing header fields.
            values (list of str):
                the list representing values corresponding to the keys.
            where (dict):
                a dictionary containing the following two keys representing the file location:
                    filename
                    lineno

        NOTE: The length of keys and values must match.
        """
        super().__init__(**kwargs)
        keys = kwargs['keys']
        values = kwargs['values']
        where = kwargs['where']
        if len(keys) != len(values):
            self.record_event('UNEXPECTED_NUM_COLUMNS', len(keys), len(values), where)
        self.where = where
        for i in range(len(keys)):
            self.set(keys[i], values[i].strip())

    def get_filename(self):
        """
        Gets the name of the file which this instance corresponds to.
        """
        return self.get('where').get('filename')
    
    def get_lineno(self):
        """
        Gets the line number which this instance corresponds to.
        """
        return self.get('where').get('lineno')

    def __str__(self):
        return '{}\n'.format('\t'.join([self.get(column) for column in self.get('schema').get('columns')]))

class FileHandler(Object):
    """
    File handler for reading tab-separated files.
   """

    def __init__(self, **kwargs):
        """
        Initializes this instance.
        Arguments:
            logger (aida.Logger):
                the aida.Logger object
            filename (str):
                the name of the file including the path
            header (aida.Header or None):
                if provided, this header will be used for the file,
                otherwise the header will be read from the first line.
            encoding (str or None):
                the encoding to be used for opening the file.
        """
        super().__init__(**kwargs)
        self.encoding = kwargs['encoding'] if 'encoding' in kwargs else None
        self.filename = kwargs['filename'] if 'filename' in kwargs else None
        self.header = kwargs['header'] if 'header' in kwargs else None
        self.logger = kwargs['logger'] if 'logger' in kwargs else None
        self.separator = '\t' if 'separator' not in kwargs else kwargs['separator']
        # lines from the file are read into entries (aida.Entry)
        self.entries = []
        self.load_file()
    
    def load_file(self):
        """
        Load the file.
        """
        with open(self.get('filename'), encoding=self.get('encoding')) as file:
            for lineno, line in enumerate(file, start=1):
                if self.get('header') is None:
                    self.header = FileHeader(logger=self.get('logger'), separator=self.get('separator'), header_line=line.rstrip())
                else:
                    where = {'filename': self.get('filename'), 'lineno': lineno}
                    entry = Entry(logger=self.get('logger'),
                                  keys=self.get('header').get('columns'),
                                  values=list(re.split(self.get('separator'), line.strip('\r\n'), maxsplit=len(self.get('header').get('columns'))-1)),
                                  where=where)
                    entry.set('where', where)
                    entry.set('header', self.get('header'))
                    entry.set('line', line)
                    self.get('entries').append(entry)

    def __iter__(self):
        """
        Returns iterator over entries.
        """
        return iter(self.get('entries'))

class FileHeader(Object):
    """
    The object representing the header of a tab separated file.
    """

    def __init__(self, **kwargs):
        """
        Initializes the FileHeader using header_line.

        Arguments:
            logger (aida.Logger):
                the aida.Logger object.
            header_line (str):
                the line used to generate the FileHeader object.
        """
        super().__init__(**kwargs)
        self.logger = kwargs['logger'] if 'logger' in kwargs else None
        self.line = kwargs['header_line'] if 'header_line' in kwargs else None
        self.separator = '\t' if 'separator' not in kwargs else kwargs['separator']
        self.columns = list(re.split(self.get('separator'), self.line))

    def __str__(self, *args, **kwargs):
        """
        Returns the string representation of the header.
        """
        return self.get('line')

def get_num_rows_and_columns(metatype):
    num_rows_columns = {
        'Event': [2,4],
        'Relation': [2,2],
        'Entity': [2,2],
        'ALL': [2,4],
        }
    return num_rows_columns[metatype]

def get_row_column_indexes(metric, metatype):
    metrics = {
        'Event': {
            'ArgumentMetricV1': [0,0],
            'ArgumentMetricV2': [0,1],
            'CoreferenceMetric': [0,2],
            'FrameMetric': [0,3],
            'TemporalMetric': [1,0],
            'TypeMetricV1': [1,1],
            'TypeMetricV2': [1,2],
            'TypeMetricV3': [1,3]
            },
        'Relation': {
            'ArgumentMetricV1': [0,0],
            'ArgumentMetricV2': [0,1],
            'FrameMetric': [1,0],
            'TemporalMetric': [1,1],
            },
        'Entity': {
            'CoreferenceMetric': [0,0],
            'TypeMetricV1': [0,1],
            'TypeMetricV2': [1,0],
            'TypeMetricV3': [1,1]
            },
        'ALL': {
            'ArgumentMetricV1': [0,0],
            'ArgumentMetricV2': [0,1],
            'CoreferenceMetric': [0,2],
            'FrameMetric': [0,3],
            'TemporalMetric': [1,0],
            'TypeMetricV1': [1,1],
            'TypeMetricV2': [1,2],
            'TypeMetricV3': [1,3]
            }
        }
    return metrics[metatype][metric]

sampling_study_output_file='./sampling_study_output.txt'

scores = [e for e in FileHandler(filename=sampling_study_output_file, separator='\s+')]

grouped_scores = Container()
for entry in scores:
    grouped_scores.get(entry.get('ci_size'), default=Container()) \
        .get(entry.get('language'), default=Container()) \
        .get(entry.get('metatype'), default=Container()) \
        .get(entry.get('metric'), default=Container()) \
        .add(key=entry.get('subsample_size'), value=entry)

for ci_size in grouped_scores:
    for language in grouped_scores.get(ci_size):
        for metatype in grouped_scores.get(ci_size).get(language):
            # generate a plot containing 8 subplots - one for each metric
            num_rows, num_columns = get_num_rows_and_columns(metatype)
            fig = plt.figure()
            fig.suptitle('Language: {} Metatype: {} - {} CI over Score - 95% CI over SD'.format(language, metatype, ci_size), fontsize=10)
            fig.text(0.5, 0.04, 'Subsample size (%)', ha='center')
            fig.text(0.04, 0.5, 'Significant difference', va='center', rotation='vertical')
            gs = fig.add_gridspec(num_rows, num_columns, hspace=0.4, wspace=0.1)
            #axs = gs.subplots()
            axs = gs.subplots(sharex='col', sharey='row')
            for metric in grouped_scores.get(ci_size).get(language).get(metatype):
                metric_scores = grouped_scores.get(ci_size).get(language).get(metatype).get(metric)
                row_idx, col_idx = get_row_column_indexes(metric, metatype)
                xs = []
                ys = []
                yerrs = []
                sdscores = []
                for subsample_size in sorted(grouped_scores.get(ci_size).get(language).get(metatype).get(metric)):
                    entry = grouped_scores.get(ci_size).get(language).get(metatype).get(metric).get(subsample_size)
                    sdscore = float(entry.get('sdscore'))
                    sdscore_sci = entry.get('sdscore_sci')
                    left, right = [float(v) for v in re.match(r"\d\d\%\((.*)\)", sdscore_sci).group(1).split(',')]
                    y = (left+right)/2
                    yerr = y-left
                    xs.append(subsample_size)
                    ys.append(y)
                    yerrs.append(yerr)
                    sdscores.append(sdscore)
                axs[row_idx, col_idx].plot(xs, sdscores)
                axs[row_idx, col_idx].errorbar(xs, ys, yerr=yerrs, capsize=2, fmt='.', ms=1)
                axs[row_idx, col_idx].set_title('Metric: {}'.format(metric), fontsize=5)
                axs[row_idx, col_idx].set_yticks([y*10 for y in range(0,11)])
                axs[row_idx, col_idx].set_yticklabels([y*10 for y in range(0,11)])
                axs[row_idx, col_idx].set_ylim([-10, 100])
                axs[row_idx, col_idx].tick_params(axis='x', labelsize=5)
                axs[row_idx, col_idx].tick_params(axis='y', labelsize=5)
            plt.savefig('plots/sdscores/{}_{}_{}.pdf'.format(ci_size, language, metatype))
            plt.close()


for ci_size in grouped_scores:
    for language in grouped_scores.get(ci_size):
        for metatype in grouped_scores.get(ci_size).get(language):
            # generate a plot containing 8 subplots - one for each metric
            num_rows, num_columns = get_num_rows_and_columns(metatype)
            fig = plt.figure()
            fig.suptitle('Language: {} Metatype: {} - {} CI over Score - 95% CI over Kendall\'s Tau'.format(language, metatype, ci_size), fontsize=10)
            fig.text(0.5, 0.04, 'Subsample size (%)', ha='center')
            fig.text(0.04, 0.5, 'Kendall\'s Tau', va='center', rotation='vertical')
            gs = fig.add_gridspec(num_rows, num_columns, hspace=0.4, wspace=0.1)
            #axs = gs.subplots()
            axs = gs.subplots(sharex='col', sharey='row')
            for metric in grouped_scores.get(ci_size).get(language).get(metatype):
                metric_scores = grouped_scores.get(ci_size).get(language).get(metatype).get(metric)
                row_idx, col_idx = get_row_column_indexes(metric, metatype)
                xs = []
                ys = []
                yerrs = []
                for subsample_size in sorted(grouped_scores.get(ci_size).get(language).get(metatype).get(metric)):
                    entry = grouped_scores.get(ci_size).get(language).get(metatype).get(metric).get(subsample_size)
                    kendalltau_sci = entry.get('kendalltau_sci')
                    left, right = [float(v) for v in re.match(r"\d\d\%\((.*)\)", kendalltau_sci).group(1).split(',')]
                    y = (left+right)/2
                    yerr = y-left
                    xs.append(subsample_size)
                    ys.append(y)
                    yerrs.append(yerr)
                axs[row_idx, col_idx].errorbar(xs, ys, yerr=yerrs, capsize=2, fmt='.', ms=1)
                axs[row_idx, col_idx].set_title('Metric: {}'.format(metric), fontsize=5)
                # axs[row_idx, col_idx].set_yticks([y*10 for y in range(0,11)])
                # axs[row_idx, col_idx].set_yticklabels([y*10 for y in range(0,11)])
                # axs[row_idx, col_idx].set_ylim([-10, 100])
                axs[row_idx, col_idx].tick_params(axis='x', labelsize=5)
                axs[row_idx, col_idx].tick_params(axis='y', labelsize=5)
            plt.savefig('plots/kendallstau/{}_{}_{}.pdf'.format(ci_size, language, metatype))
            plt.close()
