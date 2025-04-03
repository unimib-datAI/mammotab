import random,json
import os,time
from typing import Set
from utilities.lamapi import call_lamapi
from dotenv import load_dotenv
load_dotenv()

ADDACRONIMSPERCENT = int(os.getenv('ADDACRONIMSPERCENT') or 70)
ADDTYPOSPERCENT = int(os.getenv('ADDTYPOSPERCENT') or 50)
APPROXIMATENUMBERSPERCENT = int(os.getenv('APPROXIMATENUMBERSPERCENT') or 30)
ADDALIASESPERCENT = int(os.getenv('ADDALIASESPERCENT') or 70)

def add_random_typo(text):
    if not text:
        return text
    typo_index = random.randint(0, len(text) - 1)
    typo_char = random.choice('abcdefghijklmnopqrstuvwxyz')
    typo_text = text[:typo_index] + typo_char + text[typo_index + 1:]
    
    return typo_text

def GetNeColumns(table):
    necols = []
    for col in table['tags']:
        if isinstance(table['tags'][col], dict) and 'tags' in table['tags'][col]:
            if table['tags'][col]['tags'].get('col_type') == 'NE':
                necols.append(col)
    return necols

def GetLitColumns(table, lit_type="NUMBER"):
    litcols = []
    for col in table['tags']:
        if isinstance(table['tags'][col], dict) and 'tags' in table['tags'][col]:
            if table['tags'][col]['tags'].get('col_type') == 'LIT' and table['tags'][col]['tags']['lit_type'] == lit_type:
                litcols.append(col)
    return litcols

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'acronyms.json'), 'r') as f:
    acronym_dict = json.load(f)
def AddAcronyms(table):
    acro = 0
    acrocols = []
    necols = GetNeColumns(table)
    for row in table['text']:
        for i,cell in enumerate(row):
            lcell = cell.lower()
            if str(i) in necols and lcell in acronym_dict:
                if random.randint(1,100) <= ADDACRONIMSPERCENT:
                    if i not in acrocols:
                        acrocols.append(i)
                    cell = acronym_dict[lcell]
                    acro += 1
    return table,acro,len(acrocols)

def AddAliases(table):
    aliases_added = 0
    aliasescols = []
    necols = GetNeColumns(table)
    necells = set()
    for col_index,row in enumerate(table['entity']):
        if str(col_index) in necols:
            for col in row:
                if col!='':
                    necells.add(col)
    time.sleep(0.1)
    aliases = call_lamapi(list(necells), 'aliases')
    for col_index,col in enumerate(table['text']):
        entity = table['entity'][col_index]
        for cell_index,cell in enumerate(col):
            entity_cell = entity[cell_index]
            #if col_index in necols:
            if entity_cell in aliases:
                if "en" in aliases[entity_cell]["aliases"] and random.randint(1,100) <= ADDALIASESPERCENT:
                    if col_index not in aliasescols:
                        aliasescols.append(col_index)
                    table['text'][col_index][cell_index] = random.choice(aliases[entity_cell]["aliases"]["en"])
                    aliases_added += 1
    return table,aliases_added,len(aliasescols)

def AddTypos(table):
    typos_added = 0
    typoscols = []
    necols = GetNeColumns(table)
    for row in table['text']:
        for i,cell in enumerate(row):
            if str(i) in necols and random.randint(1,100) <= ADDTYPOSPERCENT:
                cell = add_random_typo(cell)
                typos_added += 1
                if i not in typoscols:
                    typoscols.append(i)
    return table,typos_added,len(typoscols)

def ApproximateNumbers(table):
    approx = 0
    approxcols = []
    litcols = GetLitColumns(table)
    if len(litcols) == 0:
        return table,approx,0
    for row in table['text']:
        for i,cell in enumerate(row):
            if str(i) in litcols:
                try:
                    float(cell)
                except:
                    continue
                if random.randint(1,100) <= APPROXIMATENUMBERSPERCENT:
                    if i not in approxcols:
                        approxcols.append(i)
                    cell = str(float(cell) + random.randint(-1,1))
                    approx += 1
    return table,approx,len(approxcols)

