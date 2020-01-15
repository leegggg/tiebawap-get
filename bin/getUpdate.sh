#!/usr/bin/env bash
if [[ -z $1 ]]; then
    echo "kw needed"
    exit
fi

cd /home/ylin/tiebawap-get
source env/bin/activate
# python -u src/tiebaWapGet/numberWatcher.py
python -u src/tiebaWapGet/main.py -d sqlite:////home/ylin/anna/ext_hdd/by-uuid/aea3c7d1-7bf3-4028-a87f-b9dc140a6eec/all.[$1].tieba.baidu.com.db -k [$1] -a -b -t 250
