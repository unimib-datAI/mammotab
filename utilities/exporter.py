import random,json

def add_random_typo(text):
    if not text:
        return text
    typo_index = random.randint(0, len(text) - 1)
    typo_char = random.choice('abcdefghijklmnopqrstuvwxyz')
    typo_text = text[:typo_index] + typo_char + text[typo_index + 1:]
    
    return typo_text

def AddAcronyms(table):
    with open('acronym.json', 'r') as f:
        acronym_dict = json.load(f)
    necols = []
    for i,col in enumerate(table['tags']):
        if col['tags']['col_type'] == 'NE':
            necols.append(i)
    for row in table['text']:
        for i,cell in enumerate(row):
            if i in necols and cell in acronym_dict:
                cell = acronym_dict[cell]
    return table

def AddAliases(table):
    # TODO NEW LAMAPI ENDPOINT
    return table

def AddTypos(table):
    necols = []
    for i,col in enumerate(table['tags']):
        if col['tags']['col_type'] == 'NE':
            necols.append(i)
    for row in table['text']:
        for i,cell in enumerate(row):
            if i in necols:
                cell = add_random_typo(cell)
    return table

def ApproximateNumbers(table):
    litcols = []
    for i,col in enumerate(table['tags']):
        if col['tags']['col_type'] == 'LIT' and col['tags']['lit_type'] == 'NUMBER':
            litcols.append(i)
    for row in table['text']:
        for i,cell in enumerate(row):
            if i in litcols:
                cell = str(int(cell) + random.randint(-1,1))
    return table

