from tbDAO import Base, PostHeader, Content, Content_HTML, AttachementHeader
from tbDAO import PostAttachement, Thread,ThreadError,ThreadHeader
from datetime import datetime
from common import REQUEST_HEADERS
import requests


def parseTieBaImgUrl(org):
    import re
    from urllib.parse import urlparse, parse_qs, ParseResult, unquote

    try:
        o:ParseResult = urlparse(org)
        # if not o.hostname == 'c.hiphotos.baidu.com':
        #     return org

        query = parse_qs(o.query)
        src = query.get('src')
        if not src:
            return org

        src = src[0]
        url = unquote(src)

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


def makeEmptyAttachementHeader(attachementLink:PostAttachement) -> AttachementHeader:
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
    url = "http://c.hiphotos.baidu.com/forum/w%3D400%3Bq%3D80%3Bg%3D0/sign=8e6ff1132a9759ee4a5061cb82c0322b/e95bdab44aed2e730d4113328b01a18b87d6fa22.jpg?&src=http%3A%2F%2Fimgsrc.baidu.com%2Fforum%2Fpic%2Fitem%2Fe95bdab44aed2e730d4113328b01a18b87d6fa22.jpg"
    src = parseTieBaImgUrl(url)

    pass

