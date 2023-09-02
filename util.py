import json
import os
from glob import glob
from time import sleep
import random
import string

from selenium.common.exceptions import ElementNotInteractableException

from config import MODELS_TMP_PATH


def get_download_page_url(entry):
    return "https://www.cgtrader.com/items/%s/download-page" % entry["id"]


def generate_file_list(driver, entry):
    print("> Generate list of files...")
    assert (
        driver.current_url == entry["attributes"]["url"]
    ), "Fatal: Must be on model page when generating file list."

    file_list = []

    file_list_text = driver.find_elements("css selector", ".product-formats-list")[
        0
    ].text
    if len(file_list_text) > 0:
        file_list_entries = file_list_text.split("\n")
        file_list_entries = [
            entry
            for entry in file_list_entries
            if not (entry.startswith("Version: ") or entry.startswith("Renderer: "))
        ]
        file_list_names = file_list_entries[::2]
        file_list_sizes = file_list_entries[1::2]

        for file_list_index, file_list_name in enumerate(file_list_names):
            file = {
                "name": file_list_name,
                "approximate_size": file_list_sizes[file_list_index],
                "index": file_list_index,
            }
            file_list.append(file)

    print("> > Save to file.")
    with open(
        os.path.join(entry["meta"]["localPath"], "files.json"), "w"
    ) as file_list_file:
        json.dump(file_list, file_list_file)

    return file_list


def generate_download_list(driver, entry):
    print("> Generate list of downloads... ", end="", flush=True)
    assert (
        entry["id"] in driver.current_url
    ), "Fatal: Must be on download page when generating file list."

    while True:
        downloads_list_text = driver.find_element("css selector", ".details-box").text

        if "Files are being prepared for download" in downloads_list_text:
            print("*", flush=True, end="")
            sleep(1)
        else:
            print()
            break

    download_descriptions = [
        entry.text for entry in driver.find_elements("css selector", ".details-box li")
    ]
    download_links = [
        link.get_attribute("href")
        for link in driver.find_elements("css selector", ".js-free-download")
    ]
    print(download_descriptions, download_links)

    downloads = []

    for download_index, download_description in enumerate(download_descriptions):
        # format is: "Filename\n({SIZE}) Download"
        [filename, details] = download_description.split("\n(")
        approximate_size = details.replace(") Download", "")
        download_description = {
            "file": filename.replace(" PBR-ready", ""),
            "approximate_size": approximate_size,
            "index": download_index,
            "url": download_links[download_index],
        }
        downloads.append(download_description)

    print("> > Save to file.")
    with open(
        os.path.join(entry["meta"]["localPath"], "downloads.json"), "w"
    ) as downloads_file:
        json.dump(downloads, downloads_file)

    return downloads


def download_files(driver, account_manager, entry, files="all", generate_list=True):
    download_all_files = files == "all"

    print("> Load download page and wait...")
    driver.get(get_download_page_url(entry))
    sleep(25)

    # save a list of downloads
    if generate_list:
        entry["meta"]["downloads"] = generate_download_list(driver, entry)

    # start downloads
    driver.execute_script(
        """
            window.scrollTo(
              0, 
              document.querySelector('.js-free-download').getBoundingClientRect().top + window.scrollY - 100
            );
            """
    )

    download_elements = driver.find_elements("css selector", ".js-free-download")
    available_download_count = len(download_elements)
    actual_download_count = (
        available_download_count if download_all_files else len(files)
    )
    print(
        f"> Download {actual_download_count} of {available_download_count} elements..."
    )
    while True:
        try:
            download_index = 0
            for element_index, element in enumerate(download_elements):
                file_name = element.find_element("xpath", "../..").text.split("\n")[0]
                if not download_all_files and file_name not in files:
                    print(f"> > Skip '{file_name}' - not selected.")
                    continue

                print(
                    f"> > Initiate download #{element_index + 1} '{file_name}' ({download_index + 1}/{actual_download_count})..."
                )
                driver.execute_script(
                    f"""
                        document.querySelector('.details-box__list li:nth-child({element_index + 1})').scrollIntoView();
                        window.scrollBy({{top: -100}});
                        """
                )
                element.click()
                account_manager.increase_download_count()
                sleep(3)
                print("> < Started.")
                download_index += 1
            break
        except ElementNotInteractableException:
            print("> < Failed to start. (Will retry all.)")
            sleep(5)

    print("> Wait for downloads to complete.", end="", flush=True)

    previous_partial_download_states = {}
    while True:
        partial_downloads = glob("%s/*.part" % MODELS_TMP_PATH)
        partial_download_states = {}
        for partial_download in partial_downloads:
            partial_download_size = os.path.getsize(partial_download)
            stagnating_count = 0
            if partial_download in previous_partial_download_states:
                previous_partial_download_state = previous_partial_download_states[
                    partial_download
                ]
                if previous_partial_download_state["size"] == partial_download_size:
                    stagnating_count = (
                        previous_partial_download_state["stagnating_count"] + 1
                    )

            partial_download_states[partial_download] = {
                "size": partial_download_size,
                "stagnating_count": stagnating_count,
            }

        if len(partial_downloads) == 0:
            print(" Finished.")
            break
        elif all(
            [
                partial_download_state["stagnating_count"] > 10
                for partial_download_state in partial_download_states.values()
            ]
        ):
            print(" Aborted.")
            entry["meta"]["downloadFailed"] = True
            break
        elif any(
            [
                partial_download_state["stagnating_count"] > 0
                for partial_download_state in partial_download_states.values()
            ]
        ):
            print("_", end="", flush=True)
        else:
            print(".", end="", flush=True)

        previous_partial_download_states = partial_download_states
        sleep(10)

    print("< Downloads complete.")

    print("> Organize files...")
    os.system(f"mv {MODELS_TMP_PATH}/* {entry['meta']['localPath']}")
    print("< Files placed.")


def random_string(length):
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=length))
