from tbDAO import Base, PostHeader, Content, Content_HTML, AttachementHeader
from tbDAO import PostAttachement, Thread, ThreadError, ThreadHeader
from datetime import datetime
from common import REQUEST_HEADERS
import requests


def parseTieBaImgUrl(org):
    import re
    from urllib.parse import urlparse, parse_qs, ParseResult, unquote

    try:
        o: ParseResult = urlparse(org)
        # if not o.hostname == 'c.hiphotos.baidu.com':
        #     return org

        query = parse_qs(o.query)
        src = query.get('src')
        if not src:
            return org

        src = src[0]
        url = unquote(src, encoding='gbk')

        return url
    except:
        pass

    return org


def makeEmptyAttachement(floor, parent, link) -> PostAttachement:
    att = PostAttachement()
    att.mod_date = datetime.now()
    att.floor = floor
    att.parent = parent
    att.link = link
    return att


def makeEmptyAttachementHeader(attachementLink: PostAttachement) -> AttachementHeader:
    att = AttachementHeader()
    att.mod_date = datetime.now()
    att.link = parseTieBaImgUrl(attachementLink.link)
    att.pid = attachementLink.parent

    return att


def downloadAttachement(att: AttachementHeader):
    import shutil
    import os.path
    from pathlib import Path
    from common import ATTACHEMENT_BASE_PATH
    # from common import ATTACHEMENT_OUT_BASE_PATH

    existFlag = False
    subPath = att.path
    if subPath is not None:
        subPath = Path(ATTACHEMENT_BASE_PATH).joinpath(subPath)
        if os.path.isfile(subPath):
            existFlag = True

    if not existFlag:
        downUrl = att.link
        # downUrl = 'http://dl1.subhd.com/sub/2019/03/155343934746869.zip'
        if not downUrl:
            return None

        parts = Path(downUrl).parts[1:]  # cut http[s] and host
        subPath = Path("")
        for part in parts:
            subPath = subPath.joinpath(part)
        fullPath = Path(ATTACHEMENT_BASE_PATH).joinpath(subPath)
        os.makedirs(fullPath.parent, mode=0o755, exist_ok=True)

        ret = requests.get(downUrl, headers=REQUEST_HEADERS, timeout=(30, 300))
        att.status = int(ret.status_code)

        if att.status and att.status < 400:
            with open(fullPath, "wb") as code:
                code.write(ret.content)

        att.path = subPath.as_posix()
        att.title = subPath.name
        att.downloaded = datetime.now()
        att.mod_date = datetime.now()
        print("Download {} to {}".format(att.link, att.path))

    return att


if __name__ == '__main__':
    url = "http://gss3.bdstatic.com/84oSdTum2Q5BphGlnYG/timg?wapp&quality=80&size=b400_2000&cut_x=0&cut_w=0&cut_y=0&cut_h=0&sec=1369815402&di=86ad451e706e0313228004fefbaa7837&wh_rate=null&src=http%3A%2F%2Fhiphotos.baidu.com%2F%25C0%25E4%25D4%25C2%25D3%25F4%2Fpic%2Fitem%2F1a540b32debfdde15fdf0efa.jpg"
    src = parseTieBaImgUrl(url)

    pass
