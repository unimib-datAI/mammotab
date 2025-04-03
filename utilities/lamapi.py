import requests,os
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import time

load_dotenv()

# Configure a session with retry logic and connection pooling
def create_lamapi_session():
    session = requests.Session()
    retries = Retry(
        total=5,  # Maximum number of retries
        backoff_factor=0.5,  # Exponential backoff
        status_forcelist=[500, 502, 503, 504]  # Retry on these status codes
    )
    adapter = HTTPAdapter(
        max_retries=retries,
        pool_connections=20,  # Number of connection pools to keep
        pool_maxsize=20  # Maximum connections per pool
    )
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

# Global session object
LAMAPI_SESSION = create_lamapi_session()

def call_lamapi(list_of, ent_typ):
    if ent_typ == 'entities':
        lam = 'entity/wikipedia-mapping'
    elif ent_typ == 'types':
        lam = 'entity/types'
    elif ent_typ == 'literals':
        lam = 'classify/literal-recognizer'
    elif ent_typ == 'aliases':
        lam = 'entity/aliases'
    else:
        return print('possible options: \n -entities \n -types \n -literals')

    payload = {}
    payload['json'] = list_of
    uri = os.environ.get('LAMAPI_ROOT') + lam + '?token={}'.format(os.environ.get('LAMAPI_TOKEN'))
    
    if ent_typ == 'aliases':
        uri = uri + '&lang=en'

    try:
        # Add small delay to prevent overwhelming the server
        time.sleep(0.1)
        
        # Use the configured session
        res = LAMAPI_SESSION.post(uri, json=payload, timeout=10)
        res.raise_for_status()  # Raise exception for bad status codes
        
        diz_temp = res.json()

        if ent_typ == 'entities' or ent_typ == 'aliases':
            source = 'wikidata'
            for el in diz_temp:
                if source in diz_temp[el]:
                    diz_temp[el] = diz_temp[el][source]
            return diz_temp

        elif ent_typ == 'types':
            if 'wikidata' in diz_temp:
                diz_temp = diz_temp['wikidata']
            diz_new = {}
            for key, value in diz_temp.items():
                if value['types']:
                    diz_new[key] = value['types']['P31']
            return diz_new

        elif ent_typ == 'literals':
            source = 'datatype'
            for el in diz_temp:
                diz_temp[el] = diz_temp[el][source]
            return diz_temp

    except Exception as e:
        print(f"Error calling LamAPI: {e}")
        return {}