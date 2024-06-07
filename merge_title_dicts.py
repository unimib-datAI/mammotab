import pickle
import os
import sys
from glob import glob
from tqdm import tqdm

main_folder = sys.argv[1]

all_diz = {}

total_len = 0

for diz_path in tqdm(glob(os.path.join(main_folder, '*', '*'))):
    with open(diz_path, 'rb') as fd:
        diz = pickle.load(fd)
    total_len += len(diz)

    all_diz = {**all_diz, **diz}
    # break

print('------------')
print('tot',total_len)
print('actual', len(all_diz))
print('------------')
#assert total_len == len(all_diz)
with open('all_titles.pickle', 'wb') as fd:
    pickle.dump(all_diz, fd)