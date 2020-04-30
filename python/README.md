# Python scripts in support of the AIDA program

This document describes the usage of the following scripts written in support of the AIDA program:

* [The AIF Generator](#the-aif-generator)
* [Revision History](#revision-history)

NOTE: The scripts require python3 for execution.

Refer to the sections corresponding to these scripts below for details.

# The AIF Generator

The AIF Generator script can be used to convert annotations into AIF.

This section is divided into the following parts:

* [The Usage of the AIF Generator](#the-usage-of-the-aif-generator)
* [Files needed to run the AIF Generator](#files-needed-to-run-the-aif-generator)
* [How to run the AIF Generator](#how-to-run-the-aif-generator)

## The Usage of the AIF Generator

The usage of the AIF generator can be seen by running it with the switch -h. 

~~~
python3 generate_aif.py -h
~~~

For the record, the usage of the script is given below:

~~~
usage: generate_aif.py [-h] [-l LOG] [-v] [-r REFERENCE_KB_ID] [-t] [-n]
                       log_specifications_filename encodings_filename
                       core_documents_filename parent_children_filename
                       sentence_boundaries_filename image_boundaries_filename
                       video_boundaries_filename keyframe_boundaries_filename
                       type_mappings_filename slot_mappings_filename
                       annotations_dir output_dir

Generate AIF

positional arguments:
  log_specifications_filename
                        File containing error specifications
  encodings_filename    File containing list of encoding to modality mappings
  core_documents_filename
                        File containing list of core documents to be included
                        in the pool
  parent_children_filename
                        DocumentID to DocumentElementID mappings file
  sentence_boundaries_filename
                        File containing sentence boundaries
  image_boundaries_filename
                        File containing image bounding boxes
  video_boundaries_filename
                        File containing length of videos
  keyframe_boundaries_filename
                        File containing keyframe bounding boxes
  type_mappings_filename
                        File containing type mappings
  slot_mappings_filename
                        File containing slot mappings
  annotations_dir       Directory containing annotations package as received
                        from LDC
  output_dir            Specify a directory to which output should be written

optional arguments:
  -h, --help            show this help message and exit
  -l LOG, --log LOG     Specify a file to which log output should be
                        redirected (default: log.txt)
  -v, --version         Print version number and exit
  -r REFERENCE_KB_ID, --reference_kb_id REFERENCE_KB_ID
                        Specify the reference KB ID (default: LDC2019E44)
  -t, --notime          Do not read time-offset based spans from video
                        annotations (default: True)
  -n, --nochannel       Omit generating optional channel attribute in video
                        justification? (default: True)
~~~

## Files needed to run the AIF Generator 

The following table lists the files that correspond to the arguments of the AIF Generator:

| Argument                     | File                    |
| -----------------------------|-------------------------|
| log_specifications_filename  | input/aux-data/log_specifications.txt |
| encodings_filename           | input/aux-data/encoding_modality.txt |
| core_documents_filename      | input/aux-data/LDC2019E42.coredocs-all.txt |
| parent_children_filename     | input/aux-data/LDC2019E42.parent_children.tsv |
| sentence_boundaries_filename | input/aux-data/LDC2019E42.sentence_boundaries.txt |
| image_boundaries_filename    | input/aux-data/LDC2019E42.image_boundaries.txt |
| video_boundaries_filename    | input/aux-data/LDC2019E42.video_boundaries.txt |
| keyframe_boundaries_filename | input/aux-data/LDC2019E42.keyframe_boundaries.txt |
| type_mappings_filename       | input/aux-data/type_mappings.txt |
| slot_mappings_filename       | input/aux-data/slotname_mappings.txt |

## How to run the AIF Generator

In order to run the AIF Generator, you may run the following command:

~~~
python3 generate_aif.py --log logs/generate_aif.log \
  --notime \
  --nochannel \
  input/aux_data/log_specifications.txt \
  input/aux_data/encoding_modality.txt \
  input/aux_data/LDC2019E42.coredocs-all.txt \
  input/aux_data/LDC2019E42.parent_children.tsv \
  input/aux_data/LDC2019E42.sentence_boundaries.txt \
  input/aux_data/LDC2019E42.image_boundaries.txt \
  input/aux_data/LDC2019E42.video_boundaries.txt \
  input/aux_data/LDC2019E42.keyframe_boundaries.txt \
  input/aux_data/type_mappings.txt \
  input/aux_data/slotname_mappings.txt \
  /path/to/annotation/package \
  /path/to/output
~~~

[top](#python-scripts-in-support-of-the-aida-program)

# Revision History

## 04/30/2020:
* Added the README file
* Added the section on the AIF Generator

[top](#python-scripts-in-support-of-the-aida-program)
