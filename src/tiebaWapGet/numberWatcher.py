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
    e = None
    for kw in kws:
        if len(kw)<=0:
            continue

        fields = {}
        url = 'https://tieba.baidu.com/f?kw={}'.format(kw)
        try:
            driver.get(url)
            ret = driver.page_source
            # ret = req.get(url=url, headers=REQUEST_HEADERS, params=param, timeout=(30, 30))
            # ret.encoding = 'utf-8'  # ret.apparent_encoding
            soup: BeautifulSoup = BeautifulSoup(ret, 'html.parser')
            divTags:Tag = soup.select_one('div.th_footer_bright > div.th_footer_l')
            info = divTags.get_text(separator='',strip=True)
            regexp = r".*主题.*数(?P<thread>[0-9]+)个.*贴子.*数(?P<post>[0-9]+)篇.*数(?P<member>[0-9]+)"
            match = re.match(regexp,info)
            if match:
                fields["thread"]= int(match.group('thread'))
                fields["post"]= int(match.group('post'))
                fields["member"]= int(match.group('member'))
        except Exception as e:
            logging.warning("Failed Fetch forum {} with {} got {}".format(kw,url,e))


        url = 'https://tieba.baidu.com/f?kw={}&ie=utf-8&tab=good'.format(kw)
        try:
            driver.get(url)
            ret = driver.page_source
            # ret = req.get(url=url, headers=REQUEST_HEADERS, params=param, timeout=(30, 30))
            # ret.encoding = 'utf-8'  # ret.apparent_encoding
            soup: BeautifulSoup = BeautifulSoup(ret, 'html.parser')
            divTags:Tag = soup.select_one('div.th_footer_bright > div.th_footer_l')
            info = divTags.get_text(separator='',strip=True)
            regexp = r".*精品数(?P<thread>[0-9]+)个"
            match = re.match(regexp,info)
            if match:
                fields["good"]= int(match.group('thread'))
        except Exception as e:
            logging.warning("Failed Fetch forum {} with {} got {}".format(kw,url,e))

        if fields:
            timestamp = datetime.now() - timedelta(seconds=TIME_ZONE_OFFSET_SECONDS)
            point = {
                "measurement": "tznumber",
                "tags": {
                    "kw": kw,
                },
                "time": timestamp,
                "fields": fields
            }

            points.append(point)
            logging.info("Fetch forum {} got {}".format(kw, fields))
        else:
            logging.warning("Failed Fetch forum {}".format(kw))

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
