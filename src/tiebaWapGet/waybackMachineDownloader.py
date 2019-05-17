from datetime import datetime, timedelta
import argparse
import os
import dateutil.parser

# "root@bxclient-ylin:~/archive# docker run --rm -it -v $PWD/websites:/websites hartator/wayback-machine-downloader https://tieba.baidu.com/mo -f 20170719 -t 20170720"


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('-f', "--startdate",
                        dest='startdate',
                        help="The Start Date - format YYYY-MM-DD",
                        required=False,
                        type=dateutil.parser.parse,
                        default=(datetime.now()-timedelta(days=300)))
    parser.add_argument('-t', "--enddate",
                        dest='enddate',
                        help="The End Date format YYYY-MM-DD (Inclusive)",
                        required=False,
                        type=dateutil.parser.parse,
                        default=datetime.now())
    parser.add_argument('-u', "--url",
                        dest='url',
                        help="URL",
                        required=False,
                        type=str,
                        default="http://tieba.baidu.com/mo")

    parser.add_argument('-s', "--step",
                        dest='step',
                        help="step in days",
                        required=False,
                        type=int,
                        default=15)

    parser.add_argument("-d", "--debug",
                        dest='debug',
                        help="dry run",
                        action="store_true")

    args = parser.parse_args()


    image = "hartator/wayback-machine-downloader"

    saveTo = "$PWD/data/websites"
    site = args.url
    timeFormat = "%Y%m%d%H%M%S"  # 20170716231334

    start = args.startdate
    end = args.enddate
    step = args.step
    debug = args.debug

    arg="-c {}".format(step)


    current = start
    while True:
        if current > end:
            break

        startStr = current.strftime(timeFormat)
        current = current + timedelta(days=step)
        endStr = current.strftime(timeFormat)
        cmd = "docker run --rm -it -v {to}:/websites {image} {site} -f {start} -t {end} {arg}".format(
            to=saveTo,
            image=image,
            site=site,
            start=startStr,
            end=endStr,
            arg=arg
        )
        print(cmd)
        if not debug:
            os.system(cmd)
        else:
            print("debug: {}".format(debug))


if __name__ == '__main__':
    main()

