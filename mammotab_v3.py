#!/usr/bin/env python
# encoding: utf-8
# +
from utilities.utils import clean_cell, keygen, normalize_links
import bz2
import gzip
import json
import os
import re
import sys
import numpy as np
from bs4 import BeautifulSoup, SoupStrainer
import wikitextparser as wtp
from tqdm import tqdm
from utilities.utils import clean_cell, keygen, normalize_links
from utilities.tokenizer import Tokenizer
import html

# Max number of rows parsed in a table
MAXLINES = 10000
MAXCOLUMNS = 1000
MAXHEADERS = 200
ENABLE_EXTERNAL_CONTEXT = False
#file_name = 'enwiki-20220720-pages-articles-multistream2.xml-p41243p151573.bz2'
# call by using "python mammotab_v3.py filename.bz2"
file_name = sys.argv[1]                                                    

#function to break the cycle in case of too many headers to speedup the dataset creation
def breakcycle(_header_cells):
    header_x = 0
    while header_x < len(_header_cells) and\
    _header_cells[header_x][0] and _header_cells[header_x][0].is_header:
        header_x += 1
        if header_x > MAXHEADERS:
                return True
    return False
#open the bz2 input file

Tokenizer = Tokenizer()

with bz2.open(file_name, 'rb') as f:
    text = f.read()

print("1. DONE - File read")

#parsing using <page>...<\page> tags
parse_only = SoupStrainer('page')                                         

soup = BeautifulSoup(text, "html.parser", parse_only=parse_only) 

diz_info = {'tot_pages': len(soup), #tot pages read
            'tot_tab': 0,           #tot tables
            'tot_linked_tab': 0,    #tot tables with at least ONE link
            'keep_tab': 0,          #tot keeped tables
            'keep_rows': 0,         #tot keeped rows
            'keep_cols': 0          #tot keeped cols
           }


diz = {}
#dictionary index to store each page in a dict element
diz_indx = 1                                                            

for page in tqdm(soup):
    page = html.unescape(str(page))
    #table index
    tab_indx = keygen()                                                  
    #wikitable filter for pages w/ at least a table
    if 'wikitable' in str(page):                                         

        id_ = re.search("(?<=\<id>)(.*?)(?=\</id>)", str(page))          #page id and
        tit = re.search("(?<=\<title>)(.*?)(?=\</title>)", str(page))    #page title

        id_page = id_.group(0)
        title = tit.group(0)

        #initializing dictionary
        diz[diz_indx] = {'wiki_id':id_page,
                         'title':title,
                         'tables':{}}
        
        parsed = wtp.parse(str(page))
        
        for table in parsed.tables:
            diz_info['tot_tab']+=1
            #filter tables w/ at least a linked cell
            if table.wikilinks:                                          
                diz_info['tot_linked_tab']+=1
                data = table.data() #(span=False) 

                #initializing table element, caption & header
                tab = {'caption':clean_cell(table.caption),   
                         'header': [],
                         'cells': [],
                         'cell_types': []}
                if(ENABLE_EXTERNAL_CONTEXT): 
                    tab['external_context'] = {}
                    for sec in parsed.sections:
                        tab['external_context'][sec.title] = sec.contents
                #line_number is an index allowing to check the header existance
                if(len(data)>MAXLINES):
                    print("Table too long, skipping lines after "+str(MAXLINES))
                    break
                for line_number, line in enumerate(data):  
                    tab_line = []
                    cell_type = []
                    if len(line)>MAXCOLUMNS:
                        print("Table too wide, skipping")
                        break
                    if line_number == 0:
                        header_x = 0
                        #header is set to None
                        tab['header'] = []                     
                        _header_cells = table.cells()
                        if breakcycle(_header_cells):
                            print("Table with too many headers, skipping")
                            break
                        #manage multi line headers, to ignore headers as content
                        while header_x < len(_header_cells) and\
                            _header_cells[header_x][0] and _header_cells[header_x][0].is_header:
                            _current_header = [clean_cell(_head_cell).replace('!','')\
                                for _head_cell in table.data()[header_x]]
                            tab['header'].append(_current_header)
                            header_x += 1
                    for indx, cell in enumerate(line):
                        #convert to string and remove \n
                        cell_str = str(cell).replace('\n','') 
                        
                        #find link
                        #link_mat = re.search("(?<=\[\[)(.*?)(?=\]\])", cell_str)
                        cell_parsed = wtp.parse(cell_str)
                        links_wtp = cell_parsed.wikilinks

                        celltype = Tokenizer.GetType(cell_str)
                        cell_type.append(celltype)
                        #CRITERION:
                        #-- if cell is linked
                        #-- cell starts and ends w/ square brackets
                        #-- ONLY ONE link is recognized
                        #if link_mat and cell_str.startswith('[[')\
                        # and cell_str.endswith(']]') and len(more_than_one) < 2:
                        #    cell_str = clean_cell(cell_str)
                        # only one link occupying the whole cell
                        if len(links_wtp) == 1 and\
                            len(links_wtp[0].plain_text()) == len(cell_parsed.plain_text()):
                            normalized = normalize_links(links_wtp[0].target)
                            cell_str = clean_cell(cell)
                            tab_line.append(cell_str)
                            tab_line.append(normalized)

                        else:
                            tab_line.append(cell_str)
                            tab_line.append('')
                    tab['cell_types'].append(cell_type)
                    tab['cells'].append(tab_line)
                tab['cells'] = np.matrix(tab['cells'])

                #table w/out any content are not considered
                if tab['cells'].size == 0:
                    continue

                # link matrix and conversion of true,false string to boolean
                link_mat = tab['cells'][:,1::2]      
                text_mat = tab['cells'][:,::2]       #texts matrix

                #link matrix and text matrix MUST have the same dimension
                assert text_mat.shape == link_mat.shape                  

                #sum of links
                link_sum = np.array(np.sum(link_mat != '', axis = 0)).reshape(-1)          

                assert link_sum.shape[0] == text_mat.shape[1]

                current_max = np.amax(link_sum)
                #at least 3 links MUST be in a single column
                if current_max >= 3:                                     
                    #the target array is the "most linked" among columns
                    targ_arr = np.argwhere(link_sum == current_max).reshape(-1,)

                    #conversion to list
                    tab['link'] = link_mat.tolist()
                    tab['text'] = text_mat.tolist()
                    tab['target_col'] = targ_arr.tolist()
                    tab['cells'] = tab['cells'].tolist()

                    diz_info['keep_tab']+=1
                    diz_info['keep_rows']+= len(text_mat)
                    diz_info['keep_cols']+= len(np.array(text_mat[0])[0])

                    diz[diz_indx]['tables'][str(tab_indx)] = tab

            tab_indx = keygen()
        if diz[diz_indx]['tables']:
            diz_indx +=1

print("2. DONE - all tables processed")

#create folder
cur_dir = os.getcwd()
new_dir = os.path.join(cur_dir, 'wiki_tables', file_name)

if not os.path.exists(new_dir):
    os.makedirs(new_dir)


#save each dictionary
for el in tqdm(diz):
    with gzip.open(os.path.join(new_dir, 'diz_' + diz[el]['wiki_id'] + '.json.gz'), 'wt') as fd:
        json.dump(diz[el], fd)

print("3. DONE - dictionaries saved")

#save dump info
with open(os.path.join(new_dir, 'dump_info_' + file_name +'.json'), 'w') as f:
    json.dump(diz_info, f)

print("4. DONE - dump file saved")