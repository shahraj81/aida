import math
import os
import statistics
import numpy as np

from arch.bootstrap import IIDBootstrap
from scipy.stats import  kendalltau, pearsonr, spearmanr
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
    def __init__(self, metricname, filename, header_line, data_lineno, data_line):
        entry = dict(zip(header_line.split('\t'), data_line.split('\t')))
        entry['MetricName'] = metricname
        entry['where'] = {
            'filename': filename,
            'lineno': data_lineno
            }
        self.confidence_intervals = Container()
        for key, value in entry.items():
            if key.startswith(')'):
                size = key.split(')')[1]
                self.get('confidence_intervals').get(size, default=[None, None])[1]=value
            elif key.endswith('('):
                 size = key.split('(')[0]
                 self.get('confidence_intervals').get(size, default=[None, None])[0]=value
            else:
                self.set(key, value)
    def filter(self, ci_size):
        fields = ['MetricName', 'RunID', 'Language', 'Metatype']
        ci_size_percent = int(float(ci_size) * 100)
        fields.append('{}%('.format(ci_size_percent))
        fields.append('score')
        fields.append('){}%'.format(ci_size_percent))
        return [self.get(k) for k in fields]

class Scores(Container):
    def __init__(self, **kwargs):
        self.store = {}
        super().__init__(**kwargs)
        self.load(self.get('scores_dir'))
    def get_lines(self, filename):
        with open(filename) as fh:
            return [l.strip() for l in fh.readlines()]
    def fix(self, header):
        if header == 'RunID\tLanguage\tMetatype\t95.0%(\t90.0%(\t80.0%(\t70.0%(\tscore\t)70.0%\t)80.0%\t)90.0%\t)95.0%':
            header = 'RunID\tLanguage\tMetatype\t95%(\t90%(\t80%(\t70%(\tscore\t)70%\t)80%\t)90%\t)95%'
        return(header)
    def get_entries(self, metric_name, filename):
        entries = Container()
        header = None
        lineno = 0
        for line in self.get('lines', filename):
            lineno += 1
            if header is None:
                header = line
                if self.get('FIX_HEADER'):
                    header = self.fix(header)
            else:
                entries.add(key='{}:{}'.format(filename, lineno),
                            value=Entry(metric_name, filename, header, lineno, line))
                
        return entries
    def load_a_file(self, submission, metric_name, filename):
        self.get(submission, 
                 default=Container()).add(key=metric_name,
                                          value=self.get('entries', metric_name, filename))
    def load(self, scores_dir):
        for submission in os.listdir(scores_dir):
            if not os.path.isdir(os.path.join(scores_dir, submission)):
                continue
            submission_scores = '{}/scores'.format(submission)
            submission_scores_dir = os.path.join(scores_dir, submission_scores)
            for metric_ci in os.listdir(submission_scores_dir):
                if metric_ci.endswith('-ci.tab'):
                    metric_name = metric_ci.split('-ci.tab')[0]
                    submission_metric_score_filename = os.path.join(submission_scores_dir, metric_ci)
                    self.load_a_file(submission, metric_name, submission_metric_score_filename)

class Rankings(Container):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.load()
    def get_parsed_entries(self, entry):
        lookup = {
            'runid': lambda e: e.get('RunID'),
            'metric': lambda e: e.get('MetricName'),
            'language': lambda e: e.get('Language'),
            'metatype': lambda e: e.get('Metatype'),
            }
        parsed_entries = []
        for ci_size in entry.get('confidence_intervals'):
            parsed_entry = Object()
            parsed_entry.set('confidence_interval', tuple(entry.get('confidence_intervals').get(ci_size))),
            parsed_entry.set('confidence_interval_size', ci_size)
            parsed_entry.set('score', entry.get('score'))
            for field_name in 'runid,metric,language,metatype'.split(','):
                parsed_entry.set(field_name, lookup[field_name](entry))
            parsed_entries.append(parsed_entry)
        return parsed_entries
    def load(self):
        for submission in self.get('scores'):
            for metric in self.get('scores').get(submission):
                for entry in self.get('scores').get(submission).get(metric).values():
                    for parsed_entry in self.get('parsed_entries', entry):
                        key = '::'.join([parsed_entry.get(k) for k in self.get('group_by').split('::')])
                        self.get(key, default=Container()).add(parsed_entry)
        for key in self:
            rank = 0
            for entry in sorted(self.get(key).values(), key=lambda e: e.get('score'), reverse=True):
                rank += 1
                entry.set('rank', rank)

