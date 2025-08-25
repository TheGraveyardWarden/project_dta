import requests as req
from requests.adapters import HTTPAdapter

POOLCONNECTIONS = 10
POOLMAXSIZE = 20

class Req:
    def __init__(self):
        self.headers = {
            "Connection": "keep-alive",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:141.0) Gecko/20100101 Firefox/141.0"
        }

        adapter = HTTPAdapter(pool_connections=POOLCONNECTIONS, pool_maxsize=POOLMAXSIZE)
        self.session = req.Session()
        self.session.mount("https://", adapter)
        self.session.headers.update(self.headers)
