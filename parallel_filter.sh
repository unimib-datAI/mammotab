#!/bin/bash
NPROC=8

# create outlog folder
[ -d outlog_filter ] || mkdir outlog_filter

# run
ls wiki_tables | \
    xargs -I {} -n 1 -P $NPROC bash -c 'python mammotab_filter.py wiki_tables {} wiki_tables_filtered > outlog_filter/{}.out 2> outlog_filter/{}.err || echo failed {} >> fails_filter.log'
