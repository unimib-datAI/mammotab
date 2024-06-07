from tqdm import tqdm
import gzip
import os
import json
import numpy as np
import sys
import csv
from pprint import pprint

#for i in range(10):
#    print(diz_overall[i]['wiki_id'])
#    for tab in diz_overall[i]['tables']:
#        print(diz_overall[i]['tables'][tab])

n_tables = 0
cells = 0
rows = 0
cols = 0
links = 0
mentions = 0
nils = 0
types = 0 # number of cells with at least a type
col_types = 0 # number of columns with at least a type
col_types_perfect_n = 0 # number of columns with at least a perfect type

base_folder = sys.argv[1]

output_path = sys.argv[2]

table_output_path = os.path.join(output_path, 'tables')
gt_output_path = os.path.join(output_path, 'gt')
target_output_path = os.path.join(output_path, 'target')

os.makedirs(table_output_path, exist_ok=True)
os.makedirs(gt_output_path, exist_ok=True)
os.makedirs(target_output_path, exist_ok=True)

# In[ ]:

min_links_number = 3


CEA = []

#skipped = 0

diz_overall = {}
i=0

all_entities = set()

print('1/4 Loading...')
for folder_name in tqdm(os.listdir(base_folder)):
    for f_name in os.listdir(os.path.join(base_folder, folder_name)):
        if 'diz_' in f_name:
            with gzip.open(os.path.join(base_folder, folder_name, f_name), 'rb') as f:
                diz = json.load(f)
                diz_overall[i] = diz
                i+=1

# filter
print('2/4 Filter...')
for i in tqdm(diz_overall):
    el = diz_overall[i]
    tables_to_keep = []
    for tab in el['tables']:

        tabcode = tab
        len_header = len(el['tables'][tab]['header']) if el['tables'][tab].get('header') else 0
        
        table_ent = el['tables'][tab]['entity'][len_header:]

        ent_mat = np.array(table_ent)

        # remove tables without a column with at least three entity

        if ent_mat.size > 0 and len(ent_mat.shape) >= 2:
            ent_sum = np.array(np.sum(ent_mat != '', axis = 0))          #sum of links
            current_max = np.amax(ent_sum)

            if current_max >= min_links_number:
                n_tables += 1
                rows += len(el['tables'][tab]['text'])
                cols += len(el['tables'][tab]['text'][0])
                cells += len(el['tables'][tab]['text']) * len(el['tables'][tab]['text'][0])

            
                text_mat = el['tables'][tab]['text']
                link_mat = el['tables'][tab]['link']
                entity_mat = el['tables'][tab]['entity']
                types_mat = el['tables'][tab]['types']
                col_types_mat = el['tables'][tab]['col_types']
                col_types_perfect_mat = el['tables'][tab]['col_type_perfect']

                links += sum(1 for row in link_mat for cell in row if cell)
                mentions += sum(1 for row in entity_mat for cell in row if cell)
                nils += sum(1 for row in entity_mat for cell in row if cell == 'NIL')
                types += sum(1 for row in types_mat for cell in row if cell)
                col_types += sum(1 for col in col_types_mat if col)
                col_types_perfect_n += sum(1 for col in col_types_perfect_mat if col)

                # all_entities = all_entities.union(set([cell for row in entity_mat for cell in row if cell.startswith('Q')]))


                tables_to_keep.append(tabcode)

    el['tables'] = {tabcode:table for tabcode, table in el['tables'].items() if tabcode in tables_to_keep}         

print('3/4 CEA + tables')
for i in tqdm(diz_overall):
    el = diz_overall[i]
    for tab in el['tables']:
        tabcode = tab
        len_header = len(el['tables'][tab]['header']) if el['tables'][tab].get('header') else 0
        table_txt = el['tables'][tab]['text'][len_header:]
        table_ent = el['tables'][tab]['entity'][len_header:]
        row_indx = 0

        table_ent = np.array(table_ent)
        table_txt = np.array(table_txt)

        # TABLE TXT
        ncol = len(table_txt[0])
        #col0, col1 ...
        head = ['col{}'.format(i) for i in range(ncol)]
        
        #table_text.insert(0, head)

        table_txt_anon_header = [head] + table_txt.tolist()
        #print(table_text)

        with open(os.path.join(table_output_path, tabcode + '.csv'), "w", newline = '') as file:
            write = csv.writer(file)
            write.writerows(table_txt_anon_header)

        # iterate columns
        for col_indx, ent_col in enumerate(table_ent.T):
            # if there are links in the column
            if any(ent_col):
                for row_indx, ent_cell in enumerate(ent_col):
                    cea_entity = str(ent_cell) if ent_cell else 'UNKNOWN' # ent_cell if Q1234 or NIL, if empty string -> UNKNOWN
                    if cea_entity.startswith('Q'):
                        cea_entity = 'http://www.wikidata.org/entity/' + cea_entity
                    cea_line = [tabcode,row_indx,col_indx, cea_entity]
                    CEA.append(cea_line)


# In[ ]:


CTA = []

print('4/4 CTA')
for i in tqdm(diz_overall):
    el = diz_overall[i]
    for tab in el['tables']:
        tabcode = tab
        col_types_perfect = el['tables'][tab]['col_type_perfect']

        for i,col in enumerate(col_types_perfect):
            cta_type = str(col) if col else 'UNKNOWN' # columns with no type is UNKNOWN
            if cta_type.startswith('Q'):
                cta_type = 'http://www.wikidata.org/entity/' + cta_type               
            cta_line = [tabcode,i, cta_type]
            CTA.append(cta_line)


# In[ ]:

# gt

with open(os.path.join(gt_output_path, "CEA_mammotab_gt.csv"), "w", newline = '') as file:   
    write = csv.writer(file)
    write.writerows(CEA)
    
if CTA:
    with open(os.path.join(gt_output_path, "CTA_mammotab_gt.csv"), "w", newline = '') as file:   
        write = csv.writer(file)
        write.writerows(CTA)

# target

with open(os.path.join(target_output_path, "CEA_mammotab_target.csv"), "w", newline = '') as file:   
    n_col_target = len(CEA[0]) - 1

    # remove last col
    CEA_target = map(lambda x: x[:n_col_target], CEA)
    
    write = csv.writer(file)
    write.writerows(CEA_target)
    
if CTA:
    with open(os.path.join(target_output_path, "CTA_mammotab_target.csv"), "w", newline = '') as file:   
        n_col_target = len(CTA[0]) - 1

        # remove last col
        CTA_target = map(lambda x: x[:n_col_target], CTA)
        
        write = csv.writer(file)
        write.writerows(CTA_target)

ultimate_stats = {
        'n_tables' : n_tables,
        'cells' : cells,
        'rows' : rows,
        'cols' : cols,
        'links' : links,
        "mentions": mentions,
        "nils": nils,
        "types": types,
        "col_types": col_types,
        "col_types_perfect": col_types_perfect_n,
        "all_entities": len(all_entities) # entities
    }

pprint(ultimate_stats)

with open('mammostats_semtab.json', 'w') as fd:
    json.dump(ultimate_stats, fd)