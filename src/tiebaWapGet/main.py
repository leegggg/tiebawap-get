from urllib.parse import urlparse, parse_qs
from bs4 import BeautifulSoup
from bs4.element import Tag
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from common import URL_BASE_TB, REQUEST_HEADERS, FALL_BACKDATE, DB_URL
from common import DUMMY_KW, MAX_LOOP, MAX_PN, THREAD_SIZE_SKIP
from common import MAX_RETRY, RETRY_AFTER, URL_BASE_FLR
from common import ATT_POST_STATUS_MADE
from tbDAO import Base, PostHeader, Content, Content_HTML
from tbDAO import Thread, ThreadError, ThreadHeader
from attachementUtil import makeEmptyAttachementHeader, makeEmptyAttachement
from dateutil import parser as DateParser
import logging
import re
from req import req

"m?kz=125327888&pn=30"


def insertOrIgnoreAll(objs, engine, merge=False):
    Session = sessionmaker(bind=engine)
    count = 0
    for link in objs:
        try:
            session = Session()
            if not merge:
                session.add(link)
            else:
                session.merge(link)
            session.commit()
            count += 1
        except IntegrityError:
            pass


def parseDate(dateStr):
    import re
    # 4-26 01:34
    # 2016-6-28
    # 12:36

    current = datetime.now()
    if re.match("[0-9]{1,2}:[0-9]{1,2}", dateStr):
        dateStr = "{} {}".format(current.strftime('%m-%d'), dateStr)

    if re.match("[0-9]{1,2}-[0-9]{1,2} [0-9]{1,2}:[0-9]{1,2}", dateStr):
        dateStr = "{}-{}".format(current.strftime('%Y'), dateStr)

    try:
        current = DateParser.parse(dateStr)
    except (ValueError, OverflowError):
        logging.debug(
            "Failed to parse date string {} use {} as fall back.".format(dateStr, current))

    return current


def readAdditionalData(kz, pn, floor) -> Tag:
    """
    m?kz=125327888&pn=0&lp=6015&spn=2&global=1&expand=2
    m?kz=125327888&pn=0&global=1&expand=2
    """
    param = {
        "kz": kz,
        "pn": pn,
        "expand": floor,
        "global": 1
    }
    ret = req.get(url=URL_BASE_TB, headers=REQUEST_HEADERS,
                  params=param, timeout=(30, 30))
    ret.encoding = 'utf-8'  # ret.apparent_encoding
    soup: BeautifulSoup = BeautifulSoup(ret.text, 'html.parser')
    postDivs = soup.select_one(
        'body > div > div.d:nth-child(4) > div.i:nth-child(1)')
    return postDivs


