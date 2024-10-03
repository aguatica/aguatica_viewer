# aguaticaviewer/auth.py

import pyepicollect as pyep
from aguaticaviewer.config import CLIENT_ID, CLIENT_SECRET
import pprint

pp = pprint.PrettyPrinter(indent=2)

_token = None
def request_token():
    global _token
    try:
        _token = pyep.auth.request_token(CLIENT_ID, CLIENT_SECRET)
        pp.pprint(_token)
        return _token
    except Exception as e:
        print(f"Error requesting token: {e}")
        return None





