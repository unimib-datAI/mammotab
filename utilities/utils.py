import random, string
import re
import pickle
import wikitextparser as wtp
from bs4 import BeautifulSoup

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
    
def normalize_links(text):
    text = text.strip().replace(' ', '_')
    try:
        text = text[0].capitalize() + text[1:]
    except IndexError:
        return text
    return text

def clean_links(link):
    if '#' in link:
        # remove links that refer to a page section
        return ''
    else:
        return link
    
def debug_clean(_text):
    print('CC', clean_cell(_text))
    print('WTP', wtp.parse(_text).plain_text())
    print('BS', BeautifulSoup(_text, 'lxml').text)

def keygen():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8)).upper()

def clean_cell(string):
    string = str(string)  # Ensure the input is a string
    soup = BeautifulSoup(string, 'html.parser')

    # CE1 RULE Remove tags but keep their content
    for tag in soup(['sup', 'ref', 'span', 'sub', 'code', 'small', 'poem']):
        tag.unwrap()
    
    # CE2 RULE Remove breaks and convert to space
    for br in soup.find_all('br'):
        br.replace_with(' ')

    # CE3 RULE Remove all tags and join different parts of the text with a space
    clean = soup.get_text(separator=' ').strip()

    # CE4 RULE removing "{{formatnum:"" and "}}" from strings
    clean = re.sub(r"{{formatnum:(.*?)}}", r"\1", clean)

    # Parse remaining wikitext
    clean = wtp.parse(clean).plain_text()

    # CE5 RULE remove the † symbol
    clean = clean.replace('†','')

    # CE6 RULE Remove text between brackets
    clean = re.sub(r"(.*?)\[\[(.*?)\]\]", r"\1", clean)
    clean = re.sub(r"(.*?)\{\{(.*?)\}\}", r"\1", clean)
    clean = re.sub(r"(.*d)\{\{(.*?)\}\}", r"\1", clean)

    # CE7 RULE Final cleaning
    clean = clean.replace('\xa0', ' ').replace('&nbsp;', ' ').replace('&amp;', '&').replace('&ndash;', '-')

    # CE8 RULE Remove any remaining artifacts
    clean = clean.replace('{{}}', '').replace('[[]]', '').replace('()', '').replace('"', '')

    # CE9 RULE Remove leading and trailing spaces
    clean = clean.strip()

    # CE10 RULE Handle specific page types
    clean_lower = clean.lower()
    if 'file:' in clean_lower:
        return 'IMAGE'
    if 'help:' in clean_lower:
        return 'HELP_PAGE'
    if 'wikipedia:wikiproject' in clean_lower:
        return 'WIKI_PROJ_PAGE'

    return clean