def parsePost(postDiv: Tag, kz, pn, flr=False, getFlr=False, parent_override: int = None, floor_override=-1) -> []:
    postHeader = PostHeader()
    content = Content()
    contentHtml = Content_HTML()
    attachments = []
    attHeaders = []
    posts = []

    postHeader.mod_date = datetime.now()

    dateSpan: Tag = postDiv.select_one("span.b")
    create_date = FALL_BACKDATE
    if dateSpan:
        dateStr = dateSpan.text.strip()
        create_date = parseDate(dateStr)
    postHeader.create_date = create_date

    replyATag: Tag = postDiv.select_one("a.reply_to")
    href = "#reply"
    hasFlr = False
    if replyATag:
        href = replyATag.attrs.get("href")
        if re.match(r'回复\([0-9]+\)', replyATag.text.strip()):
            hasFlr = True
    o = urlparse(href)
    param = parse_qs(o.query)
    pid = param.get("pid")
    if not pid:
        pid = '_kz_{}'.format(kz)
    else:
        pid = pid[0]

    # Disable flr for faster fetch
    if hasFlr and getFlr:
        flrPosts = readFlr(kz=kz, pid=pid)
        if flrPosts:
            posts.extend(flrPosts)

    if flr:
        pid = "_flr_{}-{}".format(parent_override, floor_override)

    un = None
    floor = None
    needExpend = False
    atts = []
    aTags = postDiv.select("a")
    for aTag in aTags:
        aTag: Tag
        href = aTag.attrs.get("href")
        if href and re.match(r"i\?.*un=.*", href):
            o = urlparse(href)
            param = parse_qs(o.query)
            un = param.get("un")
            if un:
                un = un[0]
        if href and re.match(r"m\?.*expand=.*", href):
            needExpend = True
            o = urlparse(href)
            param = parse_qs(o.query)
            floor = param.get("expand")
            if floor:
                floor = floor[0]

        if aTag.text and re.match(r"图", aTag.text.strip()):
            atts.append(href)

    postHeader.un = un

    # contentText = ''.join(postDiv.findAll(text=True, recursive=False))
    contentText = postDiv.getText(separator="\n", strip=True)
    contentSource = str(postDiv)

    if not floor:
        firstPart = contentText[:20]
        match = re.match(r"(?P<flood>[0-9]+)楼\..*", firstPart)
        if match:
            floor = match.group('flood')
    if not floor:
        floor = floor_override

    if needExpend:
        additionalPostDivTag = readAdditionalData(kz, pn, floor)
        if additionalPostDivTag:
            # contentText = "{}{}".format(contentText,additionalPostDivTag.getText(separator="\n",strip=True))
            # contentSource = "{}{}".format(contentText,str(additionalPostDivTag))
            contentText = additionalPostDivTag.getText(
                separator="\n", strip=True)
            contentSource = str(additionalPostDivTag)

    content.mod_date = datetime.now()
    content.content = contentText

    contentHtml.mod_date = datetime.now()
    contentHtml.content = contentSource

    postHeader.cid = pid
    content.cid = pid
    contentHtml.cid = pid

    postHeader.floor = int(floor)

    postHeader.flr = flr

    postHeader.parent = int(kz)
    if flr:
        postHeader.parent = int(parent_override)

    postHeader.pid = pid
    content.source = pid
    contentHtml.source = pid

    postHeader.to = None

    for href in atts:
        att = makeEmptyAttachement(floor, postHeader.parent, href)
        if att:
            attachments.append(att)
            header = makeEmptyAttachementHeader(att)
            if header:
                attHeaders.append(header)
                att.attId = header.link
                att.status = ATT_POST_STATUS_MADE

    post = {
        'header': postHeader,
        'text': content,
        'html': contentHtml,
        'attachments': attachments,
        'attachmentHeaders': attHeaders
    }

    posts.append(post)

    logging.debug(
        "Get post from thread {} page {} floor {} pid {}".format(kz, pn, floor, pid))
    return posts


def savePost(post: dict, engine):
    Session = sessionmaker(bind=engine)
    try:
        session = Session()
        pageDAO = post.get('header')
        if pageDAO:
            session.merge(pageDAO)
        session.commit()
    except Exception as e:
        logging.warning("Error save page {} with {}".format(post, str(e)))

    try:
        session = Session()
        scoreDAO = post.get('text')
        if scoreDAO:
            session.merge(scoreDAO)
        session.commit()
    except Exception as e:
        logging.warning("Error save text {} with {}".format(post, str(e)))

    try:
        session = Session()
        scoreDAO = post.get('html')
        if scoreDAO:
            session.merge(scoreDAO)
        session.commit()
    except Exception as e:
        logging.warning("Error save html {} with {}".format(post, str(e)))

    try:
        links = post.get('attachments')
        insertOrIgnoreAll(links, engine, merge=True)
    except Exception as e:
        logging.warning(
            "Error save attachments {} with {}".format(post, str(e)))

    try:
        links = post.get('attachmentHeaders')
        insertOrIgnoreAll(links, engine, merge=True)
    except Exception as e:
        logging.warning(
            "Error save attachmentHeaders {} with {}".format(post, str(e)))


def saveThreadHead(thread: ThreadHeader, engine, error: ThreadError = None):
    Session = sessionmaker(bind=engine)
    try:
        session = Session()
        if thread:
            session.merge(thread)
        session.commit()
    except Exception as e:
        logging.warning(
            "Error save thread header {} with {}".format(thread, str(e)))

    try:
        session = Session()
        if error:
            session.merge(error)
        session.commit()
    except Exception as e:
        logging.warning(
            "Error save thread header {} with {}".format(error, str(e)))


def savePage(page: dict, engine):
    """
    'thread':thread,
    'posts': posts
    """
    Session = sessionmaker(bind=engine)
    try:
        session = Session()
        thread = page.get('thread')
        if thread:
            session.merge(thread)
        session.commit()
    except Exception as e:
        logging.warning("Error save thread {} with {}".format(thread, str(e)))
    posts = page.get("posts")
    for post in posts:
        savePost(post=post, engine=engine)


