import random,json
import os
from typing import Set
from utilities.lamapi import call_lamapi

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

def AddAcronyms(table):
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'acronyms.json'), 'r') as f:
        acronym_dict = json.load(f)
    necols = GetNeColumns(table)
    for row in table['text']:
        for i,cell in enumerate(row):
            if i in necols and cell in acronym_dict:
                cell = acronym_dict[cell]
    return table

def AddAliases(table):
    necols = GetNeColumns(table)
    call_lamapi(table['entity'], 'aliases')
    necells = Set()
    for row in table['text']:
        for i,cell in enumerate(row):
            if i in necols:
                necells.add(cell)
    aliases = call_lamapi(list(necells), 'aliases')
    for row in table['text']:
        for i,cell in enumerate(row):
            entity = table['entity'][i][row]
            if i in necols and cell in aliases:
                cell = random.choice(aliases[entity]["aliases"]["en"])
    return table

def AddTypos(table):
    necols = GetNeColumns(table)
    for row in table['text']:
        for i,cell in enumerate(row):
            if i in necols:
                cell = add_random_typo(cell)
    return table

def ApproximateNumbers(table):
    litcols = GetLitColumns(table)
    for row in table['text']:
        for i,cell in enumerate(row):
            if i in litcols:
                cell = str(float(cell) + random.randint(-1,1))
    return table

