
#!/usr/bin/env python3
from importlib.resources import path
import requests
from string import Template
import os
import sys
from bs4 import BeautifulSoup

API_URL = 'https://api.crossref.org/works/{doi}'
API_URL_DATACITE = 'https://mds.test.datacite.org/media/{doi}'

ARXIV = 'arxiv'
CROSSREF = 'crossref'
DX = 'dx'

short_journal_name_dict = { 'JournalofMagnetismandMagneticMaterials':'JMMM',
                            'JournalofAppliedPhysics': 'JAP',
                            'ApplPhysLett': 'APL',
                            'PhysRevLett': 'PRL',
                            'PhysRevApplied': 'PRA',
                            'SciRep': 'SR',
                            'PhysRevB': 'PRB',
                            'ACSApplMaterInterfaces': 'ACSami',
                            'JPhysD:ApplPhys': 'JPDap',
                            'NatureNanotech': 'NatNano',
                            'NatCommun': 'NatCom',
                            'JPhysC:SolidStatePhys': 'JPCssp',
                            'jnanoscinanotechnol': 'JNN',
                            'NatNanotechnol': 'NatNano',
                            'NatureMater': 'NatMat',
                            'PhysStatusSolidiB': 'PSSB'}
def make_request(doi):
    if  ARXIV in doi or 'arXiv' in doi:
        r = requests.get(doi)
        r.raise_for_status()
        output = BeautifulSoup(r.content, "html.parser")
        method = ARXIV
    else:
        doi_ = doi.replace('https://doi.org/','')
        r = requests.get(API_URL.format(doi=doi_))
        print(doi_)
        r.raise_for_status()
        req_json = r.json()
        if not req_json["status"] == "ok":
            raise Exception("DOI API was not OK!")
        output = req_json["message"]
        method = CROSSREF
    
    print(f"Making request for {doi} with {method}")    
    return [method, output]

def clean_abstract(abstract):
    to_remove_list = ['<jats:title>Abstract</jats:title>']
    for to_remove in to_remove_list:
        abstract = abstract.replace(to_remove, '')

    to_remove_list = ['p', 'inline-formula', 'alternatives', 'tex-math']
    for to_remove in to_remove_list:
        REM1 = '<jats:{to_rem}>'
        REM2 = '</jats:{to_rem}>'
        for rem in [REM1.format(to_rem=to_remove), REM2.format(to_rem=to_remove)]:
            abstract = abstract.replace(rem, '')

    to_remove_list = ['msup',]
    for to_remove in to_remove_list:
        REM1 = '<jats:{to_rem}>'
        REM2 = '</jats:{to_rem}>'
        for rem in [REM1.format(to_rem=to_remove), REM2.format(to_rem=to_remove)]:
            abstract = abstract.replace(rem, '')
        abstract_part = abstract.split('mml:math')
        abstract = ' '.join(abstract_part[::2])
        abstract = abstract.replace('< >', '')
        abstract = abstract.replace('$$', '$')
    return abstract

def get_author(author, origin):
    '''output: family-name_given-name'''
    if origin == CROSSREF:
        family_name, given_name = [author[key] for key in ['family', 'given']]
    elif origin == ARXIV:
        family_name, given_name = author.split(', ')
    else:
        sys.exit(f'Invalid origin: {origin}')

    return '_'.join([name.replace(' ','-').replace('.','') for name in [family_name, given_name]])

def get_journal_short(journal):
    try:
        journal_name = journal[0].replace(' ','').replace('.', '')
    except IndexError:
        journal_name = 'unknown'
        print(f'unknow journal name ({journal})')
    return journal_name

def get_name_note(author, year, journal):
    print(author)
    author_ = author.split('_')[0]
    return ''.join([author_,str(year),'_',journal])

def get_tag_list(year, journal, authors):
    tags = f'- #Y/{year}\n- #J/{journal}'
    author_list = [f'- #A/{author}' for author in authors]
    return '\n'.join([tags, *author_list])

def create_md_file(doi, path, template = 'paper_template.md'):
    output = make_request(doi)
    print(f'create md file with {output[0]}')
    authors = []
    if output[0] == CROSSREF:
        json_msg = output[1]
        try:
            abstract = clean_abstract(json_msg['abstract'])
        except KeyError:
            print('No abstract found')
            abstract = 'not found'
        for author in json_msg['author']:
            authors.append(get_author(author, CROSSREF))
        try :
            year = json_msg['published-print']['date-parts'][0][0]
        except KeyError:
            year = -1

        journal = get_journal_short(json_msg['short-container-title'])
        title = json_msg['title'][0]
    
    elif output[0] == ARXIV:
        soup = output[1]
        for meta in soup.find_all('meta'):
            if meta.get('name') == 'citation_author':
                authors.append(get_author(meta.get('content'), ARXIV))
            elif meta.get('name') == 'citation_title':
                title = meta.get('content')
            elif meta.get('name') == 'citation_date':
                year = int(meta.get('content').split('/')[0])
                assert year >1900, print('Year is not valid: ', year)
            elif meta.get('name') == 'citation_abstract':
                abstract = meta.get('content')
            journal = ARXIV
    else:
        sys.exit(f'unvalid method: {output[0]}')

    # search if shorter name of journal exist
    if journal in short_journal_name_dict.keys():
        journal = short_journal_name_dict[journal] 
    tags = get_tag_list(year, journal, authors)
    name = get_name_note(authors[0], year, journal)
    path_script = os.path.dirname(os.path.realpath(__file__))
    with open(os.path.join(path_script,template), 'r') as f:
        src = Template(f.read())
    result = src.substitute(title=title, abstract=abstract, tags=tags, DOI=doi, name=''.join([name, '.pdf']))
    with open(os.path.join(path, ''.join([name, '.md'])), 'x') as f:
        f.write(result)
    
    print('output:', authors, title, year, journal, name.replace('.md', ''))    

if __name__ == '__main__':
    create_md_file(sys.argv[1], sys.argv[2])


