import gzip,json,pickle
from utilities.utils_wd import mammotab_wiki
from utilities.lamapi import call_lamapi

filename = 'diz_51991474.json.gz'

with open('all_titles.pickle', 'rb') as fd:
    all_titles = pickle.load(fd)

wikidata_entities_set = set()
entities_list = []
entities_set = set()

print('Loading...')
with gzip.open(filename, 'rb') as f:
            diz = json.load(f)

            for tab in diz['tables']:
                #print(diz['wiki_id'])
                table_link = diz['tables'][tab]['link']
                table_text = diz['tables'][tab]['text']

                for line_link in table_link:
                    for cell_link in line_link:
                        if cell_link:
                            # already a link to wikidata
                            if cell_link.startswith(':d:Q') and cell_link[4:].isnumeric():
                                wikidata_entities_set.add(cell_link[3:])
                            else:
                                entities_set.add(cell_link)
print('entities loaded')
entities_list = list(entities_set)

entities_diz = call_lamapi(entities_list, 'entities')
#types_diz = call_lamapi(entities_list, 'types')
types_list = list(set(entities_diz.values()).union(wikidata_entities_set))
types_diz = call_lamapi(types_list, 'types')

with gzip.open(filename, 'rb') as f:
    diz = json.load(f)
    print('Processing...')
    diz,current = mammotab_wiki(diz, entities_diz, types_diz, all_titles, True)