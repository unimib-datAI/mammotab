from tqdm import tqdm
import gzip
import os
import json
import numpy as np
import sys
import csv
from pprint import pprint
from dotenv import load_dotenv
from utilities.exporter import AddAcronyms, AddAliases, AddTypos, ApproximateNumbers
import multiprocessing as mp
from functools import partial
import gc

load_dotenv()

ADDACRONIMS = bool(os.getenv('ADDACRONIMS'))
ADDALIASES = bool(os.getenv('ADDALIASES'))
ADDTYPOS = bool(os.getenv('ADDTYPOS'))
APPROXIMATENUMBERS = bool(os.getenv('APPROXIMATENUMBERS'))

# Initialize stats as a multiprocessing Manager dict
def init_stats():
    return {
        'n_tables': 0,
        'max_rows': 0,
        'max_cols': 0,
        'min_rows': sys.maxsize,
        'min_cols': sys.maxsize,
        'ne_cols': 0,
        'lit_cols': 0,
        'cols_with_acronyms': 0,
        'cols_with_typos': 0,
        'cols_with_approx': 0,
        'cols_with_aliases': 0,
        'cells': 0,
        'rows': 0,
        'cols': 0,
        'tot_linked_cell': 0,
        'types_not_found': 0,
        'types_found': 0,
        'mentions': 0,
        'nils': 0,
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
        'count_multi_domain': 0
    }

base_folder = sys.argv[1]
output_path = sys.argv[2]

table_output_path = os.path.join(output_path, 'tables')
json_output_path = os.path.join(output_path, 'json')
gt_output_path = os.path.join(output_path, 'gt')
target_output_path = os.path.join(output_path, 'target')

os.makedirs(table_output_path, exist_ok=True)
os.makedirs(gt_output_path, exist_ok=True)
os.makedirs(target_output_path, exist_ok=True)
os.makedirs(json_output_path, exist_ok=True)

min_links_number = 3

