# tiebawap-get

A dirty and simple baidu tieba wap version getter for achive data. 

Tieba has hidden data before 2017 but they can still be access by wap version.

Let's just achive them.

<strong> PRs are welcomed</strong>

## How to use

```bash
git clone https://github.com/leegggg/tiebawap-get.git
cd tiebawap-get
python3 -m 'venv' env
pip install -r requirements.txt
python src/tiebaWapGet/main.py

```

## Get data from archive.org

From 2019-05-16T19:30:00+8 baidu.com has patched the wap version of tieba. Old data
can no more be read from anywhere of baidu.

Fortunately as a famous site tieba has been achived by archive.org data can be 
read from their server. 

A script that read tieba from wayback-machine has been created.

You need docker, hartator/wayback-machine-downloader image and a server outside 
the GFW to run.

Arguments can be found from help text of the python script.

```
python src/tiebaWapGet/waybackMachineDownloader.py 
``` 

It will be a great work to traiter data from archive.org.

HELP IS NEEDED.