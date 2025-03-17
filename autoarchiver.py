import argparse
import logging
import os
import requests
import sys

import waybackpy.exceptions
from bs4 import BeautifulSoup
from waybackpy import WaybackMachineSaveAPI

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger("autoarchiver")

parser = argparse.ArgumentParser()
parser.add_argument("url")
parser.add_argument("backup_file")

def backup_exists(backup_file: str) -> bool:
    logger.debug("Running backup_exists")
    return os.path.isfile(backup_file)

def get_backup_text(backup_file: str) -> str:
    logger.info("Running get_backup_text")
    with open(backup_file) as file:
        return file.read()

def save_backup(data: str, backup_file: str):
    logger.info("Running save_backup")
    with open(backup_file, "w") as file:
        file.write(data)

def get_webpage_text(url: str) -> str:
    logger.info("Running get_webpage_text")
    try:
        site_data = requests.get(url)
    except requests.exceptions.MissingSchema as e:
        logger.error("{}".format(e))
        exit(1)
    if site_data.status_code != 200:
        logger.error("Invalid response from webpage ({})".format(site_data.status_code))
        exit(1)
    site_contents = BeautifulSoup(site_data.text, 'html.parser').get_text()
    return site_contents

def save_webpage(url: str):
    logger.info("Running save_webpage")
    user_agent = "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:15.0) Gecko/20100101 Firefox/15.0.1"
    save_api = WaybackMachineSaveAPI(url, user_agent)
    try:
        save_api.save()
    except waybackpy.exceptions.TooManyRequestsError as e:
        logger.error("{}".format(e))
        exit(1)
    logger.info("Webpage saved and viewable at {}".format(save_api.saved_archive))

def autoarchive(url: str, backup_file: str):
    current_content = get_webpage_text(url)
    previous_content = ""
    if backup_exists(backup_file):
        previous_content = get_backup_text(backup_file)
    
    if current_content != previous_content:
        save_webpage(url)
    else:
        logger.info("Website hasn't changed")

    save_backup(current_content, backup_file)


if __name__ == "__main__":
    logger.info("Started")
    args = parser.parse_args()
    autoarchive(args.url, args.backup_file)