def process_single_file(file_path, table_output_path, json_output_path, min_links_number):
    local_stats = init_stats()
    local_cea = []
    local_cta = []
    local_entities = set()
    tables_to_keep = []
    
    try:
        with gzip.open(file_path, 'rb') as f:
            diz = json.load(f)
            
            for tab in diz['tables']:
                tabcode = tab
                len_header = len(diz['tables'][tab]['header']) if diz['tables'][tab].get('header') else 0
                table_ent = diz['tables'][tab]['entity'][len_header:]
                ent_mat = np.asarray(table_ent)

                if ent_mat.size > 0 and len(ent_mat.shape) >= 2:
                    ent_sum = np.sum(ent_mat != '', axis=0)
                    current_max = np.max(ent_sum)

                    if current_max >= min_links_number:
                        local_stats['n_tables'] += 1
                        rows = len(diz['tables'][tab]['text'])
                        cols = len(diz['tables'][tab]['text'][0])
                        ttags = diz['tables'][tab]['tags']
                        local_stats['rows'] += rows
                        local_stats['cols'] += cols
                        local_stats['cells'] += len(diz['tables'][tab]['text']) * len(diz['tables'][tab]['text'][0])
                        
                        if rows > local_stats['max_rows']:
                            local_stats['max_rows'] = rows
                        if cols > local_stats['max_cols']:
                            local_stats['max_cols'] = cols
                        if rows < local_stats['min_rows']:
                            local_stats['min_rows'] = rows
                        if cols < local_stats['min_cols']:
                            local_stats['min_cols'] = cols

                        for col in ttags:
                            if isinstance(ttags[col], dict) and 'tags' in ttags[col]:
                                if ttags[col]['tags'].get('col_type') == 'LIT':
                                    local_stats['lit_cols'] += 1
                                if ttags[col]['tags'].get('col_type') == 'NE':
                                    local_stats['ne_cols'] += 1

                        text_mat = diz['tables'][tab]['text']
                        entity_mat = diz['tables'][tab]['entity']
                        col_types_perfect_mat = diz['tables'][tab]['col_type_perfect']

                        local_stats['tot_linked_cell'] += diz['tables'][tab]['stats']['tot_linked_cell']
                        local_stats['types_found'] += diz['tables'][tab]['stats']['types_found']
                        local_stats['types_not_found'] += diz['tables'][tab]['stats']['types_not_found']
                        local_stats['count_with_header'] += diz['tables'][tab]['stats']['count_with_header']
                        local_stats['count_with_caption'] += diz['tables'][tab]['stats']['count_with_caption']
                        local_stats['acro_added'] += diz['tables'][tab]['stats']['acro_added']
                        local_stats['typos_added'] += diz['tables'][tab]['stats']['typos_added']
                        local_stats['approx_added'] += diz['tables'][tab]['stats']['approx_added']
                        local_stats['alias_added'] += diz['tables'][tab]['stats']['alias_added']
                        local_stats['generic_types'] += diz['tables'][tab]['stats']['generic_types']
                        local_stats['specific_types'] += diz['tables'][tab]['stats']['specific_types']
                        local_stats['filtered_types'] += diz['tables'][tab]['stats']['filtered_types']
                        local_stats['found_perfect_types'] += diz['tables'][tab]['stats']['found_perfect_types']
                        local_stats['tot_cols_with_types'] += diz['tables'][tab]['stats']['tot_cols_with_types']
                        local_stats['count_single_domain'] += diz['tables'][tab]['stats']['count_single_domain']
                        local_stats['count_multi_domain'] += diz['tables'][tab]['stats']['count_multi_domain']

                        local_stats['mentions'] += sum(1 for row in entity_mat for cell in row if cell)
                        local_stats['nils'] += diz['tables'][tab]['stats']['nils']

                        if ADDACRONIMS:
                            acro = 0
                            cols_with_acronyms = 0
                            diz['tables'][tab], acro, cols_with_acronyms = AddAcronyms(diz['tables'][tab])
                            local_stats['acro_added'] += acro
                            local_stats['cols_with_acronyms'] += cols_with_acronyms
                            diz['tables'][tab]['stats']['acro_added'] = acro
                        if ADDTYPOS:
                            typo = 0
                            cols_with_typos = 0
                            diz['tables'][tab], typo, cols_with_typos = AddTypos(diz['tables'][tab])
                            local_stats['typos_added'] += typo
                            local_stats['cols_with_typos'] += cols_with_typos
                            diz['tables'][tab]['stats']['typos_added'] = typo
                        if APPROXIMATENUMBERS:
                            approx = 0
                            cols_with_approx = 0
                            diz['tables'][tab], approx, cols_with_approx = ApproximateNumbers(diz['tables'][tab])
                            local_stats['approx_added'] += approx
                            local_stats['cols_with_approx'] += cols_with_approx
                            diz['tables'][tab]['stats']['approx_added'] = approx
                        if ADDALIASES:
                            alias = 0
                            cols_with_aliases = 0
                            diz['tables'][tab], alias, cols_with_aliases = AddAliases(diz['tables'][tab])
                            local_stats['alias_added'] += alias
                            local_stats['cols_with_aliases'] += cols_with_aliases
                            diz['tables'][tab]['stats']['alias_added'] = alias

                        entity_cells = set([cell for row in entity_mat for cell in row if cell.startswith('Q')])
                        local_entities.update(entity_cells)
                        tables_to_keep.append(tabcode)

            # Process tables to keep
            for tab in tables_to_keep:
                tabcode = tab
                len_header = len(diz['tables'][tab]['header']) if diz['tables'][tab].get('header') else 0
                table_txt = diz['tables'][tab]['text'][len_header:]
                table_ent = diz['tables'][tab]['entity'][len_header:]
                row_indx = 0

                table_ent = np.array(table_ent)
                table_txt = np.array(table_txt)

                # TABLE TXT
                ncol = len(table_txt[0])
                head = ['col{}'.format(i) for i in range(ncol)]
                table_txt_anon_header = [head] + table_txt.tolist()

                with open(os.path.join(table_output_path, tabcode + '.csv'), "w", newline='') as file:
                    write = csv.writer(file)
                    write.writerows(table_txt_anon_header)

                # CEA processing
                for col_indx, ent_col in enumerate(table_ent.T):
                    if any(ent_col):
                        for row_indx, ent_cell in enumerate(ent_col):
                            cea_entity = str(ent_cell) if ent_cell else 'UNKNOWN'
                            if cea_entity.startswith('Q'):
                                cea_entity = 'http://www.wikidata.org/entity/' + cea_entity
                            cea_line = [tabcode, row_indx, col_indx, cea_entity]
                            local_cea.append(cea_line)

                # CTA processing
                col_types_perfect = diz['tables'][tab]['col_type_perfect']
                for i, col in enumerate(col_types_perfect):
                    cta_type = str(col) if col else 'UNKNOWN'
                    if cta_type.startswith('Q'):
                        cta_type = 'http://www.wikidata.org/entity/' + cta_type
                    cta_line = [tabcode, i, cta_type]
                    local_cta.append(cta_line)

                # Save JSON
                with open(os.path.join(json_output_path, tab + '.json'), 'w') as f:
                    json.dump(diz['tables'][tab], f, indent=4, ensure_ascii=False)

            return local_stats, local_cea, local_cta, local_entities, tables_to_keep

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return None

