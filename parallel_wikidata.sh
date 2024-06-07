#!/bin/bash
NPROC=5

# create outlog folder
[ -d outlog_wikidata ] || mkdir outlog_wikidata

# run
ls wiki_tables_filtered | \
    xargs -I {} -n 1 -P $NPROC bash -c 'python mammotab_wikidata.py wiki_tables_filtered {} wiki_tables_enriched > outlog_wikidata/{}.out 2> outlog_wikidata/{}.err || echo failed {} >> fails_wikidata.log'
