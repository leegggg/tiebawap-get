from influxdb import InfluxDBClient
from datetime import datetime
import requests
from bs4 import BeautifulSoup,Tag
import logging
from common import REQUEST_HEADERS
from req import req
from selenium import webdriver
from selenium.webdriver import Firefox
from selenium.webdriver.firefox.options import Options
import re
import argparse
from datetime import timedelta

TIME_ZONE_OFFSET_SECONDS = 8 * 3600

def read(kws):
    options = Options()
    options.add_argument('-headless')
    driver = webdriver.Firefox(options=options)

    points = []

    for kw in kws:
        if len(kw)<=0:
            continue

        url='https://tieba.baidu.com/f?kw={}'.format(kw)
        driver.get(url)
        ret = driver.page_source
        # ret = req.get(url=url, headers=REQUEST_HEADERS, params=param, timeout=(30, 30))
        # ret.encoding = 'utf-8'  # ret.apparent_encoding
        soup: BeautifulSoup = BeautifulSoup(ret, 'html.parser')
        divTags:Tag = soup.select_one('div.th_footer_bright > div.th_footer_l')
        info = divTags.get_text(separator='',strip=True)
        regexp = r".*主题.*数(?P<thread>[0-9]+)个.*贴子.*数(?P<post>[0-9]+)篇.*数(?P<member>[0-9]+)"
        match = re.match(regexp,info)

        point = None
        if match:
            timestamp = datetime.now() - timedelta(seconds=TIME_ZONE_OFFSET_SECONDS)
            point = {
                "measurement": "tznumber",
                "tags": {
                    "kw": kw,
                },
                "time": timestamp,
                "fields": {
                    "thread": int(match.group('thread')),
                    "post": int(match.group('post')),
                    "member": int(match.group('member'))
                }
            }

        fields = None
        if point:
            fields = point.get('fields')
            points.append(point)

        logging.info("Fetch forum {} with {} got {}".format(kw, url, fields))

    driver.quit()

    return points


def write(points):
    db = 'tieba'
    client = InfluxDBClient(host='ada.lan.linyz.net', port=8086,username='root',password='root',database=db)
    # client.delete_series(db,"tznumber")
    client.create_database('tieba')
    client.write_points(points,database='tieba')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    # logFmt = '[%(asctime)s] p%(process)s {%(filename)s:%(lineno)d} %(levelname)s - %(message)s'
    logFmt = '%(filename)s:%(lineno)d %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=logFmt)

    parser.add_argument('-i', "--in",
                        dest='listFile',
                        help="thread list",
                        required=False,
                        type=str,
                        default="data/kw.list")

    args = parser.parse_args()

    with open(args.listFile) as f:
        kws = f.readlines()
    # you may also want to remove whitespace characters like `\n` at the end of each line
    kws = [x.strip() for x in kws]

    logging.info("Get number info of {}".format(kws))
    points = read(kws)
    write(points)
    logging.info("All done")

    pass
