import re
from collections import defaultdict

def add_entry(data, entry):
    metric = entry['metric']
    language = entry['language']
    metatype = entry['metatype']
    ci_size = entry['ci_size']
    subsample_size = entry['subsample_size']
    kendalltau_sci = entry['kendalltau_sci']
    data.setdefault(metatype, {})\
        .setdefault(language, {})\
        .setdefault(ci_size, {})\
        .setdefault(metric, {})[subsample_size] = kendalltau_sci

filename = 'sampling_study_output.txt'
lines = []
data = {}
with open(filename) as fh:
    header = None
    lineno = 1
    for line in fh.readlines():
        line = line.strip()
        if header is None:
            header = line.split()
            continue
        entry = dict(zip(header, line.split()))
        entry['line'] = line
        entry['where'] = {'filename': filename, 'lineno': lineno}
        add_entry(data, entry)
        lines.append(entry)
        lineno += 1
        
metatypess = """ArgumentMetricV1 Event
CoreferenceMetric Entity
CoreferenceMetric Event
FrameMetric Event
FrameMetric Relation
FrameMetric ALL
TemporalMetric Event
TemporalMetric Relation
TypeMetric Entity
TypeMetric Event"""

metatypes = {}
for line in metatypess.split('\n'):
    metric, event_or_relation = line.split()
    metatypes.setdefault(metric, []).append(event_or_relation)

languages = {
    'setting-1': ['ENG', 'ALL'],
    'setting-2': ['ENG', 'RUS', 'SPA', 'ALL']
    }

kendallstau_of_interest = [0.80, 0.85, 0.90]
for language_setting in languages:
    print('Results using {}'.format(language_setting))
    for metatype in data:
        for language in data[metatype]:
            if language not in languages[language_setting]: continue
            print('Language: {} Metatype: {} - 95% CI over Kendall\'s Tau'.format(language, metatype))
            for ci_size in data[metatype][language]:
                for metric in sorted(data[metatype][language][ci_size]):
                    if metric not in metatypes: continue
                    if metatype not in metatypes[metric]: continue
                    s = '  {:17}'.format(metric)
                    min_sample_sizes = {'{:0.2f}'.format(k):None for k in kendallstau_of_interest}
                    for subsample_size in sorted(data[metatype][language][ci_size][metric], key=int):
                        cis = data[metatype][language][ci_size][metric][subsample_size]
                        x = re.search(r"\d\d\%\((.*?),(.*?)\)", cis)
                        ci = [float(x.group(i)) for i in [1,2]]
                        for kendallstau in kendallstau_of_interest:
                            kendallstaus = '{:0.2f}'.format(kendallstau)
                            if min_sample_sizes[kendallstaus] is not None: continue
                            if ci[1] > kendallstau:
                                min_sample_sizes[kendallstaus] = subsample_size
                    for kendallstau in sorted(min_sample_sizes):
                        min_sample_size = min_sample_sizes[kendallstau]
                        s += ' {}:{}%'.format(int(float(kendallstau)*100), min_sample_size)
                    print(s)
                break
            print('')