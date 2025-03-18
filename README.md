# WebpageAutoArchiver

Automatically archive a website on the Internet Archive if it changed since it was last seen.

## Installation

It is recommended that this script is run in a virtual environment.
This can be set up by running:

```shell
python3 -m venv venv
pip install -r requirements.txt
```

## Running

```
usage: autoarchiver.py [-h] [--skip-first] url backup_file

positional arguments:
  url           The URL (including https://) of the webpage to archive
  backup_file   The file to track the previous version of the webpage in

optional arguments:
  -h, --help    show this help message and exit
  --skip-first  If backup_file doesn't exist yet, don't archive the page. This can be useful if you recently manually archived it.
```

This script will only archive the webpage at most one time each time it runs.
To have it update automatically, a cronjob should be set up to launch the script periodically.
Running more often than every 15 minutes is not recommended as requests may be limited by the Internet Archive.

For example, if the code has been set up in the home directory with a virtual environment named `venv`, the crontab may look like (be sure to set the script directory):

```
# Automatically archive example.com daily at 12pm and log to example_com.log
0 12 * * * cd /home/username/scripts/WebpageAutoArchiver && venv/bin/python autoarchiver.py https://example.com example_com_backup.txt >> example_com.log
```

## How it works

The script pulls the current website content and converts it to plain text using the BeautifulSoup library.
If the text matches the backup (or `--skip-first` is set), the website will not be archived.
Otherwise, if the text is different, the webpage will be archived using the waybackpy library.
Finally, the current webpage text is saved to the backup file, overwriting the previous content.