def readThreadPage(kw, kz, pn, good=None, getFlr=False) -> {}:
    param = {
        "kz": kz,
        "pn": pn
    }

    ret = req.get(url=URL_BASE_TB, headers=REQUEST_HEADERS,
                  params=param, timeout=(30, 30))
    ret.encoding = 'utf-8'  # ret.apparent_encoding
    soup: BeautifulSoup = BeautifulSoup(ret.text, 'html.parser')
    titleTag: Tag = soup.select_one("body > div > div.bc.p > strong")

    thread = Thread()
    thread.mod_date = datetime.now()
    if titleTag:
        thread.title = titleTag.text
    thread.kz = kz
    thread.kw = kw
    thread.good = good
    userTag = soup.select_one(
        "body > div > div:nth-child(4) > div:nth-child(1) > span.g > a")
    if userTag:
        href = userTag.attrs.get("href")
        o = urlparse(href)
        param = parse_qs(o.query)
        un = param.get("un")
        if un:
            un = un[0]
            thread.auth = un

    postDivs = soup.select('div .i')
    posts = []
    for postDiv in postDivs:
        for count in range(MAX_RETRY):
            try:
                post = parsePost(postDiv=postDiv, kz=kz, pn=pn, getFlr=getFlr)
                posts.extend(post)
            except Exception as e:
                logging.warning(
                    "Error get post retry {}/{} after {:.2f}s with {}".format(count, MAX_RETRY, RETRY_AFTER, e))
                logging.debug("Error get post {}".format(postDiv.text))
            else:
                break

    res = {
        'thread': thread,
        'posts': posts
    }

    if ret.text.find('>下一页</a>') < 0:
        res['lastpage'] = True

    return res


def readFlrPage(kz, pid, fpn, floor: int = 0) -> {}:
    param = {
        "kz": kz,
        "pid": pid,
        "fpn": fpn
    }

    ret = req.get(url=URL_BASE_FLR, headers=REQUEST_HEADERS,
                  params=param, timeout=(30, 30))
    ret.encoding = 'utf-8'  # ret.apparent_encoding
    soup: BeautifulSoup = BeautifulSoup(ret.text, 'html.parser')

    postDivs = soup.select('div .i')
    posts = []
    for postDiv in postDivs:
        floor += 1
        for count in range(MAX_RETRY):
            try:
                post = parsePost(postDiv=postDiv, kz=kz, pn=fpn,
                                 floor_override=floor, parent_override=pid, flr=True)
                posts.extend(post)
            except Exception as e:
                logging.warning(
                    "Error get post retry {}/{} after {:.2f}s with {}".format(count, MAX_RETRY, RETRY_AFTER, e))
                logging.debug("Error get post {}".format(postDiv.text))
            else:
                break

    res = {
        'thread': None,
        'posts': posts,
        'floor': floor
    }

    if ret.text.find('>下一页</a>') < 0:
        res['lastpage'] = True

    return res


def readFlr(kz, pid):
    posts = []

    floor = 0
    for fpn in range(1, MAX_LOOP):
        res = readFlrPage(kz=kz, pid=pid, fpn=fpn, floor=floor)
        floor = res.get('floor')
        posts.extend(res.get('posts'))
        if res.get('lastpage'):
            break
    logging.log(logging.DEBUG+1,
                "Done get flr of kz {} pid {} len: {}".format(kz, pid, len(posts)))
    return posts


def fetchThread(kw, kz, engine, good=None, getFlr=False):
    logging.log(logging.INFO-1, "Fetch thread {} of {}".format(kz, kw))
    pn = 0
    for _ in range(MAX_LOOP):
        page = readThreadPage(kw=kw, kz=kz, pn='{}'.format(
            pn), good=good, getFlr=getFlr)
        savePage(page=page, engine=engine)
        if page.get('lastpage'):
            break
        pn += 10


def parseThreadHeader(div: Tag, kw=DUMMY_KW) -> ThreadHeader:

    thread = ThreadHeader()

    thread.kw = kw

    thread.mod_date = datetime.now()

    "点174592 回536944 5-13"
    "m?kz=143407634&is_bakan=0&lp=5010&pinf=1_1_280"

    aTag: Tag = div.select_one('a')
    if aTag:
        thread.title = aTag.text
        href = aTag.attrs.get("href")
        o = urlparse(href)
        params = parse_qs(o.query)
        kzs = params.get("kz")
        if kzs:
            thread.kz = kzs[0]

    pTag: Tag = div.select_one('p')
    if pTag:
        info = pTag.text.strip()
        match = re.match(
            r"点(?P<click>[0-9]+)\s+回(?P<reply>[0-9]+)\s+(?P<date>[^\s]+)", info)
        if match:
            thread.click = int(match.group('click'))
            thread.reply = int(match.group('reply'))
            thread.last_date = parseDate(match.group('date'))

    spanTags = div.select('span.light')
    thread.top = None
    thread.good = None
    if spanTags:
        for spanTag in spanTags:
            spanTag: Tag
            if spanTag.text.strip() == '顶':
                thread.top = True
            if spanTag.text.strip() == '精':
                thread.good = True

    return thread


