#!/bin/bash
NPROC=4

# create outlog folder
[ -d outlog ] || mkdir outlog

# run
ls enwiki-*.bz2 | \
    xargs -I {} -n 1 -P $NPROC bash -c 'python mammotab_v3.py {} > outlog/{}.out 2> outlog/{}.err || echo failed {} >> fails.log'
