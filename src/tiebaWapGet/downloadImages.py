from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from common import URL_BASE_TB, REQUEST_HEADERS, FALL_BACKDATE, DB_URL, DUMMY_KW
from common import ATT_POST_STATUS_MADE, FATCH_SIZE,NB_MAX_BLOCKED
from common import MAX_RETRY, RETRY_AFTER, URL_BASE_FLR, MAX_LOOP, MAX_PN, THREAD_SIZE_SKIP
from tbDAO import Base, PostHeader, Content, Content_HTML, AttachementHeader
from tbDAO import PostAttachement, Thread,ThreadError,ThreadHeader
from attachementUtil import makeEmptyAttachementHeader, downloadAttachement
import logging

import requests
from requests.adapters import HTTPAdapter

req = requests.Session()
httpAdapter = HTTPAdapter(max_retries=MAX_RETRY)

req.mount('http://', httpAdapter)
req.mount('https://', httpAdapter)


def makeEmptyAttachements(dbUrl, attrfilter=None):
    import random

    engine = create_engine(dbUrl)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)

    nbResOld = -1
    nbBlocked = 0

    processBegin = datetime.now()

    if attrfilter is None:
        attrfilter = ((PostAttachement.mod_date < processBegin) & (PostAttachement.status.is_(None)))

    while True:
        try:
            start = datetime.now().timestamp()
            session = Session()
            from sqlalchemy.sql import exists, or_
            results = session.query(PostAttachement) \
                .filter(attrfilter) \
                .limit(FATCH_SIZE).all()
            session.expunge_all()
            session.commit()

            nbRes = len(results)
            if nbResOld == nbRes and nbRes != FATCH_SIZE:
                nbBlocked += 1
            else:
                nbBlocked = 0

            if len(results) == 0 or nbBlocked > NB_MAX_BLOCKED:
                break

            index = random.randrange(len(results))
            postAtt: PostAttachement = results[index]

            print("{} Got {} subs took {:.3f}(sec) old is {} blocked {}, select nb {}: {} - {}".format(
                datetime.now().isoformat(), nbRes, datetime.now().timestamp() - start, nbResOld, nbBlocked,
                index, postAtt.parent, postAtt.floor))
            nbResOld = nbRes

            header = None
            try:
                header = makeEmptyAttachementHeader(postAtt)
            except Exception as e:
                from common import STATUS_UNKNOW_ERROR
                postAtt.status = STATUS_UNKNOW_ERROR

            session = Session()
            if header:
                postAtt.attId = header.link
                postAtt.status = ATT_POST_STATUS_MADE
                session.merge(postAtt)
                session.merge(header)
            session.commit()
        except Exception as e:
            print("Error download thread for {}".format(e))


def fetchAttAll(dbUrl, attrfilter=None):
    import random

    engine = create_engine(dbUrl)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)

    nbResOld = -1
    nbBlocked = 0

    processBegin = datetime.now()

    if attrfilter is None:
        attrfilter = ((AttachementHeader.mod_date < processBegin) &
                      ((AttachementHeader.status.is_(None)) | (AttachementHeader.status.between(400, 999))))

    while True:
        try:
            start = datetime.now().timestamp()
            session = Session()
            from sqlalchemy.sql import exists, or_
            results = session.query(AttachementHeader) \
                .filter(attrfilter) \
                .limit(FATCH_SIZE).all()
            session.expunge_all()
            session.commit()

            nbRes = len(results)
            if nbResOld == nbRes and nbRes != FATCH_SIZE:
                nbBlocked += 1
            else:
                nbBlocked = 0

            if len(results) == 0 or nbBlocked > NB_MAX_BLOCKED:
                break

            index = random.randrange(len(results))
            header: AttachementHeader = results[index]

            print("{} Got {} subs took {:.3f}(sec) old is {} blocked {}, select nb {}: {} - {}".format(
                datetime.now().isoformat(), nbRes, datetime.now().timestamp() - start, nbResOld, nbBlocked,
                index, header.pid, header.link))
            nbResOld = nbRes

            try:
                header = downloadAttachement(header)
            except Exception as e:
                from common import STATUS_UNKNOW_ERROR
                header.status = STATUS_UNKNOW_ERROR
                header.comment = str(e)
                header.mod_date = datetime.now()

            session = Session()
            if header:
                session.merge(header)
            session.commit()
        except Exception as e:
            print("Error download thread for {}".format(e))


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    logging.getLogger("chardet.charsetprober").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    makeEmptyAttachements(dbUrl=DB_URL)
    fetchAttAll(dbUrl=DB_URL)

