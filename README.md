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
usage: autoarchiver.py [-h] [--skip-first] [--match-ratio MATCH_RATIO] [-n] [-a]
                       url backup_file

positional arguments:
  url                   The URL (including https://) of the webpage to archive
  backup_file           The file to track the previous version of the webpage in

options:
  -h, --help            show this help message and exit
  --skip-first          If backup_file doesn't exist yet, don't archive the
                        page. This can be useful if you recently manually
                        archived it
  --match-ratio MATCH_RATIO
                        Webpages with a match ratio below this value will be
                        archived. 1 is the highest and default, so any
                        difference will match
  -n, --dry-run         Check if webpage has updated without modifying backup or
                        archiving
  -a, --always-backup   If set, backup the webpage locally if the page isn't
                        archived. -n does not affect this
```

This script will only archive the webpage at most one time each time it runs.
To have it update automatically, a cronjob should be set up to launch the script periodically.
Running more often than every 15 minutes is not recommended as requests may be limited by the Internet Archive.

For example, if the code has been set up in the `~/scripts/` directory with a virtual environment named `venv`, the crontab may look like (be sure to set the script directory):

```
# Automatically archive example.com daily at 12pm and log to example_com.log
0 12 * * * cd scripts/WebpageAutoArchiver && venv/bin/python autoarchiver.py https://example.com example_com.backup >> example_com.log
```

### A note on `--match-ratio`

This feature was added to prevent webpages from being archived if they regularly update some content (such as a timestamp).
If the page isn't archived, it will also not be backed up locally.
This means that it is always comparing its content to the last archive, _not_ the last `autoarchiver.py` run.

This utilises the Python [difflib](https://docs.python.org/3/library/difflib.html) library.
The SequenceMatcher object compared the content of the two webpages and returns a similarity ratio between 0 and 1.
The comparison is done in both directions—previous to current and current to previous—because the ratio can differ based on how it is compared.
The average similarity ratio is compared against `--match-ratio`.
A `--match-ratio` of 0 will match no webpages unless they are 100% different and a ratio of 1 will match all webpages unless they are 100% identical.
Use the `--dry-run` flag after performing your first backup to figure out a baseline `--match-ratio`, but be aware that it could vary between runs even with no visible changes to the page.

If using `--match-ratio 1`, the webpage will always be archived.
To speed up the comparison, particularly for larger webpages, a simple string comparison is performed instead.

## How it works

The script pulls the current website content and converts it to plain text using the BeautifulSoup library.
If the text matches the backup (or `--skip-first` is set), the website will not be archived.
Otherwise, if the text is different, the webpage will be archived using the waybackpy library.
Finally, the current webpage text is saved to the backup file, overwriting the previous content.
