import argparse
import difflib
import logging
import os
import requests
import sys

import waybackpy.exceptions
from bs4 import BeautifulSoup
from waybackpy import WaybackMachineSaveAPI

USER_AGENT = (
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:15.0) Gecko/20100101 Firefox/15.0.1"
)

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
    help="If backup_file doesn't exist yet, don't archive the page. This can be useful if you recently manually archived it",
)
parser.add_argument(
    "--match-ratio",
    type=float,
    default=1.0,
    help="Webpages with a match ratio below this value will be archived. 1 is the highest and default, so any difference will match"
)
parser.add_argument(
    "-n",
    "--dry-run",
    action="store_true",
    help="Check if webpage has updated without modifying backup or archiving"
)
parser.add_argument(
    "-a",
    "--always-backup",
    action="store_true",
    help="If set, backup the webpage locally if the page isn't archived. -n does not affect this"
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
        headers = {"User-Agent": USER_AGENT}
        site_data = requests.get(url, headers=headers)
    except requests.exceptions.MissingSchema as e:
        logger.error("{}".format(e))
        exit(1)
    if site_data.status_code != 200:
        logger.error("Invalid response from webpage ({})".format(site_data.status_code))
        exit(1)
    site_contents = BeautifulSoup(site_data.text, "html.parser").get_text()
    # Remove \r because they can cause problems with the file comparison (not sure why)
    site_contents = site_contents.replace("\r", "")
    return site_contents


def save_webpage(url: str) -> bool:
    logger.debug("Running save_webpage")
    save_api = WaybackMachineSaveAPI(url, USER_AGENT)
    try:
        save_api.save()
    except waybackpy.exceptions.TooManyRequestsError as e:
        logger.error("{}".format(e))
        return False
    logger.info("Webpage saved and viewable at {}".format(save_api.saved_archive))
    return True


def autoarchive(url: str, backup_file: str, skip_first: bool = False, match_ratio: float = 1.0, dry_run: bool = False, always_backup: bool = False):
    if match_ratio < 0 or match_ratio > 1:
        raise ValueError("match_ratio must be between 0 and 1 (inclusive)")
    current_content = get_webpage_text(url)
    backup_found = backup_exists(backup_file)
    if backup_found:
        previous_content = get_backup_text(backup_file)

    if skip_first and not backup_found:
        logger.info("No backup file found. Not archiving")
    else:
        to_archive = not backup_found
        if not to_archive:
            # Save time by directly comparing strings if match_ratio is default
            if match_ratio == 1.0:
                to_archive = current_content != previous_content
            else:
                matcher = difflib.SequenceMatcher()
                # Take average of two ratios, because they can be different
                matcher.set_seqs(previous_content, current_content)
                ratio1 = matcher.ratio()
                matcher.set_seqs(current_content, previous_content)
                ratio2 = matcher.ratio()
                ratio = (ratio1 + ratio2) / 2.
                logger.info("Match ratio: {}".format(round(ratio, 5)))
                to_archive = ratio < match_ratio
        if to_archive:
            logger.info("Archiving webpage. Please wait")
            if not dry_run:
                if save_webpage(url):
                    # Only create local backup if successfully archived
                    logger.info("Creating local backup")
                    save_backup(current_content, backup_file)
        else:
            # Only create local backup if --always-backup set
            logger.info("Website hasn't changed. Not archiving")
            if always_backup:
                logger.info("Creating local backup")
                save_backup(current_content, backup_file)

if __name__ == "__main__":
    args = parser.parse_args()
    try:
        autoarchive(args.url, args.backup_file, args.skip_first, args.match_ratio, args.dry_run, args.always_backup)
    except ValueError as e:
        logger.error(e)
