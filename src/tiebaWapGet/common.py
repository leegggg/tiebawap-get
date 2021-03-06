import datetime
import uuid
import random

DB_URL = 'sqlite:///./data/tieba.baidu.com.db'

PAGE_SIZE_POST = 30
PAGE_SIZE_THREAD = 20

addUrl = "/q---{uuid:s}%3AFG%3D1--1-3-0--2--wapp_{ts:s}".format(
    uuid=str(uuid.uuid4()).replace('-', '').upper(),
    ts=str(datetime.datetime.now().timestamp()*1000).replace('.', '_'))

URL_BASE = "http://tieba.baidu.com/mo{}/".format(addUrl)
URL_BASE_TB = "{}m".format(URL_BASE)
URL_BASE_FLR = "{}flr".format(URL_BASE)

FALL_BACKDATE = datetime.datetime(1970, 1, 1, 0, 0, 0)


USER_AGENT_UC_MIDP = "UCWEB/2.0 (MIDP-2.0; U; zh-CN; SM-P601) U2/1.0.0 UCBrowser/3.4.3.532 U2/1.0.0 Mobile"
USER_AGENT_UC_FF_59_WIN = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:{v:d}.0) Gecko/20100101 Firefox/{v:d}.0".format(
    v=random.randint(54, 72))

REQUEST_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
    'User-Agent': USER_AGENT_UC_FF_59_WIN
}

MAX_RETRY = 10
MAX_LOOP = 10000
MAX_PN = 10000
RETRY_AFTER = 5
FATCH_SIZE = 200

STATUS_UNKNOW_ERROR = 1000

DUMMY_KW = "__dummy__"
THREAD_SIZE_SKIP = 10000

ATT_POST_STATUS_MADE = 1
NB_MAX_BLOCKED = 10


ATTACHEMENT_BASE_PATH = 'data/attachement/'
# ATTACHEMENT_OUT_BASE_PATH = 'e:\subhd\out'