def get_correlations(sample_ranking, official_ranking):
    scores = {}
    rankings = {'sample': sample_ranking, 'official': official_ranking}
    for ranking_name in rankings:
        for entry in rankings[ranking_name].values():
            runid = entry.get('runid')
            score = entry.get('score')
            if runid not in scores:
                scores[runid] = {}
            scores[runid][ranking_name] = float(score)
    lists = {'sample': [], 'official': []}
    for runid in scores:
        for ranking_name in scores[runid]:
            lists[ranking_name].append(scores[runid][ranking_name])
    methods = {'kendalltau':kendalltau, 'pearsonr':pearsonr, 'spearmanr':spearmanr}
    correlations = {}
    for method in methods:
        correlations[method], _ = methods[method](lists['sample'], lists['official'])
    return correlations

def get_significant_differences_score(rankings, topk = None):
    def is_significantly_different(entry1, entry2):
        def get_linear_overlap(start1, end1, start2, end2, text_modality=False):
            s1 = float(start1)
            e1 = float(end1)
            s2 = float(start2)
            e2 = float(end2)
            overlap = 0
            if s2 <= s1 <= e2 or s2 <= e1 <= e2 or s1 <= s2 <= e1 or s1 <= e2 <= e1:
                overlap = min(e1, e2) - max(s1, s2)
            return overlap
        ci1 = entry1.get('confidence_interval')
        ci2 = entry2.get('confidence_interval')
        if get_linear_overlap(ci1[0], ci1[1], ci2[0], ci2[1]) > 0:
            return False
        return True
    if topk is None:
        topk = len(rankings)
    num_total_pairs = 0
    num_significantly_different_pairs = 0
    for entry1 in rankings.values():
        rank1 = entry1.get('rank')
        for entry2 in rankings.values():
            rank2 = entry2.get('rank')
            if rank1 <= topk and rank2 <= topk and rank1 < rank2:
                num_total_pairs += 1
                if is_significantly_different(entry1, entry2):
                    num_significantly_different_pairs += 1
    return num_significantly_different_pairs/num_total_pairs if num_total_pairs > 0 else 0

def get_stats(scores_container):
    def get_confidence_interval(scores, ci_method='bca', ci_size=0.95, replications=100000, seed_value=None):
        """
        Compute two sided bootstrap confidence interval
        """
        def score(x):
            return np.array([x.mean()])
        data = np.array([float(score) for score in scores])
        if min(data) == max(data):
            return {'size': ci_size, 'lower': min(data), 'upper': max(data)}
        bs = IIDBootstrap(data)
        if seed_value is not None:
            bs.seed(seed_value)
        ci = bs.conf_int(score, replications, method=ci_method, size=ci_size, tail='two')
        return {'size': ci_size, 'lower': ci[0][0], 'upper': ci[1][0]}
    def mean(data):
        """Return the sample arithmetic mean of data."""
        n = len(data)
        if n < 1:
            raise ValueError('mean requires at least one data point')
        return sum(data)/n
    score_lists = {}
    for score in scores_container.values():
        for score_name in score:
            if score_name not in score_lists:
                score_lists[score_name] = []
            score_lists[score_name].append(score[score_name])
    methods = {
        'min': lambda s: min(s),
        'max': lambda s: max(s),
        'mean': lambda s: mean(s),
        'median': lambda s: statistics.median(s),
        'stdev': lambda s: statistics.stdev(s),
        'variance': lambda s: statistics.stdev(s),
        'ci': lambda s: get_confidence_interval(s),
        }
    stats = {}
    for score_name in score_lists:
        stats[score_name] = {}
        scores = score_lists[score_name]
        for method in methods:
            stats[score_name][method] = methods[method](scores)
    return stats

# number of top system to be considered for study
topk = 8

group_by = 'confidence_interval_size::metric::language::metatype'

## BEGIN
# load data to support generating rank correlation between:
#   subsample-rankings and official rankings

