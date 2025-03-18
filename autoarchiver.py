import argparse
import logging
import os
import requests
import sys

import waybackpy.exceptions
from bs4 import BeautifulSoup
from waybackpy import WaybackMachineSaveAPI

logging.basicConfig(
    format="[%(asctime)s] %(levelname)-8s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
    level=logging.INFO,
)
logger = logging.getLogger("autoarchiver")

parser = argparse.ArgumentParser()
parser.add_argument(
    "url", help="The URL (including https://) of the webpage to archive"
)
parser.add_argument(
    "backup_file", help="The file to track the previous version of the webpage in"
)
parser.add_argument(
    "--skip-first",
    action="store_true",
    help="If backup_file doesn't exist yet, don't archive the page. This can be useful if you recently manually archived it.",
)


def backup_exists(backup_file: str) -> bool:
    logger.debug("Running backup_exists")
    return os.path.isfile(backup_file)


def get_backup_text(backup_file: str) -> str:
    logger.debug("Running get_backup_text")
    with open(backup_file) as file:
        return file.read()


def save_backup(data: str, backup_file: str):
    logger.debug("Running save_backup")
    with open(backup_file, "w") as file:
        file.write(data)


def get_webpage_text(url: str) -> str:
    logger.debug("Running get_webpage_text")
    try:
        site_data = requests.get(url)
    except requests.exceptions.MissingSchema as e:
        logger.error("{}".format(e))
        exit(1)
    if site_data.status_code != 200:
        logger.error("Invalid response from webpage ({})".format(site_data.status_code))
        exit(1)
    site_contents = BeautifulSoup(site_data.text, "html.parser").get_text()
    return site_contents


def save_webpage(url: str):
    logger.debug("Running save_webpage")
    user_agent = (
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:15.0) Gecko/20100101 Firefox/15.0.1"
    )
    save_api = WaybackMachineSaveAPI(url, user_agent)
    try:
        save_api.save()
    except waybackpy.exceptions.TooManyRequestsError as e:
        logger.error("{}".format(e))
        exit(1)
    logger.info("Webpage saved and viewable at {}".format(save_api.saved_archive))


def autoarchive(url: str, backup_file: str, skip_first: bool = False):
    current_content = get_webpage_text(url)
    backup_found = backup_exists(backup_file)
    if backup_found:
        previous_content = get_backup_text(backup_file)

    if skip_first and not backup_found:
        logger.info("No backup file found. Not archiving")
    else:
        if backup_found and current_content != previous_content:
            logger.info("Archiving webpage. Please wait")
            save_webpage(url)
        else:
            logger.info("Website hasn't changed. Not archiving")

    save_backup(current_content, backup_file)


if __name__ == "__main__":
    args = parser.parse_args()
    autoarchive(args.url, args.backup_file, args.skip_first)
