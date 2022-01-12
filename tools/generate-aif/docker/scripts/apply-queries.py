from os import listdir, mkdir, system
from os.path import isfile, join

import sys

if len(sys.argv) != 2:
    print('Usage: python {} [task1|task2|task3]'.format(sys.argv[0]))
    exit()

task = sys.argv[1]
if task not in ['task1', 'task2', 'task3']:
    print('Error: unexpected task \'{}\''.format(task))
    exit()

AIF_dir = '/output/AIF/'
queries = '/output/queries/'
sparql_output = '/output/SPARQL-output'
graphdb_bin = '/opt/graphdb/dist/bin'
graphdb = '{}/graphdb'.format(graphdb_bin)
loadrdf = '{}/loadrdf'.format(graphdb_bin)
verdi = '/opt/sparql-evaluation'
jar = '{}/sparql-evaluation-1.0.0-SNAPSHOT-all.jar'.format(verdi)
config = '{}/config/Local-config.ttl'.format(verdi)
properties = '{}/config/Local-config.properties'.format(verdi)
intermediate = '{sparql_output}/intermediate'.format(sparql_output=sparql_output)

mkdir(sparql_output)

files = [f for f in listdir(AIF_dir) if isfile(join(AIF_dir, f))]
num_total = len(files)
count = 0
for filename in files:
    if not filename.endswith('.ttl'):
        continue
    if task == 'task1' and filename not in ['L0C04960U.ttl', 'L0C04936H.ttl', 'L0C0499MZ.ttl']:
        print('{filename} ... skipping'.format(filename=filename))
        continue
    count += 1
    print('Applying queries to {filename} ... {count} of {num_total}.'.format(count=count, num_total=num_total, filename=filename))
    mkdir(intermediate) 
    print('Loading {} into GraphDB.'.format(filename))
    input_kb = '{AIF_dir}/{filename}'.format(AIF_dir=AIF_dir, filename=filename)
    system('{loadrdf} -c {config} -f -m parallel {input_kb}'.format(loadrdf=loadrdf, config=config, input_kb=input_kb))
    print('Starting GraphDB')
    system('{graphdb} -d'.format(graphdb=graphdb))
    system('sleep 5')
    print('Applying queries')
    system('java -Xmx4096M -jar {jar} -c {properties} -q {queries} -o {intermediate}/'.format(jar=jar, properties=properties, queries=queries,intermediate=intermediate))
    print('Creating SPARQL output directory corresponding to the KB')
    mkdir('{sparql_output}/{filename}'.format(sparql_output=sparql_output, filename=filename))
    print('Moving output out of the intermediate directory')
    system('mv {intermediate}/*/* {output}/{filename}'.format(intermediate=intermediate, output=sparql_output, filename=filename))
    print('Removing the intermediate directory')
    system('rm -rf {}'.format(intermediate))
    print('Stopping GraphDB.')
    system('pkill -9 -f graphdb')

