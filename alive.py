from time import sleep
from requests import get as rget
from os import environ
from logging import error as logerror
from urllib.parse import urlparse

BASE_URL = environ.get('BASE_URL', None)
try:
    if len(BASE_URL) == 0:
        raise TypeError
    BASE_URL = BASE_URL.rstrip("/")
except TypeError:
    BASE_URL = None
BASE_URL_PORT = environ.get('PORT', None)

parsed_url = urlparse(BASE_URL)
if not parsed_url.port:
    if BASE_URL_PORT is not None and BASE_URL is not None:
        while True:
            try:
                rget(BASE_URL).status_code
                sleep(600)
            except Exception as e:
                logerror(f"alive.py: {e}")
                sleep(2)
                continue
else:
    print("Port is specified in the BASE_URL; not executing ALIVE process.")
