#!/usr/bin/env python
# coding: utf-8
# +

from tqdm import tqdm
import gzip
import os
import json
import sys
from pprint import pprint
import csv

diz_overall = {}

i=0

base_folder = sys.argv[1]

for folder_name in tqdm(os.listdir(base_folder)):
    for f_name in tqdm(os.listdir(os.path.join(base_folder, folder_name))):
        if 'diz_' in f_name:
            with gzip.open(os.path.join(base_folder, folder_name, f_name), 'rb') as f:
                diz = json.load(f)
                diz_overall[i] = diz
                i+=1


n_tables = 0
cells = 0
rows = 0
cols = 0
links = 0
mentions = 0
nils = 0
types = 0 # number of cells with at least a type
col_types = 0 # number of columns with at least a type
col_types_perfect = 0 # number of columns with at least a perfect type
headers = 0 # number of headers rows
headers_yn = 0 # number of tables with headers

all_entities = set()

max_rows = 0
max_cols = 0
min_rows = sys.maxsize
min_cols = sys.maxsize

csvtables = gzip.open('mammostats_per_table.csv.gz', 'wt')
csvwriter = csv.writer(csvtables, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
csvwriter.writerow(['pageid', 'page_title', 'table', 'current_rows', 'current_cols', 'current_cells', 'current_headers',
    'current_links', 'current_mentions', 'current_nils', 'current_types', 'current_col_types',
    'current_col_types_perfect'])

for i in tqdm(diz_overall):
    tables = diz_overall[i]['tables']
    for tab in tables:

        n_tables+=1
        header_mat = tables[tab]['header']
        text_mat = tables[tab]['text']
        link_mat = tables[tab]['link']
        entity_mat = tables[tab]['entity']
        types_mat = tables[tab]['types']
        col_types_mat = tables[tab]['col_types']
        col_types_perfect_mat = tables[tab]['col_type_perfect']

        current_rows = len(text_mat)
        current_cols = len(text_mat[0])
        current_cells = len(text_mat)*len(text_mat[0])
        current_headers = len(header_mat)

        current_links  = sum(1 for row in link_mat for cell in row if cell)
        current_mentions  = sum(1 for row in entity_mat for cell in row if cell)
        current_nils  = sum(1 for row in entity_mat for cell in row if cell == 'NIL')
        current_types  = sum(1 for row in types_mat for cell in row if cell)
        current_col_types  = sum(1 for col in col_types_mat if col)
        current_col_types_perfect  = sum(1 for col in col_types_perfect_mat if col)

        csvwriter.writerow([
            diz_overall[i]['wiki_id'], diz_overall[i]['title'], tab,
            current_rows, current_cols, current_cells, current_headers,
            current_links, current_mentions, current_nils, current_types,
            current_col_types, current_col_types_perfect
            ])

        rows += current_rows
        cols += current_cols
        cells += current_cells
        headers += current_headers
        headers_yn += int(current_headers > 0)

        links += current_links
        mentions += current_mentions
        nils += current_nils
        types += current_types
        col_types += current_col_types
        col_types_perfect += current_col_types_perfect

        max_rows = max(max_rows, len(text_mat))
        max_cols = max(max_cols, len(text_mat[0]))
        min_rows = min(min_rows, len(text_mat))
        min_cols = min(min_cols, len(text_mat[0]))

        # all_entities = all_entities.union(set([cell for row in entity_mat for cell in row if cell.startswith('Q')]))

csvtables.close()

ultimate_stats = {
        'n_tables' : n_tables,
        'cells' : cells,
        'rows' : rows,
        'cols' : cols,
        'links' : links,
        "mentions": mentions, # mentions
        "nils": nils,
        "types": types,
        "col_types": col_types,
        "col_types_perfect": col_types_perfect,
        # "all_entities": len(all_entities) # entities,
        "max_rows": max_rows,
        "max_cols": max_cols,
        "min_rows": min_rows,
        "min_cols": min_cols,
        "headers": headers,
        "headers_yn": headers_yn
    }

pprint(ultimate_stats)

with open('mammostats.json', 'w') as fd:
    json.dump(ultimate_stats, fd)
