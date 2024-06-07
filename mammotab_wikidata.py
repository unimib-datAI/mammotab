#!/usr/bin/env python
# coding: utf-8

# In[ ]:


#DUE STEP:
#1. si creano due dizionari
#  .entità = {}
#  .tipi = {}
#2. si aggiungono due nuove tabelle (stile "link" = [[True,False],[False,False]]) utilizzando i diz creati in precedenza

#NOTE:
#.manca regex per i literals
#.manca overwriting dei file
#.controllo generale non fatto


# In[ ]:
from tqdm import tqdm

import gzip, json
import numpy as np

import sys
import os
import gzip
import json

import requests

import pickle
import functools
import re

base_threshold = 0.6

# In[ ]:
with open('ontology_complete.pickle', 'rb') as fd:
    ontology_complete = pickle.load(fd)
with open('depth.pickle', 'rb') as fd:
    depth = pickle.load(fd)
with open('all_titles.pickle', 'rb') as fd:
    all_titles = pickle.load(fd)

def is_subclass(a, b):
    # descending order
    if a == b:
        return 0
    superclasses_a = ontology_complete.get(a)
    if superclasses_a and b in superclasses_a:
        # b is ancestor of a. b > a
        return 1
    superclasses_b = ontology_complete.get(b)
    if superclasses_b and a in superclasses_b:
        # a is ancestor of b. a > b
        return -1
    # their are not in a subclass relationship: reason on depth
    return depth[a] - depth[b]
# In[ ]:


fol_name = sys.argv[2]
origin_folder = sys.argv[1]
destination_folder = sys.argv[3]
#fol_name = 'enwiki-20220701-pages-articles-multistream1.xml-p1p41242.bz2'
#fol_name = 'enwiki-20220720-pages-articles-multistream2.xml-p41243p151573.bz2'

folder_name = os.path.join(os.getcwd(),origin_folder, fol_name)

# In[ ]:


def call_lamapi(list_of, ent_typ): #call LamAPI to get entities, types or literal types
    if ent_typ == 'entities':
        lam = 'entity/wikipedia-mapping'
    elif ent_typ == 'types':
        lam = 'entity/types'
    elif ent_typ == 'literals':
        lam = 'classify/literal-recognizer'
    else:
        return print('possible options: \n -entities \n -types \n -literals')

    payload = {}
    payload['json'] = list_of
    res = requests.post(os.environ.get('LAMAPI_ROOT') + lam + '?token={}'.format(os.environ.get('LAMAPI_TOKEN')),
                        json=payload)

    diz_temp = res.json()

    if ent_typ == 'entities':
        source = 'wikidata' #wikipedia, curid, wikipedia_id
        for el in diz_temp:
            diz_temp[el] = diz_temp[el][source]
        return diz_temp

    if ent_typ == 'types':
        res = requests.post(os.environ.get('LAMAPI_ROOT') + lam + '?token={}&kg=wikidata'.format(os.environ.get('LAMAPI_TOKEN')),
                        json=payload)

        diz_temp = res.json()
        diz_temp = diz_temp['wikidata']
        source = 'types' #direct_types, types

        diz_new = {}

        for key,value in diz_temp.items():
            if value['types']:
                diz_new[key] = value['types'] #[0] --> uncomment to select one type
        return diz_new

    if ent_typ == 'literals':
        source = 'datatype' #classification, tag, xml_datatype
        for el in diz_temp:
            diz_temp[el] = diz_temp[el][source]
        return diz_temp


# In[ ]:


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


# In[ ]:


#creating dictiory of entities and types based on wikidata
#entities_diz structure --> {page_title:entity_code}
#types_diz structure --> {page_title:type_code}

entities_list = list(entities_set)

entities_diz = call_lamapi(entities_list, 'entities')
#types_diz = call_lamapi(entities_list, 'types')
types_diz = call_lamapi(list(set(entities_diz.values()).union(wikidata_entities_set)), 'types')

diz_info['found_entities'] = len(entities_diz)
diz_info['found_types'] = len(types_diz)


# In[ ]:


#create folder
cur_dir = os.getcwd()
new_dir = os.path.join(cur_dir, 'entities_dictionaries')

