import urllib.request as request
from bs4 import BeautifulSoup
import re,json

multipleAcronyms = False
multipleAcroLines = False
listOfAbbr = []
alphabets = ['0-9', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
acroFile = open("acronyms.json", "w")

acrolist = {}
for alphabet in alphabets:
    url = "https://en.wikipedia.org/wiki/List_of_acronyms:_" + alphabet
    print(url)

    html = request.urlopen(url).read()
    soup = BeautifulSoup(html)

    content_div = soup.select_one('#mw-content-text > div:nth-of-type(1)')

    if content_div:
        for li in content_div.find_all('li'):
            text = li.get_text()
            tarr = text.split(" – ")
            if len(tarr) > 1:
                tarr[1] = (re.sub(r"(.*?)\[(.*?)\]", r"\1", tarr[1]))
                tarr[1] = (re.sub(r"(.*?)\((.*?)\)", r"\1", tarr[1])).strip().replace('  ',' ')
                if tarr[1].find('"') != -1 and tarr[1].find(':') != -1:
                    tarr[1] = tarr[1].split(":")[0]
                tarr[1] = tarr[1].replace('"','')
                tarr[1] = tarr[1].split(';')[0].strip()
                tarr[1] = tarr[1].split('/')[0].strip()
                tarr[1] = tarr[1].split('such as')[0].strip()
                tarr[1] = tarr[1].replace('many, including','').replace(')','').replace('(','').strip()
                tarr[0] = tarr[0].split('or')[0].strip()
                print(tarr)
                acrolist[tarr[1].lower()] = tarr[0]
acroFile.write(json.dumps(acrolist))
