# %%
import gzip
import functools
import pickle
import sys
from tqdm import tqdm
from utils_wd import get_qid
# %%
ontology = {} # X sublass_of Y --> x: y
# %%
errors = 0
total = 0
with gzip.open('ontology_all.gz', 'rt') as fd:
    line = fd.readline()
    while line:
        total += 1
        subject, _, object, dot = line.split(' ')
        #print('"{}"'.format(dot))
        assert dot == '.\n', dot
        subject = get_qid(subject)
        object = get_qid(object)

        if subject and object:
            if subject in ontology:
                ontology[subject].add(object)
            else:
                ontology[subject] = set([object])
        else:
            errors += 1

        line = fd.readline()
        print('\r{}'.format(total), end='')
print()
print('errors', errors, 'total', total)

def get_super(a):
    superclasses = set()
    processed = set()
    depth = 1
    if a in ontology:
        superclasses = superclasses.union(ontology[a])
        processed.add(a)
        # for each superclass
        remaining = superclasses - processed
        while len(remaining) != 0:
            for superclass in remaining:
                if superclass in ontology:
                    superclasses = superclasses.union(ontology[superclass])
                processed.add(superclass)
            #print(superclasses)
            remaining = superclasses - processed
            depth += 1
    return superclasses, depth

ontology_complete = {}
depth = {}
for k in tqdm(ontology):
    ontology_complete[k], depth[k] = get_super(k)

with open('ontology_complete.pickle', 'wb') as fd:
    pickle.dump(ontology_complete, fd)
#number of "subclass of" for each class in the ontology
with open('depth.pickle', 'wb') as fd:
    pickle.dump(depth, fd)