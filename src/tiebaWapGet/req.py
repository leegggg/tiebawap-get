import requests
from requests.adapters import HTTPAdapter
from common import MAX_RETRY

req = requests.Session()
httpAdapter = HTTPAdapter(max_retries=MAX_RETRY)

req.mount('http://', httpAdapter)
req.mount('https://', httpAdapter)

