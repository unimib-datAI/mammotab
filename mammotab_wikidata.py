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
import re
from utilities.utils_wd import handle_types
from utilities.lamapi import call_lamapi
from utilities.exporter import AddAcronyms,AddAliases,AddTypos,ApproximateNumbers

with open('all_titles.pickle', 'rb') as fd:
    all_titles = pickle.load(fd)

fol_name = sys.argv[2]
origin_folder = sys.argv[1]
destination_folder = sys.argv[3]
#fol_name = 'enwiki-20220701-pages-articles-multistream1.xml-p1p41242.bz2'
#fol_name = 'enwiki-20220720-pages-articles-multistream2.xml-p41243p151573.bz2'
ADDACRONIMS = True
ADDALIASES = False
ADDTYPOS = True
APPROXIMATENUMBERS = True

folder_name = os.path.join(os.getcwd(),origin_folder, fol_name)

#creating a list of possible linked entities

diz_info = {'tot_link' : 0,
            'tot_nolink' : 0}

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

# entities and types
tot_cells = 0
tot_linked_cell = 0
entities_found = 0
entities_not_found = 0
types_found = 0
types_not_found = 0

diz_overall = {}
i=0

filtered_types = set()
found_perfect_types = 0
tot_cols_with_types = 0
count_with_header = 0
count_with_caption = 0
count_single_domain = 0
count_multi_domain = 0