if not os.path.exists(new_dir):
    os.makedirs(new_dir)


#save entities dictionary
with open(os.path.join(new_dir, 'entities_diz_' + fol_name +'.json'), 'w') as f:
    json.dump(entities_diz, f)


# In[ ]:


from statistics import mode

def dynamic_threshold(n, base_th=0.8):
    # return a threshold that varies with the number of rows
    return  base_th + (1 - base_th) / (n - 2)

def handle_types(list_of_types):
    # iterate by columns
    nlines = len(list_of_types)
    # rotate
    list_of_types = np.array(list_of_types, dtype=object).T.tolist()
    counter = []
    perfect = []
    to_filter = set()
    for column in list_of_types:
        current_counter = {}
        for line in column:
            for _type in line:
                _type = int(_type[1:])
                if _type in current_counter:
                    current_counter[_type] += 1
                else:
                    current_counter[_type] = 1
        current_counter = {k:v / nlines for k,v in current_counter.items()}
        # exclude all types that are nor subject nor object of the relation is_subclass
        to_filter = to_filter.union(set([t for t in current_counter if t not in depth]))
        current_counter = {k:v for k,v in current_counter.items() if k not in to_filter}
        current_counter = sorted(current_counter.items(), key=lambda x: functools.cmp_to_key(is_subclass)(x[0]))
        current_counter = [('Q{}'.format(_type),coverage) for _type, coverage in current_counter]

        counter.append(current_counter)

        th = dynamic_threshold(nlines, base_threshold)
        try:
            perfect.append(next(c for c,v in reversed(current_counter) if v >= th))
        except:
            perfect.append('')

    return counter, perfect, to_filter


# In[ ]:

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
                                # verify cell is not the wikidata id # TODO
                                cell_text = table_text[row_id][col_id]
                                # if cell_text.startswith('Q') and cell_text[1:].isnumeric():
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
                                    # check if link not present in wikipedia -> NIL
                                    if cell_link not in all_titles:
                                        entities_not_found+=1
                                        entities_line.append('NIL')
                                    else:
                                        entities_not_found+=1
                                        entities_line.append('') #entities not in dictionary --> (possible nil?)

                                    types_not_found+=1
                                    types_line.append([])

                        else:
                            entities_line.append('')
                            types_line.append([])

                        tot_cells+=1

                    diz['tables'][tab]['entity'].append(entities_line)
                    diz['tables'][tab]['types'].append(types_line)

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

                diz['tables'][tab]['col_types'], diz['tables'][tab]['col_type_perfect'], current_filtered = handle_types(diz['tables'][tab]['types']) #TODO append set of types
                filtered_types = filtered_types.union(current_filtered)

                found_perfect_types += len([t for t in diz['tables'][tab]['col_type_perfect'] if t])
                tot_cols_with_types += len([t for t in diz['tables'][tab]['col_types'] if t])

                tables_to_keep.add(tab)

            diz['tables'] = {k:t for k,t in diz['tables'].items() if k in tables_to_keep}

            diz_overall[i] = diz
            i+=1



# In[ ]:


diz_info = {'tot_cells': tot_cells,
            'tot_linked_cell': tot_linked_cell,
            'entities_found': entities_found,
            'entities_not_found': entities_not_found,
            'types_found': types_found,
            'types_not_found': types_not_found,
            'filtered_types': len(filtered_types),
            'found_perfect_types': found_perfect_types,
            'tot_cols': tot_cols_with_types
           }


# In[ ]:


#create folder
cur_dir = os.getcwd()
new_dir = os.path.join(cur_dir, destination_folder, fol_name)

if not os.path.exists(new_dir):
    os.makedirs(new_dir)


# In[ ]:


#save each dictionary
for el in tqdm(diz_overall):
    with gzip.open(os.path.join(new_dir, 'diz_' + diz_overall[el]['wiki_id'] + '.json.gz'), 'wt') as fd:
        json.dump(diz_overall[el], fd)


# In[ ]:


#save dump info
with open(os.path.join(new_dir, 'entype_info_' + fol_name +'.json'), 'w') as f:
    json.dump(diz_info, f)
