#!/usr/bin/env python
# coding: utf-8
# +
import wikitextparser as wtp
from bs4 import BeautifulSoup, SoupStrainer

import re
import numpy as np

import gzip
import json

import html
from tqdm import tqdm

import unidecode
import sys
import os


# +


#file_name = 'enwiki-20220720-pages-articles-multistream2.xml-p41243p151573.bz2'
file_name = sys.argv[1]                                                    #recall by using "python script_name.py filename.bz2

#file_name = 'enwiki-20220520-pages-articles-multistream1.xml-p1p41242.bz2'  #write file name

# +


#open ONE bz2 file
import bz2
with bz2.open(file_name, 'rb') as f:
    text = f.read()


# +


import random, string
def keygen():
    x = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    return x.upper()


# #### Useful Regex:
#
# * links are between double square brackets &emsp; &emsp; `(?<=\[\[)(.*?)(?=\]\])`
# * tables captions begin with &emsp; &emsp; &emsp; `|+`

# +


ref_regex = r'(?<=\<ref)(.*)(?=\<\/ref>)'          #supercite links
ref2_regex = r'(?<=\<ref)(.*)(?=\>)'               #other supercite links format
sup_regex = r'(?<=\<sup>)(.*)(?=\<\/sup>)'         #superscripts regex
apex_regex = r'(?<=\{\{)(.*)(?=\}\})'              #apex mouse-over links
#cellnum_regex = "(?<=\{\{formatnum\:)(.*)(?=\}\})" #numbers formatted with 'formatnum' in cells
cellnum_regex = r'{{formatnum:(.*)}}'
span_regex = r"\<span(.*?)\>"                       #span


# +


def clean_cell(string):
    string = str(string)                                       #convert to string
    clean = string.replace('<br />', " ")                      #spaces
    clean = re.sub(sup_regex, "", clean)
    clean = re.sub(ref_regex, "", clean)
    clean = re.sub(ref2_regex, "", clean)
    clean = re.sub(span_regex, "", clean)
    # formatum
    num_match = re.search(cellnum_regex, clean)
    if num_match:
        num_span = num_match.span()
        clean = clean[:num_span[0]] + num_match.group(1) + clean[num_span[1]:]
    #if '{{' in clean:
    #    if 'formatnum' in clean:                               #is a number
    #        try:
    #            clean = re.search(cellnum_regex, clean).group(0)
    #        except AttributeError:
    #            pass
    #    else: #is a mouse-over link
    #        clean = re.sub(apex_regex, "", str(clean))

    clean = clean.rstrip().lstrip()                            #remove spaces before and after string
    if clean.startswith("'") or clean.endswith("'"):
        while clean.startswith("'") or clean.endswith("'"):
            clean = clean[1:-1]

#    if clean.startswith(" ") or clean.endswith(" "):
#        while clean.startswith(" ") and clean.endswith(" "):
#            clean = clean.rstrip().lstrip()                    #remove spaces before and after string

    clean = clean.rstrip().lstrip()                            #remove spaces before and after string
    clean = clean.replace('*','')                              #points
    #other cleaning criteria?
    clean = clean.replace('<ref>','').replace('</ref>','')     #supercite residuals
    clean = clean.replace('\n','')                             #line breaks
    # clean = clean.replace('{{','').replace('}}','')            #mouse over & formatnum residuals
    # clean = clean.replace('[[','').replace(']]','')            #links residuals
    clean = clean.replace('<sub>','').replace('</sub>','')     #pedice
    clean = clean.replace('<sup>','').replace('</sup>','')     #apice
    clean = clean.replace('<span>','').replace('</span>','')   #span residuals
    clean = clean.replace('<code>','').replace('</code>','')   #code residuals
    clean = clean.replace('<br>','').replace('<br/>','')       #other spaces left
    clean = clean.replace('<small>','').replace('</small>','') #small text format
    clean = clean.replace('<poem>','').replace('</poem>','')   #poem format
    clean = clean.replace("\xa0",' ')                          #unicode spacing
    clean = clean.replace("&nbsp;",' ')                        #html spacing without breaking line (scappa all'unescape)
    clean = clean.replace("&amp;",'&')                         #e commerciale
    clean = clean.replace("&ndash;",'-')                       #en-dash
    #clean = clean.replace("'",'')                             #bold --> do not use in case of entity recognition

    if clean.startswith(" ") or clean.endswith(" "):
        while clean.startswith(" ") or clean.endswith(" "):
            clean = clean.rstrip().lstrip()                    #remove spaces before and after string

    if 'file:' in clean.lower():                               #img files are linked but unuseful
        return 'IMAGE'
    if 'help:' in clean.lower():                               #help pages are not listed as normal wiki pages in LamAPI
        return 'HELP_PAGE'
    if 'wikipedia:wikiproject' in clean.lower():
        return 'WIKI_PROJ_PAGE'

    # wtp plain text
    clean = wtp.parse(clean).plain_text()

    clean = clean.replace('{{}}', '').replace('[[]]', '')

    return clean