for f_name in tqdm(os.listdir(folder_name)):
    if 'diz_' in f_name:
        with gzip.open(os.path.join(folder_name, f_name), 'rb') as f:
            diz = json.load(f)

            tables_to_keep = set()

            for tab in diz['tables']:
                table_link = diz['tables'][tab]['link']
                table_text = diz['tables'][tab]['text']
                diz['tables'][tab]['entity'] = []
                diz['tables'][tab]['types'] = []
                diz['tables'][tab]['col_types'] = []
                table_tags = diz['tables'][tab]['tags']
                row_to_remove = set()

                for row_id, line_link in enumerate(table_link):
                    entities_line = []
                    types_line = []
                    for col_id, cell_link in enumerate(line_link):
                        if cell_link:
                            #print(cell_text,cell_link)
                            tot_linked_cell+=1
                            # a wikidata link
                            if cell_link.startswith(':d:Q'):
                                # wikidata
                                cell_text = table_text[row_id][col_id]
                                if re.search('Q[0-9]+', cell_text):
                                    # remove row
                                    row_to_remove.add(row_id)
                                else:
                                    entity = cell_link[3:]
                                    entities_line.append(entity)
                                    entities_found+=1

                                    try:
                                        types_line.append(types_diz[entity])
                                        types_found+=1
                                    except KeyError:
                                        types_line.append([])
                                        types_not_found+=1
                            else:
                                try:
                                    entity = entities_diz[cell_link]
                                    entities_line.append(entity)
                                    entities_found+=1

                                    try:
                                        types_line.append(types_diz[entity])
                                        types_found+=1
                                    except KeyError:
                                        types_line.append([])
                                        types_not_found+=1


                                except KeyError:
                                    # if NIL
                                    # not found with lamapi
                                    # check if link not present in wikipedia -> NIL, red wiki link
                                    if cell_link not in all_titles:
                                        entities_not_found+=1
                                        if col_id not in table_tags:
                                            table_tags[col_id] = {}
                                        table_tags[str(col_id)]['nil_present'] = True
                                        entities_line.append('NIL')
                                    else:
                                        entities_not_found+=1
                                        #entities not in dictionary --> (possible nil?)
                                        entities_line.append('') 

                                    types_not_found+=1
                                    types_line.append([])

                        else:
                            entities_line.append('')
                            types_line.append([])

                        tot_cells+=1

                    diz['tables'][tab]['entity'].append(entities_line)
                    diz['tables'][tab]['types'].append(types_line)

                    if ADDACRONIMS:
                        diz['tables'][tab] = AddAcronyms(diz['tables'][tab])
                    if ADDALIASES:
                        diz['tables'][tab] = AddAliases(diz['tables'][tab])
                    if ADDTYPOS:
                        diz['tables'][tab] = AddTypos(diz['tables'][tab])
                    if APPROXIMATENUMBERS:
                        diz['tables'][tab] = ApproximateNumbers(diz['tables'][tab])
                    if(len(diz['tables'][tab]['header']) > 0):
                        diz['tables'][tab]['tags']['header'] = True
                        count_with_header += 1
                    else:
                        diz['tables'][tab]['tags']['header'] = False   
                    if(diz['tables'][tab]['caption']!=None):
                        diz['tables'][tab]['tags']['caption'] = True
                        count_with_caption += 1
                    else:
                        diz['tables'][tab]['tags']['caption'] = False

                # remove rows with wikidata item in clear text
                text_mat = np.array(diz['tables'][tab]['text'])
                header_mat = np.array(diz['tables'][tab]['header'])
                link_mat = np.array(diz['tables'][tab]['link'])
                cells_mat = np.array(diz['tables'][tab]['cells'])
                entity_mat = np.array(diz['tables'][tab]['entity'])
                types_mat = np.array(diz['tables'][tab]['types'], dtype=object)

                row_to_keep = set(range(text_mat.shape[0])) - row_to_remove
                header_row_to_keep = list(row_to_keep.intersection(set(range(header_mat.shape[0]))))
                row_to_keep = list(row_to_keep)

                text_mat = text_mat[row_to_keep]
                if header_mat.size > 0:
                    header_mat = header_mat[header_row_to_keep]
                link_mat = link_mat[row_to_keep]
                cells_mat = cells_mat[row_to_keep]
                entity_mat = entity_mat[row_to_keep]
                types_mat = types_mat[row_to_keep]

                try:
                    assert text_mat.shape == link_mat.shape
                    assert text_mat.shape == entity_mat.shape
                    if types_mat.size > 0:
                        assert text_mat.shape == types_mat.shape[:2]
                    assert text_mat.shape[0] == cells_mat.shape[0]
                    assert text_mat.shape[1] * 2 == cells_mat.shape[1]
                    if header_mat.size > 0:
                        assert text_mat.shape[1] == header_mat.shape[1]
                        assert text_mat.shape[0] >= header_mat.shape[0]
                except:
                    continue

                diz['tables'][tab]['text'] = text_mat.tolist()
                diz['tables'][tab]['header'] = header_mat.tolist()
                diz['tables'][tab]['link'] = link_mat.tolist()
                diz['tables'][tab]['cells'] = cells_mat.tolist()
                diz['tables'][tab]['entity'] = entity_mat.tolist()
                diz['tables'][tab]['types'] = types_mat.tolist()

                #accept father types of an annotation 
                diz['tables'][tab]['col_types'], diz['tables'][tab]['col_type_perfect'],\
                    current_filtered = handle_types(diz['tables'][tab]['types']) 
                filtered_types = filtered_types.union(current_filtered)

                perfectCount = len([t for t in diz['tables'][tab]['col_type_perfect'] if t])
                if(perfectCount <= 2):
                    diz['tables'][tab]['single_domain'] = True
                    count_single_domain += 1
                else:
                    diz['tables'][tab]['single_domain'] = False
                    count_multi_domain += 1
                found_perfect_types += perfectCount
                tot_cols_with_types += len([t for t in diz['tables'][tab]['col_types'] if t])

                tables_to_keep.add(tab)

            diz['tables'] = {k:t for k,t in diz['tables'].items() if k in tables_to_keep}

            diz_overall[i] = diz
            i+=1

diz_info = {'tot_cells': tot_cells,
            'tot_linked_cell': tot_linked_cell,
            'entities_found': entities_found,
            'entities_not_found': entities_not_found,
            'types_found': types_found,
            'types_not_found': types_not_found,
            'filtered_types': len(filtered_types),
            'found_perfect_types': found_perfect_types,
            'tot_cols': tot_cols_with_types,
            'count_with_header': count_with_header,
            'count_with_caption': count_with_caption,
            'count_single_domain': count_single_domain,
            'count_multi_domain': count_multi_domain,
           }

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
