import requests
from requests.adapters import HTTPAdapter
from common import MAX_RETRY
import os

proxies = {}

if os.environ.get("http_proxy"):
    proxies["http"] = os.environ.get("http_proxy")

if os.environ.get("https_proxy"):
    proxies["https"] = os.environ.get("https_proxy")

req = requests.Session()
if proxies:
    req.proxies.update(proxies)
httpAdapter = HTTPAdapter(max_retries=MAX_RETRY)

req.mount('http://', httpAdapter)
req.mount('https://', httpAdapter)