def main():
    # Initialize global stats
    global_stats = init_stats()
    global_cea = []
    global_cta = []
    global_entities = set()
    processed_files = 0

    # Get all files to process
    file_paths = []
    for folder_name in os.listdir(base_folder):
        folder_path = os.path.join(base_folder, folder_name)
        if os.path.isdir(folder_path):
            for f_name in os.listdir(folder_path):
                if 'diz_' in f_name:
                    file_paths.append(os.path.join(folder_path, f_name))

    # Setup multiprocessing
    num_processes = max(1, mp.cpu_count() // 2)
    print(f"Using {num_processes} processes")

    # Process files in parallel
    with mp.Pool(processes=num_processes) as pool:
        # Create partial function with fixed arguments
        process_func = partial(process_single_file, 
                              table_output_path=table_output_path,
                              json_output_path=json_output_path,
                              min_links_number=min_links_number)
        
        # Use imap_unordered for better performance with tqdm
        results = list(tqdm(pool.imap_unordered(process_func, file_paths), total=len(file_paths)))

    # Aggregate results
    for result in results:
        if result is not None:
            local_stats, local_cea, local_cta, local_entities, _ = result
            processed_files += 1
            
            # Merge stats
            for key in global_stats:
                if key in ['max_rows', 'max_cols']:
                    global_stats[key] = max(global_stats[key], local_stats[key])
                elif key in ['min_rows', 'min_cols']:
                    global_stats[key] = min(global_stats[key], local_stats[key])
                else:
                    global_stats[key] += local_stats[key]
            
            # Merge CEA/CTA
            global_cea.extend(local_cea)
            global_cta.extend(local_cta)
            global_entities.update(local_entities)

    print(f"Processed {processed_files} files")

    # Save final outputs
    print('Creating GT...')
    with open(os.path.join(gt_output_path, "CEA_mammotab_gt.csv"), "w", newline='') as file:
        write = csv.writer(file)
        write.writerows(global_cea)
    
    if global_cta:
        with open(os.path.join(gt_output_path, "CTA_mammotab_gt.csv"), "w", newline='') as file:
            write = csv.writer(file)
            write.writerows(global_cta)

    # Save target files
    with open(os.path.join(target_output_path, "CEA_mammotab_target.csv"), "w", newline='') as file:
        n_col_target = len(global_cea[0]) - 1
        CEA_target = map(lambda x: x[:n_col_target], global_cea)
        write = csv.writer(file)
        write.writerows(CEA_target)
    
    if global_cta:
        with open(os.path.join(target_output_path, "CTA_mammotab_target.csv"), "w", newline='') as file:
            n_col_target = len(global_cta[0]) - 1
            CTA_target = map(lambda x: x[:n_col_target], global_cta)
            write = csv.writer(file)
            write.writerows(CTA_target)

    # Final stats
    ultimate_stats = {
        'n_tables': global_stats['n_tables'],
        'max_rows': global_stats['max_rows'],
        'max_cols': global_stats['max_cols'],
        'min_rows': global_stats['min_rows'],
        'min_cols': global_stats['min_cols'],
        'ne_cols': global_stats['ne_cols'],
        'lit_cols': global_stats['lit_cols'],
        'cols_with_acronyms': global_stats['cols_with_acronyms'],
        'cols_with_typos': global_stats['cols_with_typos'],
        'cols_with_approx': global_stats['cols_with_approx'],
        'cols_with_aliases': global_stats['cols_with_aliases'],
        'cells': global_stats['cells'],
        'rows': global_stats['rows'],
        'cols': global_stats['cols'],
        'tot_linked_cell': global_stats['tot_linked_cell'],
        "mentions": global_stats['mentions'],
        "nils": global_stats['nils'],
        "types_not_found": global_stats['types_not_found'],
        "types_found": global_stats['types_found'],
        "count_with_header": global_stats['count_with_header'],
        "count_with_caption": global_stats['count_with_caption'],
        "acro_added": global_stats['acro_added'],
        "typos_added": global_stats['typos_added'],
        "approx_added": global_stats['approx_added'],
        "alias_added": global_stats['alias_added'],
        "generic_types": global_stats['generic_types'],
        "specific_types": global_stats['specific_types'],
        "filtered_types": global_stats['filtered_types'],
        "found_perfect_types": global_stats['found_perfect_types'],
        "tot_cols_with_types": global_stats['tot_cols_with_types'],
        "count_single_domain": global_stats['count_single_domain'],
        "count_multi_domain": global_stats['count_multi_domain'],
        "all_entities": len(global_entities)
    }

    pprint(ultimate_stats)

    with open('mammostats_semtab.json', 'w') as fd:
        json.dump(ultimate_stats, fd)

if __name__ == '__main__':
    main()