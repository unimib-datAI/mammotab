#!/bin/bash
NPROC=4

# create outlog folder
[ -d outlog_entity_titles ] || mkdir outlog_entity_titles

# run
ls enwiki-*.bz2 | \
    xargs -I {} -n 1 -P $NPROC bash -c 'python mammotab_entity_titles.py {} > outlog_entity_titles/{}.out 2> outlog_entity_titles/{}.err || echo failed {} >> fails.log'