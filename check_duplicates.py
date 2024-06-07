import pandas
import json
from glob import glob
import gzip
from tqdm import tqdm

file_list = glob('wiki_tables/*/*.json.gz')

tab_codes = []

for fname in tqdm(file_list):
    with gzip.open(fname, 'rt') as fd:
        diz_overall = json.load(fd)
    for tab in diz_overall['tables']:
        tab_codes.append(tab)

assert len(tab_codes) == len(set(tab_codes))
print('OK')

