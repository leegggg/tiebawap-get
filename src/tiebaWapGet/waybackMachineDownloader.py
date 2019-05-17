from datetime import datetime, timedelta
import os

# "root@bxclient-ylin:~/archive# docker run --rm -it -v $PWD/websites:/websites hartator/wayback-machine-downloader https://tieba.baidu.com/mo -f 20170719 -t 20170720"


def main():
    image = "hartator/wayback-machine-downloader"

    saveTo = "$PWD/data/websites"
    site = "http://tieba.baidu.com/mo"
    timeFormat = "%Y%m%d%H%M%S"  # 20170716231334
    start = datetime(2018,1,1)
    end = datetime(2019.1.1)
    step = 15

    arg="-c 15"


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
        os.system(cmd)


if __name__ == '__main__':
    main()

