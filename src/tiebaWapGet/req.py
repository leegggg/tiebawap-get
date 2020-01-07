import requests
from requests.adapters import HTTPAdapter
from common import MAX_RETRY

proxies = {
  "http": "http://redqueen.lan.linyz.net:7890",
  "https": "http://redqueen.lan.linyz.net:7890",
}

req = requests.Session()
req.proxies.update(proxies)
httpAdapter = HTTPAdapter(max_retries=MAX_RETRY)

req.mount('http://', httpAdapter)
req.mount('https://', httpAdapter)

