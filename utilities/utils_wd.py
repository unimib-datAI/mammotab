import pickle
import requests
import functools
import os
import numpy as np

base_threshold = 0.6
with open('ontology_complete.pickle', 'rb') as fd:
    ontology_complete = pickle.load(fd)
with open('depth.pickle', 'rb') as fd:
    depth = pickle.load(fd)

def get_qid(uri):
    uri = uri.strip()
    uri = uri.replace('<','').replace('>','')
    uri = uri.split('/')[-1]
    uri = uri[1:]
    if not uri.isnumeric():
        return None
    else:
        uri = int(uri)
        return uri
    
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
    uri = os.environ.get('LAMAPI_ROOT') + lam + '?token={}'.format(os.environ.get('LAMAPI_TOKEN'))
    res = requests.post(uri,
                        json=payload)
    #print(uri)
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