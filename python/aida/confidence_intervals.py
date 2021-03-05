"""
AIDA class for bootstrap resampling based two-sided BCA confidence intervals.
"""
from aida.file_handler import FileHandler
from aida.container import Container
__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "26 February 2021"

import numpy as np

from aida.object import Object
from arch.bootstrap import IIDBootstrap

class ConfidenceIntervals(Object):
    """
    AIDA class for bootstrap resampling BCA confidence intervals.
    """

    separators = {
        'pretty': None,
        'tab': '\t',
        'space': ' '
        }

    def __init__(self, logger, **kwargs):
        """
        Arguments
            input:           Input file containing scores (required).

            primary_key_col: Comma-separated list of column-names to be used for
                             generating confidence intervals (required).

                             If provided, confidence intervals will be separately
                             generated corresponding to each value of the primary_key
                             in the input file.

                             If left blank, confidence scores corresponding to all
                             non-summary lines will be used for generating confidence
                             intervals.

            score:           Name of the column containing the scores to be used for
                             generating confidence intervals.

            aggregate:       Dictionary containing key-value pairs used to identify
                             aggregate score lines in the input file.

            run_id_col:      Name of the column from input file containing
                             RunID. (required).

            sizes:           Comma-separated list of confidence sizes (optional).
                             Default value: "0.9, 0.95, 0.99".

            seed_value:      Seed value for computing confidence interval (optional).
        """
        super().__init__(logger)
        for key in kwargs:
            self.set(key, kwargs[key])
        self.scores = FileHandler(logger, self.get('input'))
        self.confidence_intervals = Container(logger)
        self.widths = {}
        self.compute_confidences()

    def get_primary_key(self, entry):
        primary_key = {}
        for field_name in self.get('primary_key_col').split(','):
            value = entry.get(field_name)
            if value is None:
                self.record_event('MISSING_ITEM_WITH_KEY', 'Column name', field_name, entry.get('where'))
            else:
                primary_key[field_name] = value
        return primary_key

    def get_entry_score(self, entry):
        score_column = self.get('score')
        value = entry.get(score_column)
        if value is None:
            self.record_event('MISSING_ITEM_WITH_KEY', 'Column name', score_column, entry.get('where'))
        return value

    def is_aggregate(self, entry):
        for key, value in self.get('aggregate').items():
            if entry.get(key) != value:
                return False
        return True

    def get_custom_filter_strategy_columns(self, primary_key):
        columns = [k for k,v in primary_key.items() if v=='ALL'] if primary_key is not None else []
        for entry in self.get('scores'):
            if not self.is_aggregate(entry):
                for field_name in columns:
                    if entry.get(field_name) == 'ALL':
                        columns.remove(field_name)
        return columns

    def filter_entries(self, aggregate=None, primary_key=None):
        entries = []
        custom_filter_strategy_fields = self.get('custom_filter_strategy_columns', primary_key)
        for entry in self.get('scores'):
            if aggregate is not None and aggregate != self.is_aggregate(entry):
                continue
            if primary_key is not None:
                entry_primary_key = self.get('primary_key', entry)
                filter_out = False
                for field_name in primary_key:
                    if field_name not in custom_filter_strategy_fields:
                        if primary_key[field_name] != entry_primary_key[field_name]:
                            filter_out = True
                if filter_out:
                    continue
            entries.append(entry)
        return entries

    def get_confidence_interval_sizes(self):
        return sorted([float(size) for size in self.get('sizes').split(',')])

    def get_confidence_interval(self, scores, ci_method='bca', ci_size=0.95, seed_value=None):
        """
        Compute two sided bootstrap confidence interval
        """
        def score(x):
            return np.array([x.mean()])
        data = np.array([float(score) for score in scores])
        if min(data) == max(data):
            return tuple([min(data), max(data)])
        bs = IIDBootstrap(data)
        if seed_value is not None:
            bs.seed(seed_value)
        ci = bs.conf_int(score, 1000, method=ci_method, size=ci_size, tail='two')
        return tuple([ci[0][0], ci[1][0]])

    def compute_confidences(self):
        logger = self.get('logger')
        for aggregate_entry in self.filter_entries(aggregate=True, primary_key=None):
            primary_key = self.get('primary_key', aggregate_entry)
            primary_key_str = '.'.join([primary_key[fn] for fn in self.get('primary_key_col').split(',')])
            scores = [entry.get(self.get('score')) for entry in self.filter_entries(aggregate=False,
                                                                                    primary_key=primary_key)]
            for size in [float(s.strip()) for s in self.get('sizes').split(',')]:
                confidence_interval = self.get('confidence_interval', scores, ci_size=size, seed_value=self.get('seed_value'))
                self.get('confidence_intervals').get(primary_key_str, default=Container(logger)).add(key=str(size), value=confidence_interval)

    def get_score_header(self, header, score=None, sizes=None):
        if score is None and len(sizes) == 0:
            return header
        if score is not None:
            header.append(score)
            return self.get('score_header', header, score=None, sizes=sizes)
        else:
            size = sizes.pop()
            size_left = '{}%('.format(float(size)*100)
            size_right = '){}%'.format(float(size)*100)
            header.insert(0, size_left)
            header.append(size_right)
            return self.get('score_header', header, score=None, sizes=sizes)

    def get_header(self):
        header = self.get('score_header', [], 'score', self.get('sizes').split(','))
        header = [field_name for field_name in self.get('primary_key_col').split(',')] + header
        return header

    def get_format_spec(self, field_name):
        return 's' if field_name in self.get('primary_key_col').split(',') else '6.4f'

    def get_field_value(self, line, field_name):
        return line[field_name]

    def prepare_lines(self):
        self.lines = []
        # prepare lines
        for aggregate_entry in self.filter_entries(aggregate=True, primary_key=None):
            line = self.get('primary_key', aggregate_entry)
            primary_key_str = '.'.join([line[fn] for fn in self.get('primary_key_col').split(',')])
            line['score'] = float(aggregate_entry.get(self.get('score')))
            self.add_confidence_intervals(line, primary_key_str)
            self.get('lines').append(line)
        # prepare widths
        widths = self.get('widths')
        for field_name in self.get('header'):
            widths[field_name] = len(field_name)
            format_spec = self.get('format_spec', field_name)
            for line in self.get('lines'):
                value = self.get('field_value', line, field_name)
                text = '{0:{1}}'.format(value, 's' if value=='' else format_spec)
                line[field_name] = text
                widths[field_name] = len(text) if len(text)>widths[field_name] else widths[field_name]

    def add_confidence_intervals(self, line, primary_key_value):
        confidence_intervals = self.get('confidence_intervals').get(primary_key_value)
        for size in [float(s.strip()) for s in self.get('sizes').split(',')]:
            lower_key, upper_key = '{s}%('.format(s=size*100), '){s}%'.format(s=size*100)
            lower_value, upper_value = confidence_intervals.get(str(size))
            line[lower_key] = lower_value
            line[upper_key] = upper_value

    def get_header_text(self):
        return self.get('line_text')

    def get_justify(self, field_name):
        return 'L' if field_name in [self.get('primary_key_col').split(',')] else 'R'

    def get_line_text(self, line=None):
        text = ''
        separator = ''
        for field_name in self.get('header'):
            text += separator
            value = line.get(field_name) if line is not None else field_name
            num_spaces = 0 if self.separators[self.get('separator')] is not None else self.widths[field_name] - len(str(value))
            spaces_prefix = ' ' * num_spaces if self.get('justify', field_name) == 'R' and self.separators[self.get('separator')] is None else ''
            spaces_postfix = ' ' * num_spaces if self.get('justify', field_name) == 'L' and self.separators[self.get('separator')] is None else ''
            text = '{}{}{}{}'.format(text, spaces_prefix, value, spaces_postfix)
            separator = ' ' if self.separators[self.get('separator')] is None else self.separators[self.get('separator')]
        return text

    def get_output(self, separator):
        self.set('separator', separator)
        self.prepare_lines()
        string = self.get('header_text')
        for line in self.get('lines'):
            string = '{}\n{}'.format(string, self.get_line_text(line))
        return string