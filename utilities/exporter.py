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
    necells = set()
    for row in table['entity']:
        for col in necols:
            col_index = int(col)
            if col_index in row and row[col_index]!='':
                necells.add(row[col_index])
    aliases = call_lamapi(list(necells), 'aliases')
    for col_index,col in enumerate(table['text']):
        entity = table['entity'][col_index]
        for cell_index,cell in enumerate(col):
            entity_cell = entity[cell_index]
            #if col_index in necols:
            if entity_cell in aliases:
                if "en" in aliases[entity_cell]["aliases"]:
                    table['text'][col_index][cell_index] = random.choice(aliases[entity_cell]["aliases"]["en"])
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

