import datetime

scoreUrlFormat = "https://www.meijutt.com/inc/ajax.asp?id={}&action=newstarscorevideo"
forumPageFormat = 'http://www.btbtt08.com/forum-index-fid-{}-page-{}.htm'
threadRegexp = 'http://www.btbtt08.com/thread-index-fid-(?P<fid>[0-9]+)-tid-(?P<tid>[0-9]+).htm'
attachementRegexp = 'http://www.btbtt08.com/attach-dialog-fid-(?P<fid>[0-9]+)-aid-(?P<aid>[0-9]+)-ajax-1.htm'
attachementUrlFormat = "http://www.btbtt08.com/attach-download-fid-{}-aid-{}.htm"
attachementUrlRegexp = "http://www.btbtt08.com/attach-download-fid-(?P<fid>[0-9]+)-aid-(?P<aid>[0-9]+).htm"
DB_URL = 'sqlite:///./data/tieba.baidu.com.db'

PAGE_SIZE_POST = 30
PAGE_SIZE_THREAD = 20

addUrl = "/q---785538BFFE3D92C21F541F83658AF269%3AFG%3D1--1-3-0--2--wapp_1557887161765_590"

URL_BASE = "http://tieba.baidu.com/mo{}/".format(addUrl)
URL_BASE_TB = "{}m".format(URL_BASE)
URL_BASE_FLR = "{}flr".format(URL_BASE)

FALL_BACKDATE = datetime.datetime(1970, 1, 1, 0, 0, 0)


USER_AGENT_UC_MIDP = "UCWEB/2.0 (MIDP-2.0; U; zh-CN; SM-P601) U2/1.0.0 UCBrowser/3.4.3.532 U2/1.0.0 Mobile"
USER_AGENT_UC_FF_59_WIN = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:59.0) Gecko/20100101 Firefox/59.0"

REQUEST_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
    'User-Agent': USER_AGENT_UC_FF_59_WIN
}

MAX_RETRY = 10
RETRY_AFTER = 5
FATCH_SIZE = 200

STATUS_UNKNOW_ERROR = 1000