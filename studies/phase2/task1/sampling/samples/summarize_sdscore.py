from math import ceil

import re

def add_entry(data, entry):
    metric = entry['metric']
    language = entry['language']
    metatype = entry['metatype']
    ci_size = entry['ci_size']
    subsample_size = entry['subsample_size']
    sdscore = float(entry['sdscore'])
    x = re.search(r"\d\d\%\((.*?),(.*?)\)", entry['sdscore_sci'])
    sdscore_sci = [float(x.group(i)) for i in [1,2]]
    drop = int((10000*(sdscore - sdscore_sci[1])/sdscore))/100 if sdscore else 'NAN'
    data.setdefault(metatype, {})\
        .setdefault(language, {})\
        .setdefault(ci_size, {})\
        .setdefault(metric, {})[subsample_size] = drop

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

max_drop_by_subsample_size = {}

for language_setting in languages:
    print('Results using {}'.format(language_setting))
    for metatype in data:
        for language in data[metatype]:
            if language not in languages[language_setting]: continue
            for ci_size in data[metatype][language]:
                print('Language: {} Metatype: {} - {} CI over Score - 95% CI over SD'.format(language, metatype, ci_size))
                for metric in sorted(data[metatype][language][ci_size]):
                    if metric not in metatypes: continue
                    if metatype not in metatypes[metric]: continue
                    s = '  {:17}'.format(metric)
                    for subsample_size in sorted(data[metatype][language][ci_size][metric], key=int):
                        drop = data[metatype][language][ci_size][metric][subsample_size]
                        if drop != 'NAN':
                            if subsample_size not in max_drop_by_subsample_size:
                                max_drop_by_subsample_size[subsample_size] = ceil(drop)
                            else:
                                if max_drop_by_subsample_size[subsample_size] < ceil(drop):
                                    max_drop_by_subsample_size[subsample_size] = ceil(drop)
                        s += ' {}:{}'.format(subsample_size, drop)
                    print(s)
            print('')


for subsample_size in max_drop_by_subsample_size:
    print('subsample:{} drop:{}'.format(subsample_size, max_drop_by_subsample_size[subsample_size]))