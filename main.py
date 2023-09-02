import json
import os
import shutil
import sys
import urllib.request
from time import sleep
import pathlib
from glob import glob

from config import MODELS_BASE_PATH, MODELS_TMP_PATH, OVERRIDE, AUTO_RESTART
from cgtrader_accounts import AccountManager
from selenium_provider import get_driver
from util import generate_file_list, download_files


def scrape(model_urls):
    driver = get_driver(MODELS_TMP_PATH)

    # launch account provider, used later
    account_manager = AccountManager(driver)

    def model_already_downloaded(model_url):
        for info_filename in glob(
            os.path.join(MODELS_BASE_PATH, "*_" + model_url.split("/")[-1], "info.json")
        ):
            with open(info_filename, "r") as info_json_file:
                info = json.load(info_json_file)

            if info["attributes"]["url"] == model_url:
                return True

        return False

    for url in model_urls:
        if model_already_downloaded(url):
            print(f"Model already downloaded... skipping. {url}")
            continue

        account_manager.ensure_logged_in()
        entry = {"attributes": {"url": url}, "meta": {}, "info": {}}

        print(f"> Load model page... {url}")
        driver.get(url)

        sleep(5)
        entry["id"] = driver.find_element(
            "css selector", ".stats-info__wishlist-button"
        ).get_attribute("data-item-id")
        entry["info"]["tags"] = [
            label.get_attribute("content")
            for label in driver.find_elements("css selector", ".labels-list .label")
        ]

        print("ID %s..." % entry["id"])

        # generate directory
        model_path = (
            os.path.join(MODELS_BASE_PATH, entry["id"]) + "_" + url.split("/")[-1]
        )
        if OVERRIDE and os.path.isdir(model_path):
            shutil.rmtree(model_path)
        pathlib.Path(model_path).mkdir(parents=True)
        entry["meta"]["localPath"] = model_path

        entry["info"]["name"] = driver.find_element("css selector", "h1").text
        entry["info"]["author"] = driver.find_element("css selector", ".username").text
        entry["info"]["license"] = driver.find_element(
            "css selector", ".product-pricing:not(.is-sticky) [data-class='license']"
        ).text

        # generate file list
        entry["meta"]["files"] = generate_file_list(driver, entry)

        # download primary image
        print("> > Loading image...")
        image_url = driver.find_element(
            "css selector", ".product-carousel__current-media"
        ).get_attribute("src")
        image_file_name = f"image.{image_url.split('.')[-1]}"
        urllib.request.urlretrieve(image_url, os.path.join(model_path, image_file_name))
        print("> < Image saved.")

        print("< Model page complete.")

        download_files(driver, account_manager, entry)

        for file in entry["meta"]["files"]:
            if ".zip" not in file["name"]:
                continue

            shutil.unpack_archive(file["name"], entry["meta"]["localPath"])

        with open(
            os.path.join(entry["meta"]["localPath"], "info.json"), "w"
        ) as info_json_file:
            json.dump(entry, info_json_file)

        with open(
            os.path.join(entry["meta"]["localPath"], "README.md"), "w"
        ) as readme_file:
            readme_file.write(
                f"""
# {entry['info']['name']}
by [{entry['info']['author']}](https://cgtrader.com/{entry['info']['author']})
  
License: {entry['info']['license']}

![Preview](./{image_file_name})
            """
            )

        print("Model complete.")

    print("Goodbye.")
    driver.close()


if __name__ == "__main__":
    urls = sys.argv[1:]
    print(f"Downloading models from {len(urls)} URLs.")

    if AUTO_RESTART:
        while True:
            try:
                scrape(urls)
                break
            except Exception as exception:
                print("XXXXXXXXXXXXXXXXXXXXXXXX")
                print("X Unrecoverable error. X")
                print("XXXXXXXXXXXXXXXXXXXXXXXX")
                print("Exception:")
                print(exception)
                print("Will kill all 'geckodriver'...")
                os.system("killall geckodriver")
                print("Will kill all Firefox marionettes...")
                os.system(
                    "for x in `ps ax | awk '!/awk/ && /firefox.*-marionette/' | awk '{print $1}'`; do kill \"$x\"; done"
                )
                print("Will restart.")
                print("XXXXXXXXXXXXXXXXXXXXXXXX")
    else:
        scrape(urls)
