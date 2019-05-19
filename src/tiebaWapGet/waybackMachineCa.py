from datetime import datetime, timedelta
import argparse
import os
import dateutil.parser

# "root@bxclient-ylin:~/archive# docker run --rm -it -v $PWD/websites:/websites hartator/wayback-machine-downloader https://tieba.baidu.com/mo -f 20170719 -t 20170720"


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('-i', "--in",
                        dest='listFile',
                        help="thread list",
                        required=False,
                        type=str,
                        default="data/ca.list")

    parser.add_argument('-o', "--out",
                        dest='out',
                        help="URL",
                        required=False,
                        type=str,
                        default="data/ca.list")


    parser.add_argument("-d", "--debug",
                        dest='debug',
                        help="dry run",
                        action="store_true")

    args = parser.parse_args()


    image = "hartator/wayback-machine-downloader"

    saveTo = "$PWD/data/{}".format(args.out)

    timeFormat = "%Y%m%d%H%M%S"  # 20170716231334

    debug = args.debug

    arg = ""

    threads = []
    with open(args.listFile) as f:
        threads = f.readlines()
    # you may also want to remove whitespace characters like `\n` at the end of each line
    threads = [x.strip() for x in threads]

    for thread in threads:
        site = "tieba.baidu.com/p/{}".format(thread)
        cmd = "docker run --rm -v {to}:/websites {image} {site} {arg}".format(
            to=saveTo,
            image=image,
            site=site,
            arg=arg
        )
        print(cmd)
        if not debug:
            os.system(cmd)
            pass
        else:
            print("debug: {}".format(debug))


if __name__ == '__main__':
    main()

