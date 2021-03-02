"""
AIDA class for bootstrap resampling based two-sided BCA confidence intervals.
"""
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
    def __init__(self, logger, run_id, metric_name, scores, seed_value=None):
        super().__init__(logger)
        self.run_id = run_id
        self.metric_name = metric_name
        self.confidence_intervals = {}
        self.scores = scores
        self.seed_value = seed_value
        self.compute_confidence_intervals()

    def compute_confidence_intervals(self):
        spec = self.get('spec', self.get('metric_name'))
        if spec is None:
            self.record_event('MISSING_ENTRY_IN_LOOKUP_ERROR', 'spec', self.get('metric_name'), self.get('code_location'))
            return
        scores = {}
        for score in self.get('scores').values():
            if score.get('summary'): continue
            group_by = '.'.join([score.get(field_name) for field_name in spec.get('group_by')])
            if group_by not in scores:
                scores[group_by] = {}
            scores[group_by][score.get(spec.get('key'))] = score.get(spec.get('confidence_over'))
        for group_by in scores:
            self.get('confidence_intervals')[group_by] = {}
            for size in [0.90, 0.95, 0.99]:
                self.get('confidence_intervals')[group_by][size] = self.get('confidence_interval',
                                                                            scores=scores[group_by],
                                                                            ci_size=size,
                                                                            seed_value=self.get('seed_value'))

    def get_confidence_interval(self, scores, ci_method='bca', ci_tail='two', ci_size=0.95, seed_value=None):
        def score(x):
            return np.array([x.mean()])
        data = np.array(list(scores.values()))
        if min(data) == max(data):
            return {'lower': '{:0.4f}'.format(min(data)), 'upper': '{:0.4f}'.format(max(data))}
        bs = IIDBootstrap(data)
        if seed_value is not None:
            bs.seed(seed_value)
        ci = bs.conf_int(score, 1000, method=ci_method, size=ci_size, tail=ci_tail)
        confidence_interval = {'lower': '{:0.4f}'.format(ci[0][0]), 'upper': '{:0.4f}'.format(ci[1][0])} 
        return confidence_interval

    def get_spec(self, metric_name):
        specs = {
            'ArgumentMetricScorerV1': {
                'key': 'document_id',
                'group_by': ['language', 'metatype'],
                'confidence_over': 'f1',
                'header': ['RunID', 'Language', 'Metatype'],
                'justify': {'RunID':'L', 'Language':'L', 'Metatype':'L'},
                },
            'ArgumentMetricScorerV2': {
                'key': 'document_id',
                'group_by': ['language', 'metatype'],
                'confidence_over': 'f1',
                'header': ['RunID', 'Language', 'Metatype'],
                'justify': {'RunID':'L', 'Language':'L', 'Metatype':'L'},
                },
            'CoreferenceMetricScorer': {
                'key': 'document_id',
                'group_by': ['language', 'metatype'],
                'confidence_over': 'f1',
                'header': ['RunID', 'Language', 'Metatype'],
                'justify': {'RunID':'L', 'Language':'L', 'Metatype':'L'},
                },
            'FrameMetricScorer': {
                'key': 'document_id',
                'group_by': ['language', 'metatype'],
                'confidence_over': 'f1',
                'header': ['RunID', 'Language', 'Metatype'],
                'justify': {'RunID':'L', 'Language':'L', 'Metatype':'L'},
                },
            'TemporalMetricScorer': {
                'key': 'document_id',
                'group_by': ['language', 'metatype'],
                'confidence_over': 'similarity',
                'header': ['RunID', 'Language', 'Metatype'],
                'justify': {'RunID':'L', 'Language':'L', 'Metatype':'L'},
                },
            'TypeMetricScorerV1': {
                'key': 'document_id',
                'group_by': ['language', 'metatype'],
                'confidence_over': 'f1',
                'header': ['RunID', 'Language', 'Metatype'],
                'justify': {'RunID':'L', 'Language':'L', 'Metatype':'L'},
                },
            'TypeMetricScorerV2': {
                'key': 'document_id',
                'group_by': ['language', 'metatype'],
                'confidence_over': 'average_precision',
                'header': ['RunID', 'Language', 'Metatype'],
                'justify': {'RunID':'L', 'Language':'L', 'Metatype':'L'},
                },
            'TypeMetricScorerV3': {
                'key': 'document_id',
                'group_by': ['language', 'metatype'],
                'confidence_over': 'average_precision',
                'header': ['RunID', 'Language', 'Metatype'],
                'justify': {'RunID':'L', 'Language':'L', 'Metatype':'L'},
                },
            }
        return specs[metric_name] if metric_name in specs else None

    def __str__(self):
        def get_widths(header, lines):
            widths = {}
            for column_name in header:
                if column_name not in widths:
                    widths[column_name] = len(column_name)
                for line in lines:
                    value = line[column_name]
                    if len(value) > widths[column_name]:
                        widths[column_name] = len(value)
            return widths
        def get_line(widths, header, justify, line=None):
            text = ''
            for field_name in header:
                value = field_name if line is None else line[field_name]
                num_spaces = widths[field_name] - len(str(value)) + 1
                spaces_prefix = ' ' * num_spaces if justify[field_name] == 'R' else ''
                spaces_postfix = ' ' * num_spaces if justify[field_name] == 'L' else ''
                text = '{}{}{}{}'.format(text, spaces_prefix, value, spaces_postfix)
            return text
        def order(line):
            language = line.get('Language')
            metatype = '_ALL' if line.get('Metatype') == 'ALL' else line.get('Metatype')
            return '{language}:{metatype}'.format(metatype=metatype, language=language)
        retVal = ''
        spec = self.get('spec', self.get('metric_name'))
        if spec is None:
            self.record_event('MISSING_ENTRY_IN_LOOKUP_ERROR', 'spec', self.get('metric_name'), self.get('code_location'))
            return retVal
        ci_sizes = ['90%(', '95%(', '99%(', ')99%', ')95%', ')90%']
        justify = spec['justify']
        header = spec['header']
        header.extend(ci_sizes)
        lines = []
        for group_by in self.get('confidence_intervals'):
            line = {
                header[0]: self.get('run_id'),
                header[1]: group_by.split('.')[0],
                header[2]: group_by.split('.')[1]
                }
            for size in self.get('confidence_intervals')[group_by]:
                line['{size}%('.format(size=int(size*100))] = self.get('confidence_intervals')[group_by][size]['lower']
                line['){size}%'.format(size=int(size*100))] = self.get('confidence_intervals')[group_by][size]['upper']
                justify['{size}%('.format(size=int(size*100))] = 'R'
                justify['){size}%'.format(size=int(size*100))] = 'R'
            lines.append(line)
        widths = get_widths(header, lines)
        retVal = get_line(widths, header, justify)
        for line in sorted(lines, key=order):
            retVal = '{}\n{}'.format(retVal, get_line(widths, header, justify, line))
        return retVal