# apply clean_cell elementwise
clean_cell_v = np.vectorize(clean_cell)

# +


#soup = BeautifulSoup(sub_text, "html.parser")
parse_only = SoupStrainer('page')                                         #parsing using <page>...<\page>

#some useful samples
#sub_text = text[220000000:270000000]
#sub_text = text[:3000000]

soup = BeautifulSoup(text, "html.parser", parse_only=parse_only)          #all tables
#soup = BeautifulSoup(sub_text, "html.parser", parse_only=parse_only)     #for sub-sampling

#it may takes a few minutes, be patient!


# +


def normalize_links(text):
    #if '|' in text:                               #wiki format of linking to another wiki page is "official_page_title|alias"
    #    text = text.split('|')[0]
    text = text.strip()
    text = text.replace(' ','_')              #replacing spaces with underscore
    try:
        text = text[0].capitalize() + text[1:]    #capitalizing first letter w/out changing the rest
    except IndexError:
        return text

    #text = text.title()                          #capitalizing first letter of each word
    return text

def debug_clean(_text):
    print('CC', clean_cell(_text))
    print('WTP', wtp.parse(_text).plain_text())
    print('BS', BeautifulSoup(_text, 'lxml').text)

# +


diz_info = {'tot_pages': len(soup), #tot pages read
            'tot_tab': 0,           #tot tables
            'tot_linked_tab': 0,    #tot tables with at least ONE link
            'keep_tab': 0,          #tot keeped tables
            'keep_rows': 0,         #tot keeped rows
            'keep_cols': 0          #tot keeped cols
           }



# +


diz = {}
diz_indx = 1                                                            #dictionary index to store each page in a dict element

