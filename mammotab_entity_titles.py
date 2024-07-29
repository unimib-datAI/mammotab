#!/usr/bin/env python
# coding: utf-8
# +
from bs4 import BeautifulSoup, SoupStrainer

import re
from utilities.utils import normalize_links
import html
from tqdm import tqdm

import sys
import os
import pickle

#file_name = 'enwiki-20220720-pages-articles-multistream2.xml-p41243p151573.bz2'
# call by using "python script_name.py filename.bz2
file_name = sys.argv[1]                                                    

#file_name = 'enwiki-20220520-pages-articles-multistream1.xml-p1p41242.bz2'  #write file name


#open ONE bz2 file
import bz2
with bz2.open(file_name, 'rb') as f:
    text = f.read()

#parsing using <page>...<\page>
parse_only = SoupStrainer('page')                                         

#some useful samples
#sub_text = text[220000000:270000000]
#sub_text = text[:3000000]

soup = BeautifulSoup(text, "html.parser", parse_only=parse_only)          #all tables
#soup = BeautifulSoup(sub_text, "html.parser", parse_only=parse_only)     #for sub-sampling

#it may takes a few minutes, be patient!

#dictionary index to store each page in a dict element
diz = {}                                                           

for n_page, page in enumerate(tqdm(soup)):
    page = html.unescape(str(page))


    id_ = re.search("(?<=\<id>)(.*?)(?=\</id>)", str(page))          #page id and
    tit = re.search("(?<=\<title>)(.*?)(?=\</title>)", str(page))    #page title

    id_page = id_.group(0)
    title = tit.group(0)

    if not title:
        raise Exception(f'Cannot find title for page {n_page}')

    if not id_page:
        raise Exception(f'Cannot find id for page {n_page}')

    title = normalize_links(title)

    diz[title] = id_page

#create folder
cur_dir = os.getcwd()
new_dir = os.path.join(cur_dir, 'wiki_entities_titles', file_name)

if not os.path.exists(new_dir):
    os.makedirs(new_dir)

#save dictionary
with open(os.path.join(new_dir, 'diz.pickle'), 'wb') as fd:
    pickle.dump(diz, fd)

