all: git-pull generate-aif apply-queries clean-sparql-output verify

git-pull:
	cd aida/python/ && git pull && cd ../../
	cp aida/python/input/aux_data/log_specifications.txt /scripts/

generate-aif:
	cd aida/python/ && python3.9 generate_aif.py $$TASK --log /output/generate_aif.log /scripts/log_specifications.txt /scripts/data/encoding_modality.txt /scripts/data/parent_children.tsv /annotations /output/AIF

apply-queries:
	cp -r /scripts/queries/$$TASK /output/queries
	cd /scripts && python3.9 apply-queries.py $$TASK

clean-sparql-output:
	cd aida/python/ && python3.9 clean_sparql_output.py /scripts/log_specifications.txt /output/SPARQL-output /output/SPARQL-CLEAN-output

verify:
	cd aida/python/ && python3.9 verify_aif_against_annotations.py $$TASK --log /output/verify_aif.log /scripts/log_specifications.txt /scripts/data/encoding_modality.txt /scripts/data/parent_children.tsv /annotations /output/SPARQL-CLEAN-output
