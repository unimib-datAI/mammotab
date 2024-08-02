import requests,os

def call_lamapi(list_of, ent_typ): #call LamAPI to get entities, types or literal types
    if ent_typ == 'entities':
        lam = 'entity/wikipedia-mapping'
    elif ent_typ == 'types':
        lam = 'entity/types'
    elif ent_typ == 'literals':
        lam = 'classify/literal-recognizer'
    elif ent_typ == 'aliases':
        lam = 'entity/aliases'
    else:
        return print('possible options: \n -entities \n -types \n -literals')

    payload = {}
    payload['json'] = list_of
    uri = os.environ.get('LAMAPI_ROOT') + lam + '?token={}'.format(os.environ.get('LAMAPI_TOKEN'))
    
    if ent_typ == 'aliases':
        uri = uri + '&lang=en'

    if ent_typ == 'entities' or ent_typ == 'aliases':
        source = 'wikidata' #wikipedia, curid, wikipedia_id
        res = requests.post(uri,json=payload)
        diz_temp = res.json()
        for el in diz_temp:
            diz_temp[el] = diz_temp[el][source]
        return diz_temp

    elif ent_typ == 'types':
        res = requests.post(uri+'&kg=wikidata',json=payload)

        diz_temp = res.json()
        # manage older version of LamAPI returning the additional 'wikidata' key
        if 'wikidata' in diz_temp:
            diz_temp = diz_temp['wikidata']
        source = 'types' #direct_types, types

        diz_new = {}

        for key,value in diz_temp.items():
            if value['types']:
                diz_new[key] = value['types'] #[0] --> uncomment to select one type
        return diz_new

    elif ent_typ == 'literals':
        source = 'datatype' #classification, tag, xml_datatype
        for el in diz_temp:
            diz_temp[el] = diz_temp[el][source]
        return diz_temp