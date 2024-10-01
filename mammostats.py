#!/usr/bin/env python
# coding: utf-8
# +

from tqdm import tqdm
import gzip
import os
import json
import sys
from pprint import pprint

base_folder = sys.argv[1]

stats = {
    'n_tables': 0,
    'max_rows' : 0, 
    'max_cols' : 0,
    'min_rows' : sys.maxsize,
    'min_cols' : sys.maxsize,
    'ne_cols' : 0,
    'lit_cols' : 0,
    'cells': 0,
    'rows': 0,
    'cols' : 0,
    'nils' : 0,
    }
""" 'count_with_header': 0,
    'count_with_caption': 0,
    'acro_added': 0,
    'typos_added': 0,
    'approx_added': 0,
    'alias_added': 0,
    'generic_types': 0,
    'specific_types': 0,
    'count_single_domain': 0,
    'count_multi_domain': 0 """

for folder_name in tqdm(os.listdir(base_folder)):
    folder_path = os.path.join(base_folder, folder_name)
    if os.path.isdir(folder_path):
        for f_name in tqdm(os.listdir(folder_path)):
            if 'diz_' in f_name and f_name.endswith('.json.gz'):
                with gzip.open(os.path.join(folder_path, f_name), 'rb') as f:
                    diz = json.load(f)
                    for tab in diz['tables']:
                        stats['n_tables'] += 1
                        ttags = diz['tables'][tab]['tags']
                        tstats = diz['tables'][tab]['stats']
                        rows = len(diz['tables'][tab]['link'])
                        cols = len(diz['tables'][tab]['link'][0])
                        stats['rows'] += rows
                        stats['cols'] += cols
                        if rows > stats['max_rows']:
                            stats['max_rows'] = rows
                        if cols > stats['max_cols']:
                            stats['max_cols'] = cols
                        if rows < stats['min_rows']:
                            stats['min_rows'] = rows
                        if cols < stats['min_cols']:
                            stats['min_cols'] = cols

                        stats['cells'] += tstats['tot_cells']
                        stats['nils'] += tstats['nils']

                        for col in ttags:
                            if isinstance(ttags[col], dict) and 'tags' in ttags[col]:
                                if ttags[col]['tags'].get('col_type') == 'LIT':
                                    stats['lit_cols'] += 1
                                if ttags[col]['tags'].get('col_type') == 'NE':
                                    stats['ne_cols'] += 1


# for i in tqdm(diz_overall):
#     tables = diz_overall[i]['tables']
#     for tab in tables:

#         n_tables+=1
#         header_mat = tables[tab]['header']
#         text_mat = tables[tab]['text']
#         link_mat = tables[tab]['link']
#         entity_mat = tables[tab]['entity']
#         types_mat = tables[tab]['types']
#         col_types_mat = tables[tab]['col_types']
#         col_types_perfect_mat = tables[tab]['col_type_perfect']

#         current_rows = len(text_mat)
#         current_cols = len(text_mat[0])
#         current_cells = len(text_mat)*len(text_mat[0])
#         current_headers = len(header_mat)

#         current_links  = sum(1 for row in link_mat for cell in row if cell)
#         current_mentions  = sum(1 for row in entity_mat for cell in row if cell)
#         current_nils  = sum(1 for row in entity_mat for cell in row if cell == 'NIL')
#         current_types  = sum(1 for row in types_mat for cell in row if cell)
#         current_col_types  = sum(1 for col in col_types_mat if col)
#         current_col_types_perfect  = sum(1 for col in col_types_perfect_mat if col)

#         rows += current_rows
#         cols += current_cols
#         cells += current_cells
#         headers += current_headers
#         headers_yn += int(current_headers > 0)

#         links += current_links
#         mentions += current_mentions
#         nils += current_nils
#         types += current_types
#         col_types += current_col_types
#         col_types_perfect += current_col_types_perfect

#         max_rows = max(max_rows, len(text_mat))
#         max_cols = max(max_cols, len(text_mat[0]))
#         min_rows = min(min_rows, len(text_mat))
#         min_cols = min(min_cols, len(text_mat[0]))

#        all_entities = all_entities.union(set([cell for row in entity_mat for cell in row if cell.startswith('Q')]))


pprint(stats)

with open('mammostats.json', 'w') as fd:
    json.dump(stats, fd)
