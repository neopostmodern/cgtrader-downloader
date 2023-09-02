import re
from time import sleep
import json

from selenium.common.exceptions import (
    NoSuchElementException,
    ElementNotInteractableException,
    ElementClickInterceptedException,
)
import uuid

from disposable_mail import GuerrillaMail
from util import random_string

DOWNLOADS_PER_ACCOUNT = 80


class AccountManager:
    def __init__(self, driver, minimum_downloads_per_account=20):
        self.driver = driver
        self.minimum_downloads_per_account = minimum_downloads_per_account
        self.logged_in = False

    @staticmethod
    def _load_accounts():
        try:
            with open("data/accounts.json", "r") as accounts_json_file:
                accounts = json.load(accounts_json_file)

            return accounts
        except FileNotFoundError:
            pass
        except json.JSONDecodeError:
            print("Failed to decode accounts.json – continuing with empty list.")

        return None

    @staticmethod
    def _save_accounts(accounts):
        with open("data/accounts.json", "w") as accounts_json_file:
            json.dump(accounts, accounts_json_file)

    def _load_account_with_remaining_quota(self):
        accounts = self._load_accounts()

        if accounts is None:
            return None

        for account in accounts:
            if (
                account["download_count"]
                < DOWNLOADS_PER_ACCOUNT - self.minimum_downloads_per_account
            ):
                return account

        return None

    def _update_account_download_count(self, account_id, download_count):
        accounts = self._load_accounts()

        if accounts is None:
            raise Exception(
                "Can't update account – accounts.json is corrupt or does not exist."
            )

        for account in accounts:
            if account["_id"] == account_id:
                account["download_count"] = download_count

        self._save_accounts(accounts)

    def _insert_account(self, account):
        accounts = self._load_accounts()

        if accounts is None:
            accounts = []

        accounts.append(account)

        self._save_accounts(accounts)

    def ensure_logged_in(self):
        # todo: check DOM instead

        print("Ensuring logged in...")
        if self.logged_in:
            if (
                self.account["download_count"]
                < DOWNLOADS_PER_ACCOUNT - self.minimum_downloads_per_account
            ):
                print("Logged in already.")
                return
            else:
                print("Account has not enough remaining downloads - logout...")
                self._logout()

        account = self._load_account_with_remaining_quota()

        if account is None:
            print("No accounts available - creating a new one.")
            self._create_credentials()
            self._logout()
            self._login(self.account)
            return

        self._login(account)

    def increase_download_count(self):
        self.account["download_count"] += 1
        self._update_account_download_count(
            self.account["_id"], self.account["download_count"]
        )

    def _create_credentials(self):
        print("Creating account...")
        tempmail = GuerrillaMail()

        account = {
            "username": random_string(10),
            "password": random_string(8),
            "email": tempmail.email_address,
        }

        self.driver.get("https://cgtrader.com")

        while True:
            try:
                sleep(3)
                self.driver.execute_script(
                    """const iframe = document.getElementById('credential_picker_container'); if (iframe) { iframe.parentNode.removeChild(iframe); }"""
                )

                user_element = self.driver.find_element("css selector", ".user")
                user_element.click()
                self.driver.implicitly_wait(5)

                self.driver.find_element(
                    "css selector", ".auth-tabs li:nth-child(2)"
                ).click()
                self.driver.implicitly_wait(5)
                # refresh link to dom element

                self.driver.find_element(
                    "css selector",
                    "#regsiter-username-top-menu-old-layout",  # sic: regsiter
                ).send_keys(account["username"])
                sleep(1)
                self.driver.find_element(
                    "css selector", "#register-email-top-menu-old-layout"
                ).send_keys(account["email"])
                sleep(1)
                self.driver.find_element(
                    "css selector", "#register-password-top-menu-old-layout"
                ).send_keys(account["password"])
                sleep(3)
                self.driver.find_element("css selector", "#register-for-submit").click()

                sleep(5)
                if "verify-email" in self.driver.current_url:
                    break
            # except ElementClickInterceptedException as intercepted:
            #     print("intercepted!")
            except (NoSuchElementException, ElementNotInteractableException) as e:
                print("*", end="", flush=True)
                sleep(1)

        print()
        print("Waiting for confirmation mail...")

        while True:
            mail = tempmail.check_mail()
            if (
                mail is not None
                and "<title>Confirm your CGTrader account</title>" in mail
            ):
                confirmation_link_regex = re.compile(
                    r'https?://links\.cgtrader\.com/u/click[^"]*'
                )
                confirmation_link = confirmation_link_regex.findall(mail)[0]
                self.driver.get(confirmation_link)
                break
            print("*", end="", flush=True)
            sleep(1)

        print()

        account["download_count"] = 0

        account["_id"] = str(uuid.uuid4())
        self._insert_account(account)
        self.account = account
        print("Account created. Maybe logged in.")

    def _login(self, account):
        print("Logging in...")
        self.driver.get("https://cgtrader.com")

        while True:
            try:
                sleep(3)
                self.driver.execute_script(
                    """const iframe = document.getElementById('credential_picker_container'); if (iframe) { iframe.parentNode.removeChild(iframe); }"""
                )
                sleep(2)

                user_element = self.driver.find_element("css selector", ".user")
                user_element.click()
                sleep(5)

                self.driver.find_element(
                    "css selector", "#login-email-top-menu-old-layout"
                ).send_keys(account["email"])
                sleep(2)
                self.driver.find_element(
                    "css selector", "#login-password-top-menu-old-layout"
                ).send_keys(account["password"])
                sleep(2)
                self.driver.find_element(
                    "css selector", "#login-tab .cgt-button--primary"
                ).click()
                break
            except (NoSuchElementException, ElementNotInteractableException):
                print("*", end="", flush=True)
                sleep(1)
        print()

        print("Waiting for login to complete...")
        while not self.driver.find_element(
            "css selector", ".js-avatar-container"
        ).is_displayed():
            print("*", end="", flush=True)
            sleep(1)
        print()

        print("Logged in.")

        self.logged_in = True
        self.account = account

    def _logout(self):
        print("Logging out...")
        while True:
            try:
                self.driver.find_element("css selector", ".avatar").click()
                self.driver.implicitly_wait(1)
                self.driver.find_element("css selector", "#user-logout-action").click()
                break
            except (
                ElementNotInteractableException,
                NoSuchElementException,
                ElementClickInterceptedException,
            ):
                print("*", end="", flush=True)
                sleep(1)
        print()
        sleep(5)
        print("Logged out.")
