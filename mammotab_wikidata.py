#!/usr/bin/env python
# coding: utf-8

from tqdm import tqdm

import gzip, json
import numpy as np
import sys
import os
import gzip
import json
import pickle
from utilities.utils_wd import mammotab_wiki
from utilities.lamapi import call_lamapi
from utilities.exporter import AddAcronyms,AddAliases,AddTypos,ApproximateNumbers

with open('all_titles.pickle', 'rb') as fd:
    all_titles = pickle.load(fd)

fol_name = sys.argv[2]
origin_folder = sys.argv[1]
destination_folder = sys.argv[3]
#fol_name = 'enwiki-20220701-pages-articles-multistream1.xml-p1p41242.bz2'
#fol_name = 'enwiki-20220720-pages-articles-multistream2.xml-p41243p151573.bz2'

folder_name = os.path.join(os.getcwd(),origin_folder, fol_name)

#creating a list of possible linked entities

diz_info = {'tot_link' : 0,
            'tot_nolink' : 0,
            'tot_linked_cell': 0,
        'entities_found': 0,
        'entities_not_found': 0,
        'types_found': 0,
        'types_not_found': 0,
        'tot_cells': 0,
        'count_with_header': 0,
        'count_with_caption': 0,
        'acro_added': 0,
        'typos_added': 0,
        'approx_added': 0,
        'alias_added': 0,
        'generic_types': 0,
        'specific_types': 0,
        'filtered_types': 0,
        'found_perfect_types': 0,
        'tot_cols_with_types': 0,
        'count_single_domain': 0,
        'count_multi_domain': 0}

entities_list = []
entities_set = set()
wikidata_entities_set = set()

for f_name in tqdm(os.listdir(folder_name)):
    if 'diz_' in f_name:
        with gzip.open(os.path.join(folder_name, f_name), 'rb') as f:
            diz = json.load(f)

            for tab in diz['tables']:
                #print(diz['wiki_id'])
                table_link = diz['tables'][tab]['link']
                table_text = diz['tables'][tab]['text']

                for line_link in table_link:
                    for cell_link in line_link:
                        if cell_link:
                            diz_info['tot_link'] +=1
                            # already a link to wikidata
                            if cell_link.startswith(':d:Q') and cell_link[4:].isnumeric():
                                wikidata_entities_set.add(cell_link[3:])
                            else:
                                entities_set.add(cell_link)
                                #anche se non è linkata potrebbe avere un'entità, si prova lo stesso?
                        else:
                            diz_info['tot_nolink'] +=1


#creating dictiory of entities and types based on wikidata
#entities_diz structure --> {page_title:entity_code}
#types_diz structure --> {page_title:type_code}

entities_list = list(entities_set)

entities_diz = call_lamapi(entities_list, 'entities')
#types_diz = call_lamapi(entities_list, 'types')
types_list = list(set(entities_diz.values()).union(wikidata_entities_set))
types_diz = call_lamapi(types_list, 'types')

diz_info['found_entities'] = len(entities_diz)
diz_info['found_types'] = len(types_diz)

#create folder
cur_dir = os.getcwd()
new_dir = os.path.join(cur_dir, 'entities_dictionaries')

if not os.path.exists(new_dir):
    os.makedirs(new_dir)


#save entities dictionary
with open(os.path.join(new_dir, 'entities_diz_' + fol_name +'.json'), 'w') as f:
    json.dump(entities_diz, f)

diz_overall = {}
i=0
for f_name in tqdm(os.listdir(folder_name)):
    if 'diz_' in f_name:
        with gzip.open(os.path.join(folder_name, f_name), 'rb') as f:
            diz = json.load(f)
            current = {}
            #main function to add wikidata info
            diz,current = mammotab_wiki(diz, entities_diz, types_diz, all_titles)
            for key in current:
                if key in diz_info:
                    diz_info[key] += current[key]
            diz_overall[i] = diz
            i+=1

#create folder
cur_dir = os.getcwd()
new_dir = os.path.join(cur_dir, destination_folder, fol_name)

if not os.path.exists(new_dir):
    os.makedirs(new_dir)


#save each dictionary
for el in tqdm(diz_overall):
    with gzip.open(os.path.join(new_dir, 'diz_' + diz_overall[el]['wiki_id'] + '.json.gz'), 'wt') as fd:
        json.dump(diz_overall[el], fd)

#save dump info
with open(os.path.join(new_dir, 'entype_info_' + fol_name +'.json'), 'w') as f:
    json.dump(diz_info, f)
