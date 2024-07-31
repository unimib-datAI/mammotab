import gzip, json
from collections import OrderedDict,Counter
from utils_wd import get_qid

ontology = Counter()
errors = 0
total = 0

# bzcat wikidata-20220521-truthy.nt.bz2 | 
# awk '$2 == "<http://www.wikidata.org/prop/direct/P31>" 
# {print $0}'| gzip -c > SubclassOf.gz

with gzip.open('SubclassOf.gz', 'rt') as fd:
    line = fd.readline()
    while line:
        total += 1
        subject, _, object, dot = line.split(' ')
        #print('"{}"'.format(dot))
        assert dot == '.\n', dot
        subject = get_qid(subject)
        object = get_qid(object)

        if subject and object:
            if object in ontology:
                ontology[object] +=1
            else:
                ontology[object] = 1
        else:
            errors += 1

        line = fd.readline()
        print('\r{}'.format(total), end='')
print()
print('errors', errors, 'total', total)

# Write to a JSON file
with open('most_common.json', 'w') as json_file:
    json.dump(OrderedDict(ontology.most_common()), json_file, indent=4)