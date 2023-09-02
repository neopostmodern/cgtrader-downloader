import requests
import feedparser

from util import random_string


class GuerrillaMail:
    def __init__(self):
        self.username = random_string(8)
        self.email_address = f"{self.username}@ulm-dsl.de"
        response = requests.get(
            f"https://ulm-dsl.de/index.php?search={self.username}",
            cookies={"eu-cookie": "1"},
        )

        if response.status_code != 200:
            print(f"Failed to create mail account: {response.status_code}")

        if self.email_address.lower() not in response.content.decode("utf-8"):
            raise Exception("Could not activate mail address!")

        print(f"Registered new e-mail address {self.email_address}.")

    def fetch_mail(self, email_id):
        response = requests.get(
            f"https://ulm-dsl.de/mail-api.php?name={self.username}&id={email_id}"
        )

        if response.status_code != 200:
            print(f"Failed to fetch mail: {response.status_code}")

        return response.content.decode("utf-8")

    def check_mail(self):
        response = feedparser.parse(
            f"https://ulm-dsl.de/inbox-api.php?name={self.username}"
        )

        if response["entries"][0]["title"] == "0 E-Mails im Posteingang":
            return None

        email_id = response["entries"][0]["id"].split("/")[-1]

        return self.fetch_mail(email_id)