for page in tqdm(soup):
    page = html.unescape(str(page))

    tab_indx = keygen()                                                  #table index
    if 'wikitable' in str(page):                                         #wikitable filter for pages w/ at least a table

        id_ = re.search("(?<=\<id>)(.*?)(?=\</id>)", str(page))          #page id and
        tit = re.search("(?<=\<title>)(.*?)(?=\</title>)", str(page))    #page title

        id_page = id_.group(0)
        title = tit.group(0)

        diz[diz_indx] = {'wiki_id':id_page,                              #initializing dictionary element
                         'title':title,
                         'tables':{}}

        parsed = wtp.parse(str(page))

        for table in parsed.tables:
            diz_info['tot_tab']+=1
            if table.wikilinks:                                          #filter tables w/ at least a linked cell
                diz_info['tot_linked_tab']+=1
                data = table.data() #(span=False)                        #creating a not-nested table

                tab = {'caption':clean_cell(table.caption),              #initializing table element
                         'header': [],
                         'cells': []}                                    #initializing caption & header

                for first_line, line in enumerate(data):                 #first_line is a index to check header
                    tab_line = []

                    if first_line == 0:                              #header
                        header_x = 0
                        tab['header'] = []                     #header is set to None
                        _header_cells = table.cells()
                        while header_x < len(_header_cells) and _header_cells[header_x][0] and _header_cells[header_x][0].is_header:
                            _current_header = [clean_cell(_head_cell).replace('!','')\
                                for _head_cell in table.data()[header_x]]
                            tab['header'].append(_current_header)
                            header_x += 1

                    for indx, cell in enumerate(line):
                                         #iterating cell in a line
                        cell_str = str(cell).replace('\n','')            #convert to string and remove \n

                        #find link
                        #link_mat = re.search("(?<=\[\[)(.*?)(?=\]\])", cell_str)
                        cell_parsed = wtp.parse(cell_str)
                        links_wtp = cell_parsed.wikilinks

                        #CRITERION:
                        #-- if cell is linked
                        #-- cell starts and ends w/ square brackets
                        #-- ONLY ONE link is recognized
                        #if link_mat and cell_str.startswith('[[') and cell_str.endswith(']]') and len(more_than_one) < 2:
                        #    cell_str = clean_cell(cell_str)
                        # only one link occupying the whole cell
                        if len(links_wtp) == 1 and len(links_wtp[0].plain_text()) == len(cell_parsed.plain_text()):
                            #images, link to wiki help pages and wiki project pages are not considered as standard links
                            # if cell_str == 'file_img':
                            #     tab_line.append('IMAGE')
                            #     tab_line.append('')
                            # elif cell_str == 'help_page':
                            #     tab_line.append('HELP_PAGE')
                            #     tab_line.append('')
                            # elif cell_str == 'wiki_project':
                            #     tab_line.append('WIKI_PROJ_PAGE')
                            #     tab_line.append('')
                            # else:
                            #     # normalize later
                            #     # tab_line.append(clean_cell(cell_str))
                            tab_line.append(cell_str)
                            tab_line.append(normalize_links(links_wtp[0].target))

                        else:
                            tab_line.append(cell_str)
                            tab_line.append('')

                    tab['cells'].append(tab_line)
                tab['cells'] = np.matrix(tab['cells'])

                #table w/out any content are not considered
                if tab['cells'].size == 0:
                    continue

                link_mat = tab['cells'][:,1::2]               # link matrix and conversion of true,false string to boolean
                text_mat = tab['cells'][:,::2]                           #texts matrix

                assert text_mat.shape == link_mat.shape                  #link matrix and text matrix MUST have the same dimension

                link_sum = np.array(np.sum(link_mat != '', axis = 0)).reshape(-1)          #sum of links

                assert link_sum.shape[0] == text_mat.shape[1]

                current_max = np.amax(link_sum)
                if current_max >= 3:                                     #at least 3 links MUST be in a single column
                    #target array is considered as such if is the "more linked" compared to other columns
                    targ_arr = np.argwhere(link_sum == current_max).reshape(-1,)

                    #images, link to wiki help pages and wiki project pages are not considered as standard links
                    # for x, _line in enumerate(text_mat):
                    #     for y, _cell in enumerate(_line):
                    #         new_cell = clean_cell(_cell)
                    #         if new_cell == 'file_img':
                    #             new_cell = 'IMAGE'
                    #             link_mat[x,y] = ''
                    #         elif new_cell == 'help_page':
                    #             new_cell = 'HELP_PAGE'
                    #             link_mat[x,y] = ''
                    #         elif new_cell == 'wiki_project':
                    #             new_cell = 'WIKI_PROJ_PAGE'
                    #             link_mat[x,y] = ''
                    #         text_mat[x,y] = new_cell

                    text_mat = clean_cell_v(text_mat)

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


# +
#create folder
cur_dir = os.getcwd()
new_dir = os.path.join(cur_dir, 'wiki_tables', file_name)

if not os.path.exists(new_dir):
    os.makedirs(new_dir)


# +


#save each dictionary
for el in tqdm(diz):
    with gzip.open(os.path.join(new_dir, 'diz_' + diz[el]['wiki_id'] + '.json.gz'), 'wt') as fd:
        json.dump(diz[el], fd)


# +


#save dump info
with open(os.path.join(new_dir, 'dump_info_' + file_name +'.json'), 'w') as f:
    json.dump(diz_info, f)

