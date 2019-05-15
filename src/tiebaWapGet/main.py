from urllib.parse import urlparse, parse_qs
import requests
from bs4 import BeautifulSoup
from bs4.element import Tag
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, DateTime, Integer, Float
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from common import URL_BASE_TB, REQUEST_HEADERS, FALL_BACKDATE, DB_URL, MAX_RETRY, RETRY_AFTER
from tbDAO import Base, PostHeader, Content, Content_HTML, AttachementHeader, PostAttachement, Thread
from dateutil import parser as DateParser
import logging
import re

import requests
from requests.adapters import HTTPAdapter

req = requests.Session()
httpAdapter = HTTPAdapter(max_retries=MAX_RETRY)

req.mount('http://', httpAdapter)
req.mount('https://', httpAdapter)

"m?kz=125327888&pn=30"


def insertOrIgnoreAll(objs, engine):
    Session = sessionmaker(bind=engine)
    count = 0
    for link in objs:
        try:
            session = Session()
            session.add(link)
            session.commit()
            count += 1
        except IntegrityError as e:
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
        logging.debug("Failed to parse date string {} use {} as fall back.".format(dateStr, current))

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
    ret = req.get(url=URL_BASE_TB, headers=REQUEST_HEADERS, params=param, timeout=(30, 30))
    ret.encoding = 'utf-8'  # ret.apparent_encoding
    soup: BeautifulSoup = BeautifulSoup(ret.text, 'html.parser')
    postDivs = soup.select_one('body > div > div.d:nth-child(4) > div.i:nth-child(1)')
    return postDivs


def makeEmptyAttachement(floor, parent, link) -> PostAttachement:
    att = PostAttachement()
    att.mod_date = datetime.now()
    att.floor = floor
    att.parent = parent
    att.link = link
    return att


def parsePost(postDiv: Tag, kz, pn, parent_override=None, floor_override=-1) -> dict:
    postHeader = PostHeader()
    content = Content()
    contentHtml = Content_HTML()
    attachments = []

    postHeader.mod_date = datetime.now()

    dateSpan: Tag = postDiv.select_one("span.b")
    create_date = FALL_BACKDATE
    if dateSpan:
        dateStr = dateSpan.text.strip()
        create_date = parseDate(dateStr)
    postHeader.create_date = create_date

    replyATag: Tag = postDiv.select_one("a.reply_to")
    href = "#reply"
    if replyATag:
        href = replyATag.attrs.get("href")
    o = urlparse(href)
    param = parse_qs(o.query)
    pid = param.get("pid")
    if not pid:
        pid = '_kz_{}'.format(kz)
    else:
        pid = pid[0]

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
            contentText = additionalPostDivTag.getText(separator="\n", strip=True)
            contentSource = str(additionalPostDivTag)

    content.mod_date = datetime.now()
    content.content = contentText

    contentHtml.mod_date = datetime.now()
    contentHtml.content = contentSource

    postHeader.cid = pid
    content.cid = pid
    contentHtml.cid = pid

    postHeader.floor = int(floor)

    postHeader.flr = False

    postHeader.parent = int(kz)

    postHeader.pid = pid
    content.source = pid
    contentHtml.source = pid

    postHeader.to = None

    for href in atts:
        att = makeEmptyAttachement(floor, postHeader.parent, href)
        if att:
            attachments.append(att)

    res = {
        'header': postHeader,
        'text': content,
        'html': contentHtml,
        'attachments': attachments
    }

    logging.debug("Get post from thread {} page {} floor {} pid {}".format(kz, pn, floor, pid))
    return res


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
        insertOrIgnoreAll(links, engine)
    except Exception as e:
        logging.warning("Error save attachments {} with {}".format(post, str(e)))


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


def readThreadPage(kw, kz, pn, good=None) -> {}:
    import re
    start = datetime.now().timestamp()

    param = {
        "kz": kz,
        "pn": pn
    }

    ret = req.get(url=URL_BASE_TB, headers=REQUEST_HEADERS, params=param, timeout=(30, 30))
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
    userTag = soup.select_one("body > div > div:nth-child(4) > div:nth-child(1) > span.g > a")
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
                post = parsePost(postDiv=postDiv, kz=kz, pn=pn)
                posts.append(post)
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


def fetchThread(kw, kz, engine, good=None):
    logging.info("Fetch thread {} of {}".format(kz, kw))
    pn = 0
    for _ in range(10000):
        page = readThreadPage(kw=kw, kz=kz, pn='{}'.format(pn), good=good)
        savePage(page=page, engine=engine)
        if page.get('lastpage'):
            break
        pn += 10


def fetchForumPage(kw,pn,engine,good=None):
    param = {
        'kw' : kw,
        'pn' : pn
    }
    if good:
        param['lm']=4
    logging.info("Fetch forum {} page {} with {}".format(kw,pn,param))
    ret = req.get(url=URL_BASE_TB, headers=REQUEST_HEADERS, params=param, timeout=(30, 30))
    ret.encoding = 'utf-8'  # ret.apparent_encoding
    soup: BeautifulSoup = BeautifulSoup(ret.text, 'html.parser')
    aTags = soup.select('div .i > a')
    threads = []
    for aTag in aTags:
        aTag:Tag
        href = aTag.attrs.get("href")
        o = urlparse(href)
        param = parse_qs(o.query)
        kzs = param.get("kz")
        if kzs:
            threads.append(kzs[0])
    for kz in threads:
        fetchThread(kw=kw, kz=kz, engine=engine, good=good)

    hasNext = True
    if ret.text.find('>下一页</a>') < 0:
        hasNext = False

    return hasNext

def fetchForum(kw,engine, good=None):
    pn = 0
    for _ in range(10000):
        hasNext = fetchForumPage(kw, pn, engine, good=good)
        if not hasNext:
            break
        pn += 10

def main():
    logging.basicConfig(level=logging.DEBUG)
    # logging.getLogger("chardet.charsetprober").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    # url = "m?kz=125327888&pn=0&lp=6015&spn=2&global=1&expand=2"
    # o = urlparse(url)
    # query = parse_qs(o.query)

    engine = create_engine(DB_URL)
    Base.metadata.create_all(engine)

    # page = readThreadPage(kw='柯哀', kz="125327888", pn='1890')

    # fetchPost(kw='柯哀', kz="6120869672", engine=engine)
    fetchForum(kw='四枫院夜一',engine=engine,good=True)

    # parseDate("12:36")
    pass


if __name__ == '__main__':
    main()
