import pickle,json,os,re
import functools
import numpy as np

base_threshold = 0.6
with open('ontology_complete.pickle', 'rb') as fd:
    ontology_complete = pickle.load(fd)
with open('depth.pickle', 'rb') as fd:
    depth = pickle.load(fd)

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'most_common.json'), 'r') as file:
    data = json.load(file)
    first_5000_keys = list(data.keys())[:5000]

def IsGeneric(qid):
    return str(qid).replace('Q','') in first_5000_keys
    
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
    
def dynamic_threshold(n, base_th=0.8):
    # return a threshold that varies with the number of rows
    return  base_th + (1 - base_th) / (n - 2)

def handle_types(list_of_types):
    # iterate by columns
    nlines = len(list_of_types)
    # rotate
    list_of_types = np.array(list_of_types, dtype=object).T.tolist()
    #print("list_of_types",list_of_types)
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
        #breakpoint()
        # exclude all types that are nor subject nor object of the relation is_subclass
        to_filter = to_filter.union(set([t for t in current_counter if t not in depth]))
        current_counter = {k:v for k,v in current_counter.items() if k not in to_filter}

        current_counter = sorted(current_counter.items(), key=lambda x: functools.cmp_to_key(is_subclass)(x[0]))
        current_counter = [('Q{}'.format(_type),coverage) for _type, coverage in current_counter]
        # EXAMPLE: [('Q486972', 0.01818181818181818), ('Q3957', 0.01818181818181818), ('Q1093829', 0.7090909090909091), ('Q62049', 0.4727272727272727), ('Q1074523', 0.2), ('Q1549591', 0.2909090909090909), ('Q15127012', 0.05454545454545454), ('Q17201685', 0.01818181818181818), ('Q13410438', 0.14545454545454545)]
        # from the most generic to the most specific types
        #print("current_counter",current_counter)
        
        counter.append(current_counter)

        th = dynamic_threshold(nlines, base_threshold)
        #print("th",th)
        
        try:
            #find the first most specific (reversed) type that has a value greater than the threshold
            perfect.append(next(c for c,v in reversed(current_counter) if v >= th))
        except:
            perfect.append('')
    
    return counter, perfect, to_filter

def manage_generic_types(current,types,ctab):
    for tp in types:
        for t in tp:
            if IsGeneric(t):
                current['generic_types'] += 1
                if 'generic_types' not in ctab:
                    ctab['generic_types'] = True
            else:
                current['specific_types'] += 1
                if 'specific_types' not in ctab:
                    ctab['specific_types'] = True

def mammotab_wiki(diz, entities_diz, types_diz, all_titles,doprint=False):
    filtered_types = set()
    current = {
        'tot_linked_cell': 0,
        'entities_found': 0,
        'entities_not_found': 0,
        'types_found': 0,
        'types_not_found': 0,
        'tot_cells': 0,
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
    tables_to_keep = set()

    for tab in diz['tables']:
        table_link = diz['tables'][tab]['link']
        table_text = diz['tables'][tab]['text']
        diz['tables'][tab]['entity'] = []
        diz['tables'][tab]['types'] = []
        diz['tables'][tab]['col_types'] = []
        table_tags = diz['tables'][tab]['tags']
        row_to_remove = set()
        local = {
            'tot_linked_cell': 0,
            'entities_found': 0,
            'entities_not_found': 0,
            'types_found': 0,
            'types_not_found': 0,
            'tot_cells': 0,
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
        for row_id, line_link in enumerate(table_link):
            entities_line = []
            types_line = []
            for col_id, cell_link in enumerate(line_link):
                if cell_link:
                    #print(cell_text,cell_link)
                    local['tot_linked_cell']+=1
                    # a wikidata link
                    if cell_link.startswith(':d:Q'):
                        # wikidata
                        cell_text = table_text[row_id][col_id]
                        if re.search('Q[0-9]+', cell_text):
                            # remove row
                            row_to_remove.add(row_id)
                            empty_line = [''] * len(line_link)
                            entities_line = empty_line
                            break
                        else:
                            entity = cell_link[3:]
                            entities_line.append(entity)
                            local['entities_found']+=1

                            try:
                                types_line.append(types_diz[entity])
                                local['types_found']+=1
                                manage_generic_types(local,types_diz[entity],diz['tables'][tab]['tags'])
                            except KeyError:
                                types_line.append([])
                                local['types_not_found']+=1
                    else:
                        try:
                            entity = entities_diz[cell_link]
                            entities_line.append(entity)
                            local['entities_found']+=1

                            try:
                                types_line.append(types_diz[entity])
                                local['types_found']+=1
                                manage_generic_types(local,types_diz[entity],diz['tables'][tab]['tags'])
                            except KeyError:
                                types_line.append([])
                                local['types_not_found']+=1


                        except KeyError:
                            # if NIL
                            # not found with lamapi
                            # check if link not present in wikipedia -> NIL, red wiki link
                            if cell_link not in all_titles:
                                local['entities_not_found']+=1
                                local['nils']+=1
                                if str(col_id) not in table_tags:
                                    table_tags[str(col_id)] = {}
                                table_tags[str(col_id)]['nil_present'] = True
                                entities_line.append('NIL')
                            else:
                                local['entities_not_found']+=1
                                #entities not in dictionary --> (possible nil?)
                                entities_line.append('') 

                            local['types_not_found']+=1
                            types_line.append([])

                else:
                    entities_line.append('')
                    types_line.append([])

                local['tot_cells']+=1

            diz['tables'][tab]['entity'].append(entities_line)
            diz['tables'][tab]['types'].append(types_line)

        if(len(diz['tables'][tab]['header']) > 0):
            diz['tables'][tab]['tags']['header'] = True
            local['count_with_header'] += 1
        else:
            diz['tables'][tab]['tags']['header'] = False   
        if(diz['tables'][tab]['caption'] and diz['tables'][tab]['caption']!='None'):
            diz['tables'][tab]['tags']['caption'] = True
            local['count_with_caption'] += 1
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
        local['filtered_types'] = len(filtered_types)
        perfectCount = len([t for t in diz['tables'][tab]['col_type_perfect'] if t])
        #TODO this need to be improved to consider the number and frequency 
        # of types in the column to identify if it is a single domain table
        if(perfectCount <= 2):
            diz['tables'][tab]['single_domain'] = True
            local['count_single_domain'] += 1
        else:
            diz['tables'][tab]['single_domain'] = False
            local['count_multi_domain'] += 1
        local['found_perfect_types'] += perfectCount
        local['tot_cols_with_types'] += len([t for t in diz['tables'][tab]['col_types'] if t])
        diz['tables'][tab]['stats'] = local
        tables_to_keep.add(tab)
    for key in local:
        if key in current:
            current[key] += local[key]
    
    diz['tables'] = {k:t for k,t in diz['tables'].items() if k in tables_to_keep}
    #print("current",current)
    return diz,current