def parsePcThreadHeader(liTag: Tag):
    import json
    metadata = json.loads(liTag.attrs.get("data-field"))
    thread = ThreadHeader()
    thread.kz = metadata.get("id")
    thread.author_name = metadata.get("author_name")
    thread.author_nickname = metadata.get("author_nickname")
    thread.author_portrait = metadata.get("author_portrait")
    thread.first_post_id = metadata.get("first_post_id")
    thread.reply = metadata.get("reply_num")
    thread.bakan = metadata.get("is_bakan")
    thread.vid = metadata.get("vid")
    thread.good = metadata.get("is_good")
    thread.top = metadata.get("is_top")
    thread.protal = metadata.get("is_protal")
    thread.membertop = metadata.get("is_membertop")
    thread.multi_forum = metadata.get("is_multi_forum")
    thread.frs_tpoint = metadata.get("frs_tpoint")
    titleATag = liTag.select_one(".j_th_tit a")
    if titleATag:
        thread.title = titleATag.text
    thread.mod_date = datetime.now()
    if not thread.kz:
        thread = None
    return thread


def parsePcThreadHeaderPage(pcPageHtml: str):
    pcPageHtml = pcPageHtml.replace(
        '\r', '').replace('\n', '').replace("'", '"')

    # Last page
    if pcPageHtml.find("下一页") < 0 and pcPageHtml.find("尾页") >= 0:
        return []

    threadRegexp = re.compile(
        '<li class=" j_thread_list .+?</li>', re.MULTILINE)
    matches = threadRegexp.findall(pcPageHtml)
    threads = []
    for match in matches:
        soup: BeautifulSoup = BeautifulSoup(match, 'html.parser')
        liTag = soup.select_one('li')
        thread = None
        try:
            thread = parsePcThreadHeader(liTag)
        except Exception as e:
            print(str(e))
        if thread:
            threads.append(parsePcThreadHeader(liTag))
    return threads


def fetchForumPage(
        kw, pn, engine, good=None, flr=False, fetchContent=True,
        threadSkipSize=THREAD_SIZE_SKIP):
    param = {
        'kw': kw,
        'pn': pn
    }

    # if good:
    #     param['lm'] = 4
    # logging.info("Fetch forum {} page {} with {}".format(kw, pn, param))
    # ret = req.get(url=URL_BASE_TB, headers=REQUEST_HEADERS,
    #               params=param, timeout=(30, 30))
    # ret.encoding = 'utf-8'  # ret.apparent_encoding
    # soup: BeautifulSoup = BeautifulSoup(ret.text, 'html.parser')
    # divTags = soup.select('div .i')
    # threads = []
    # for div in divTags:
    #     threads.append(parseThreadHeader(div=div, kw=kw))

    # PC page
    param['ie'] = 'utf-8'
    param['cid'] = 0
    if good:
        param['tab'] = 'good'
    logging.info("Fetch forum {} page {} with {}".format(kw, pn, param))
    pcPageUrl = 'https://tieba.baidu.com/f'
    ret = req.get(url=pcPageUrl, headers=REQUEST_HEADERS,
                  params=param, timeout=(30, 30))
    ret.encoding = 'utf-8'  # ret.apparent_encoding

    # threadRegexp = re.compile('"/p/(?P<kz>[0-9]+)')
    # matches = threadRegexp.finditer(ret.text)
    # kzSet = set()
    # for match in matches:
    #     kzSet.add(match.group('kz'))

    # threads = []
    # for kz in kzSet:
    #     thread = ThreadHeader()
    #     thread.kz = kz
    #     threads.append(thread)

    threads = parsePcThreadHeaderPage(ret.text)

    for thread in threads:
        thread: ThreadHeader
        kz = thread.kz
        thread.kw = kw
        error = None
        if thread.reply and fetchContent and threadSkipSize > 0 and thread.reply > threadSkipSize:
            thread.comment = 'skip'
            error = ThreadError()
            error.kw = kw
            error.mod_date = datetime.now()
            error.kz = kz
            comment = 'skip kw {} kz {} - {} for size {} larger than {}'\
                .format(kw, kz, thread.title, thread.reply, threadSkipSize)
            error.comment = comment
            error.code = 1000
            error.pn = pn
            import uuid
            error.uid = str(uuid.uuid4())
            logging.warning(comment)

        saveThreadHead(thread=thread, error=error, engine=engine)
        if (not error) and fetchContent:
            comment = 'Fatch kw {} kz {} - {} for size {}'.format(
                kw, kz, thread.title, thread.reply)
            logging.info(comment)
            try:
                fetchThread(kw=kw, kz=kz, engine=engine, good=good, getFlr=flr)
            except Exception as e:
                logging.warning(
                    "Failed fetchThread kw {} kz {} with {}".
                    format(kw, kz, str(e)))

    hasNext = True
    if ret.text.find('下一页') < 0 or len(threads) <= 0:
        hasNext = False

    return hasNext


