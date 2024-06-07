# %%
import gzip
import functools
import pickle
import sys
from tqdm import tqdm
# %%
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

# %%
def depth(a):
    if a not in ontology:
        return 1
    else:
        return 1 + min(depth(superclass) for superclass in ontology[a])
# %%
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
# %%
ontology_complete = {}
depth = {}
for k in tqdm(ontology):
    ontology_complete[k], depth[k] = get_super(k)

# %%
with open('ontology_complete.pickle', 'wb') as fd:
    pickle.dump(ontology_complete, fd)
with open('depth.pickle', 'wb') as fd:
    pickle.dump(depth, fd)
# %%
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