official_scores_dir = '../initial/scores'
official_scores = Scores(scores_dir=official_scores_dir, FIX_HEADER=True)
official_rankings = Rankings(scores=official_scores, group_by=group_by)
## END

sd_scores = Container()
samples_scores_dir = './sample_scores'
for sample_id in sorted(os.listdir(samples_scores_dir)):
    sample_size, sample_num = sample_id.split('-')
    sample_score_dir = os.path.join(samples_scores_dir, sample_id)
    scores = Scores(scores_dir=sample_score_dir)
    rankings = Rankings(scores=scores, group_by=group_by)
    if len(rankings) == 0: continue
    grouped_rankings = Container()
    for key in rankings:
        ranking = rankings.get(key)
        confidence_interval_size, metric, language, metatype = key.split('::')
        grouped_rankings.get(confidence_interval_size, default=Container()) \
            .get(metric, default=Container()) \
            .get(language, default=Container()).add(key=metatype, value=ranking)
    rows = ['ALL', 'ENG', 'SPA', 'RUS']
    columns = ['ALL', 'Event', 'Relation', 'Entity']
    num_rows, num_columns = 4, 3
    for confidence_interval_size in grouped_rankings:
        ci_rankings = grouped_rankings.get(confidence_interval_size)
        for metric in ci_rankings:
            metric_rankings = ci_rankings.get(metric)
            for row_idx in range(num_rows):
                language = rows[row_idx]
                language_rankings = metric_rankings.get(language)
                col_idx = 0
                for metatype in columns:
                    if metatype not in language_rankings:
                        continue
                    ranking = language_rankings.get(metatype)
                    official_ranking = official_rankings.get('::'.join([confidence_interval_size,
                                                                        metric,
                                                                        language,
                                                                        metatype]))
                    sample_stats = get_correlations(ranking, official_ranking)
                    sample_stats['sd_score'] = get_significant_differences_score(ranking, topk=topk)
                    sd_scores.get(language, default=Container()) \
                        .get(metatype, default=Container()) \
                        .get(metric, default=Container()) \
                        .get(confidence_interval_size, default=Container()) \
                        .get(sample_size, default=Container()) \
                            .add(key=sample_num, value=sample_stats)

program_output = open('sampling_study_output.txt', 'w')
entire_sample_significant_differences_filename = '../initial/significant_difference.txt'
header = None
with open(entire_sample_significant_differences_filename) as fh:
    for line in fh.readlines():
        line = line.strip()
        if header is None:
            header = line
        else:
            metric, language, metatype, confidence_interval_size, sd_score = line.split()
            subsample_sd_scores = sd_scores.get(language).get(metatype).get(metric).get(confidence_interval_size)
            for subsample_size in subsample_sd_scores:
                subsample_sd_scores_stats = get_stats(subsample_sd_scores.get(subsample_size))
                output_dict = {
                    'metric': metric,
                    'language': language,
                    'metatype': metatype,
                    'ci_size': confidence_interval_size,
                    'sd_score': sd_score,
                    'subsample_size': subsample_size
                    }
                header = list(output_dict.keys())
                stats_submetrics = ['min', 'max', 'mean', 'median', 'stdev', 'variance']
                for submetric_name in subsample_sd_scores_stats:
                    for stats_submetric in stats_submetrics:
                        key = '{}_{}'.format(submetric_name, stats_submetric)
                        header.append(key)
                        output_dict[key] = subsample_sd_scores_stats[submetric_name][stats_submetric]
                    key = '{}_sci'.format(submetric_name)
                    header.append(key)
                    output_dict[key] = '{sci_size}%({lower}.{upper})'.format(
                        sci_size=int(subsample_sd_scores_stats[submetric_name]['ci']['size']*100),
                        lower='{:0.1f}'.format(subsample_sd_scores_stats[submetric_name]['ci']['lower']*100),
                        upper='{:0.1f}'.format(subsample_sd_scores_stats[submetric_name]['ci']['upper']*100)
                        )
                output = ''
                for key in header:
                    if output != '':
                        output = output + ' '
                    output = output + '{' + '{}'.format(key) + '}'
                output = output.format(**output_dict)
                print(output)
                program_output.write(output)
program_output.close()