def fetchForum(
        kw, engine, good=None, flr=False, startPn=0, endPn=MAX_PN,
        fetchContent=True, threadSkipSize=THREAD_SIZE_SKIP):
    pn = startPn
    for _ in range(MAX_LOOP):
        try:
            hasNext = fetchForumPage(
                kw, pn, engine, good=good, flr=flr,
                fetchContent=fetchContent, threadSkipSize=threadSkipSize)
            if not hasNext:
                logging.info("Done get kw {} good {}".format(kw, good))
                break
        except Exception as e:
            logging.warning(
                "Failed to fetchForumPage kz {} pn {} with {}".format(kw, pn, e))

        # On wap tieba pn can not pass 20000
        if pn > endPn:
            break
        pn += 50


def main():
    import argparse
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO)
    logging.getLogger("chardet.charsetprober").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    # url = "m?kz=125327888&pn=0&lp=6015&spn=2&global=1&expand=2"
    # o = urlparse(url)
    # query = parse_qs(o.query)

    parser = argparse.ArgumentParser()

    parser.add_argument('-d', "--db",
                        dest='db',
                        help="path to db",
                        required=False,
                        type=str,
                        default=DB_URL)

    parser.add_argument('-k', "--kw",
                        dest='kw',
                        help="kw",
                        required=False,
                        type=str,
                        default="柯哀")

    parser.add_argument('-f', "--from",
                        dest='fromPn',
                        help="from pn",
                        required=False,
                        type=int,
                        default=0)

    parser.add_argument('-t', "--to",
                        dest='toPn',
                        help="to pn",
                        required=False,
                        type=int,
                        default=MAX_PN)

    parser.add_argument('-m', "--mmx",
                        dest='mmx',
                        help="skip thread with posts bigger than mmx",
                        required=False,
                        type=int,
                        default=THREAD_SIZE_SKIP)

    parser.add_argument('-a', "--all",
                        dest='all',
                        help="all thread, if not given fatch good threads only",
                        required=False,
                        action="store_true")

    parser.add_argument('-b', "--flr",
                        dest='flr',
                        help="fatch flr (aka. floor in floor)",
                        required=False,
                        action="store_true")

    args = parser.parse_args()

    dbUrl = args.db
    engine = create_engine(dbUrl)
    kw = args.kw
    good = not args.all
    flr = args.flr
    Base.metadata.create_all(engine)

    # readFlrPage(kz="125327888", pid="1058754776", fpn="1")
    # readFlr(kz="125327888", pid="1058754776")
    # page = readThreadPage(kw='柯哀', kz="125327888", pn='1890')

    # fetchThread(kw='显卡', kz="6131086464", engine=engine)
    # fetchForum(kw='反哀', engine=engine, good=False, flr=True)
    # python src/tiebaWapGet/main.py \
    # -k '**' --db=sqlite:///./data/zkw.tieba.baidu.com.db -a -f 1620
    # python src/tiebaWapGet/main.py -k '**' \
    # --db=sqlite:///./data/zhenjie.tieba.baidu.com.db -a
    fetchForum(kw=kw, engine=engine, good=good, flr=flr, fetchContent=True,
               threadSkipSize=args.mmx, startPn=args.fromPn, endPn=args.toPn)
    # fetchForum(kw='EVA', engine=engine, good=True,fetchContent=True)

    # parseDate("12:36")
    pass


if __name__ == '__main__':
    main()
