import numpy as np
import os
import json
import matplotlib.pyplot as plt

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

group_by = 'confidence_interval_size::metric::language::metatype'
scores = Scores(scores_dir='./scores', FIX_HEADER=True)
rankings = Rankings(scores=scores, group_by=group_by)

program_output = open('rankings.txt', 'w')
header = ['score', 'confidence_interval', 'runid']
header.extend(group_by.split('::'))
program_output.write('{}\n'.format(' '.join(header)))
output = []
for key in rankings:
    ranking = {}
    for k,v in dict(zip(group_by.split('::'), key.split('::'))).items():
        #program_output.write('{:25}: {}\n'.format(k, v))
        ranking[k] = v
    ranking['ranking'] = {}
    rank = 0
    for entry in sorted(rankings.get(key).values(), key=lambda e: e.get('score'), reverse=True):
        rank += 1
        runid = entry.get('runid')
        score = entry.get('score')
        confidence_interval = '[{}]'.format(','.join(entry.get('confidence_interval')))
        ranking['ranking'][str(rank)] = {
            'runid': entry.get('runid'),
            'score': entry.get('score'),
            'confidence_interval': entry.get('confidence_interval')
            }
        program_output.write('{rank} {score} {confidence_interval} {runid} {group_by}\n'.format(rank=str(rank),
                                                                                                score=score,
                                                                                                confidence_interval=confidence_interval,
                                                                                                runid=runid,
                                                                                                group_by=' '.join(key.split('::'))))
        output.append(ranking)
program_output.close()

with open('rankings.json', 'w') as program_output: 
    program_output.write(json.dumps(output, indent = 4))

# generate plots
grouped_rankings = Container()
for key in rankings:
    ranking = rankings.get(key)
    confidence_interval_size, metric, language, metatype = key.split('::')
    grouped_rankings.get(confidence_interval_size, default=Container()) \
        .get(metric, default=Container()) \
        .get(language, default=Container()).add(key=metatype, value=ranking)

program_output = open('significant_difference.txt', 'w') 
program_output.write('{metric:17} {language:8} {metatype:8} {confidence_interval_size:>7} {num_significant_differences:>8}\n'.format(metric='metric',
                                                                                language='language',
                                                                                metatype='metatype',
                                                                                confidence_interval_size='ci_size',
                                                                                num_significant_differences='sd_score'))
sd_scores = Container()
rows = ['ALL', 'ENG', 'SPA', 'RUS']
columns = ['ALL', 'Event', 'Relation', 'Entity']
num_rows, num_columns = 4, 3
for confidence_interval_size in grouped_rankings:
    ci_rankings = grouped_rankings.get(confidence_interval_size)
    for metric in ci_rankings:
        metric_rankings = ci_rankings.get(metric)
        suptitle = '{} - {} CI'.format(metric, confidence_interval_size)
        fig = plt.figure()
        fig.text(0.5, 0.04, 'runs', ha='center')
        fig.text(0.04, 0.5, 'scores', va='center', rotation='vertical')
        gs = fig.add_gridspec(num_rows, num_columns, hspace=0.4, wspace=0.1)
        axs = gs.subplots(sharex='col', sharey='row')
        fig.suptitle(suptitle, fontsize=10)
        for row_idx in range(num_rows):
            language = rows[row_idx]
            language_rankings = metric_rankings.get(language)
            col_idx = 0
            for metatype in columns:
                if metatype not in language_rankings:
                    continue
                ranking = language_rankings.get(metatype)
                sd_score = get_significant_differences_score(ranking, topk=8)
                sd_scores.get(language, default=Container()) \
                    .get(metatype, default=Container()) \
                    .get(metric, default=Container()).add(key=confidence_interval_size, value=sd_score)
                program_output.write('{metric:17} {language:8} {metatype:8} {confidence_interval_size:>7} {sd_score:>8}\n'.format(metric=metric,
                                                                                language=language,
                                                                                metatype=metatype,
                                                                                confidence_interval_size=confidence_interval_size,
                                                                                #sd_score='{:0.4f}'.format(sd_score)))
                                                                                sd_score='{:>8}'.format(int(round(sd_score*100)))))
                ranks = []
                scores = []
                runids = []
                lower_errors = []
                upper_errors = []
                for entry in sorted(ranking.values(), key=lambda e: e.get('rank')):
                    rank = entry.get('rank')
                    score = float(entry.get('score'))
                    runid = entry.get('runid')
                    lower_error = score - float(entry.get('confidence_interval')[0])
                    upper_error = float(entry.get('confidence_interval')[1]) - score
                    ranks.append(rank)
                    scores.append(score)
                    runids.append(runid)
                    lower_errors.append(lower_error)
                    upper_errors.append(upper_error)
                asymmetric_errors = [lower_errors, upper_errors]
                axs[row_idx, col_idx].errorbar(ranks, scores, yerr=asymmetric_errors, capsize=2, fmt='.', ms=1)
                axs[row_idx, col_idx].set_title('Language: {} Metatype: {}'.format(language, metatype), fontsize=5)
                axs[row_idx, col_idx].set_xticks([])
                yticks = axs[row_idx, col_idx].get_yticks()
                axs[row_idx, col_idx].tick_params(axis='y', labelsize=5)
                col_idx += 1
        for ax in axs.flat:
            ax.label_outer()
        plt.savefig('plots/{}_{}.pdf'.format(metric, confidence_interval_size))
        plt.close()
program_output.close()

data = sd_scores.to_dict()

with open('sd_scores.json', 'w') as program_output: 
    program_output.write(json.dumps(data, indent = 4))

width = 0.75
for language in data:
    for metatype in data[language]:
        labels = [metric for metric in sorted(data[language][metatype])]
        sd_scores = {}
        for ci_value in ['95%', '90%', '80%', '70%']:
            sd_scores[ci_value] = []
            for metric in sorted(data[language][metatype]):
                sd_value = data[language][metatype][metric][ci_value]
                sd_scores[ci_value].append(sd_value)
        x = np.array([i*6 for i in range(len(labels))])
        fig, ax = plt.subplots()
        increment = 1
        i = -1.5
        for ci_value in ['95%', '90%', '80%', '70%']:
            ax.bar(x + i, sd_scores[ci_value], width, label=ci_value)
            i += increment
        ax.set_ylabel('Significant Differences')
        ax.set_xlabel('Metrics')
        ax.set_title('{} - {}'.format(language, metatype))
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=30)
        ax.tick_params(axis='x', labelsize=8)
        ax.tick_params(axis='y', labelsize=8)
        ax.legend()
        plt.gcf().subplots_adjust(bottom=0.20)
        plt.savefig('significant_difference_plots/{}_{}.pdf'.format(language, metatype))
        plt.close()
