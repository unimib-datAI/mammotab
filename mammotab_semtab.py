from tqdm import tqdm
import gzip
import os
import json
import numpy as np
import sys
import csv
from pprint import pprint
from dotenv import load_dotenv
from utilities.exporter import AddAcronyms,AddAliases,AddTypos,ApproximateNumbers

load_dotenv()

ADDACRONIMS = bool(os.getenv('ADDACRONIMS'))
ADDALIASES = bool(os.getenv('ADDALIASES'))
ADDTYPOS = bool(os.getenv('ADDTYPOS'))
APPROXIMATENUMBERS = bool(os.getenv('APPROXIMATENUMBERS'))

stats = {
    'n_tables': 0,
    'max_rows' : 0, 
    'max_cols' : 0,
    'min_rows' : sys.maxsize,
    'min_cols' : sys.maxsize,
    'ne_cols' : 0,
    'lit_cols' : 0,
    'cols_with_acronyms': 0,
    'cols_with_typos': 0,
    'cols_with_approx': 0,
    'cols_with_aliases': 0,
    'cells': 0,
    'rows': 0,
    'cols' : 0,
    'tot_linked_cell' : 0,
    'types_not_found': 0,
    'types_found': 0,
    'mentions' : 0,
    'nils' : 0,
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

base_folder = sys.argv[1]

output_path = sys.argv[2]

table_output_path = os.path.join(output_path, 'tables')
gt_output_path = os.path.join(output_path, 'gt')
target_output_path = os.path.join(output_path, 'target')

os.makedirs(table_output_path, exist_ok=True)
os.makedirs(gt_output_path, exist_ok=True)
os.makedirs(target_output_path, exist_ok=True)


min_links_number = 3

CEA = []
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
                stats['n_tables'] += 1
                rows = len(el['tables'][tab]['text'])
                cols = len(el['tables'][tab]['text'][0])
                ttags = el['tables'][tab]['tags']
                stats['rows'] += rows
                stats['cols'] += cols
                stats['cells'] += len(el['tables'][tab]['text']) * len(el['tables'][tab]['text'][0])
                if rows > stats['max_rows']:
                    stats['max_rows'] = rows
                if cols > stats['max_cols']:
                    stats['max_cols'] = cols
                if rows < stats['min_rows']:
                    stats['min_rows'] = rows
                if cols < stats['min_cols']:
                    stats['min_cols'] = cols

                for col in ttags:
                    if isinstance(ttags[col], dict) and 'tags' in ttags[col]:
                        if ttags[col]['tags'].get('col_type') == 'LIT':
                            stats['lit_cols'] += 1
                        if ttags[col]['tags'].get('col_type') == 'NE':
                            stats['ne_cols'] += 1

                text_mat = el['tables'][tab]['text']
                link_mat = el['tables'][tab]['link']
                entity_mat = el['tables'][tab]['entity']
                types_mat = el['tables'][tab]['types']
                col_types_mat = el['tables'][tab]['col_types']
                col_types_perfect_mat = el['tables'][tab]['col_type_perfect']

                stats['tot_linked_cell'] += el['tables'][tab]['stats']['tot_linked_cell']
                stats['types_found'] += el['tables'][tab]['stats']['types_found']
                stats['types_not_found'] += el['tables'][tab]['stats']['types_not_found']
                stats['count_with_header'] += el['tables'][tab]['stats']['count_with_header']
                stats['count_with_caption'] += el['tables'][tab]['stats']['count_with_caption']
                stats['acro_added'] += el['tables'][tab]['stats']['acro_added']
                stats['typos_added'] += el['tables'][tab]['stats']['typos_added']
                stats['approx_added'] += el['tables'][tab]['stats']['approx_added']
                stats['alias_added'] += el['tables'][tab]['stats']['alias_added']
                stats['generic_types'] += el['tables'][tab]['stats']['generic_types']
                stats['specific_types'] += el['tables'][tab]['stats']['specific_types']
                stats['filtered_types'] += el['tables'][tab]['stats']['filtered_types']
                stats['found_perfect_types'] += el['tables'][tab]['stats']['found_perfect_types']
                stats['tot_cols_with_types'] += el['tables'][tab]['stats']['tot_cols_with_types']
                stats['count_single_domain'] += el['tables'][tab]['stats']['count_single_domain']
                stats['count_multi_domain'] += el['tables'][tab]['stats']['count_multi_domain']

                stats['mentions'] += sum(1 for row in entity_mat for cell in row if cell)
                stats['nils'] += el['tables'][tab]['stats']['nils']

                
                if ADDACRONIMS:
                    acro = 0
                    cols_with_acronyms = 0
                    el['tables'][tab],acro,cols_with_acronyms = AddAcronyms(el['tables'][tab])
                    stats['acro_added'] += acro
                    stats['cols_with_acronyms'] += cols_with_acronyms
                if ADDTYPOS:
                    typo = 0
                    cols_with_typos = 0
                    el['tables'][tab],typo,cols_with_typos = AddTypos(el['tables'][tab])
                    stats['typos_added'] += typo
                    stats['cols_with_typos'] += cols_with_typos
                if APPROXIMATENUMBERS:
                    approx=0
                    cols_with_approx = 0
                    el['tables'][tab],approx,cols_with_approx = ApproximateNumbers(el['tables'][tab])
                    stats['approx_added'] += approx
                    stats['cols_with_approx'] += cols_with_approx
                if ADDALIASES:
                    alias = 0
                    cols_with_aliases = 0
                    el['tables'][tab],alias,cols_with_aliases = AddAliases(el['tables'][tab])
                    stats['alias_added'] += alias
                    stats['cols_with_aliases'] += cols_with_aliases
                

                entity_cells = set([cell for row in entity_mat for cell in row if cell.startswith('Q')])
                all_entities = all_entities.union(entity_cells)

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
                    # ent_cell if Q1234 or NIL, if empty string -> UNKNOWN
                    cea_entity = str(ent_cell) if ent_cell else 'UNKNOWN' 
                    if cea_entity.startswith('Q'):
                        cea_entity = 'http://www.wikidata.org/entity/' + cea_entity
                    cea_line = [tabcode,row_indx,col_indx, cea_entity]
                    CEA.append(cea_line)


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
        'n_tables' : stats['n_tables'],
        'cells' : stats['cells'],
        'rows' : stats['rows'],
        'cols' : stats['cols'],
        'tot_linked_cell' : stats['tot_linked_cell'],
        "mentions": stats['mentions'],
        "nils": stats['nils'],
        "types_not_found": stats['types_not_found'],
        "types_found": stats['types_found'],
        "count_with_header": stats['count_with_header'],
        "count_with_caption": stats['count_with_caption'],
        "acro_added": stats['acro_added'],
        "typos_added": stats['typos_added'],
        "approx_added": stats['approx_added'],
        "alias_added": stats['alias_added'],
        "generic_types": stats['generic_types'],
        "specific_types": stats['specific_types'],
        "filtered_types": stats['filtered_types'],
        "found_perfect_types": stats['found_perfect_types'],
        "tot_cols_with_types": stats['tot_cols_with_types'],
        "count_single_domain": stats['count_single_domain'],
        "count_multi_domain": stats['count_multi_domain'],
        
        "all_entities": len(all_entities) # entities
    }

pprint(ultimate_stats)

with open('mammostats_semtab.json', 'w') as fd:
    json.dump(ultimate_stats, fd)