import undetected_chromedriver as webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException
import pandas as pd
import threading
import time
import random
import shutil
import tempfile
from pprint import pprint
import requests
import sys, os

PROXY = ('proxy.packetstream.io', 31112, 'pergfan', '6ofKZOXwL7qSTGNZ_country-France')


class ProxyExtension:
    manifest_json = """
    {
        "version": "1.0.0",
        "manifest_version": 2,
        "name": "Chrome Proxy",
        "permissions": [
            "proxy",
            "tabs",
            "unlimitedStorage",
            "storage",
            "<all_urls>",
            "webRequest",
            "webRequestBlocking"
        ],
        "background": {"scripts": ["background.js"]},
        "minimum_chrome_version": "76.0.0"
    }
    """

    background_js = """
    var config = {
        mode: "fixed_servers",
        rules: {
            singleProxy: {
                scheme: "http",
                host: "%s",
                port: %d
            },
            bypassList: ["localhost"]
        }
    };

    chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});

    function callbackFn(details) {
        return {
            authCredentials: {
                username: "%s",
                password: "%s"
            }
        };
    }

    chrome.webRequest.onAuthRequired.addListener(
        callbackFn,
        { urls: ["<all_urls>"] },
        ['blocking']
    );
    """

    def __init__(self, host, port, user, password):
        self._dir = os.path.normpath(tempfile.mkdtemp())

        manifest_file = os.path.join(self._dir, "manifest.json")
        with open(manifest_file, mode="w") as f:
            f.write(self.manifest_json)

        background_js = self.background_js % (host, port, user, password)
        background_file = os.path.join(self._dir, "background.js")
        with open(background_file, mode="w") as f:
            f.write(background_js)

    @property
    def directory(self):
        return self._dir

    def __del__(self):
        shutil.rmtree(self._dir)


def selenium_connect():
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    #options.add_argument("--incognito")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--log-level=3")
    options.add_argument("--disable-web-security")
    options.add_argument("--disable-site-isolation-trials")
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--lang=EN')
    #pergfan:6ofKZOXwL7qSTGNZ@proxy.packetstream.io:31112
    proxy_extension = ProxyExtension(*PROXY)
    options.add_argument(f"--load-extension={proxy_extension.directory}")

    prefs = {"credentials_enable_service": False,
        "profile.password_manager_enabled": False}
    options.add_experimental_option("prefs", prefs)
    options.add_extension('/Users/vlad5322/Desktop/work/rugby-bot-resale/3.4.0_0.crx')

    # Create the WebDriver with the configured ChromeOptions
    driver = webdriver.Chrome(
        options=options,
        enable_cdp_events=True,
        
    )

    screen_width, screen_height = driver.execute_script(
        "return [window.screen.width, window.screen.height];")
    
    desired_width = int(screen_width / 2)
    desired_height = int(screen_height / 3)
    driver.set_window_position(0, 0)
    driver.set_window_size(desired_width, screen_height)

    return driver


def read_excel(file_path):
    df = pd.read_excel(file_path)
    matches_data = []

    for i in range(len(df)):
        match_info = df.iloc[i, :].tolist()
        match_data = {
            "match": match_info[1],
            "categories": {
                "cat1": match_info[2],
                "cat2": match_info[3],
                "cat3": match_info[4],
                "cat4": match_info[5]
            },
            "link": match_info[6]
        }
        matches_data.append(match_data)

    return matches_data


def check_categories(data):
    for match_data in data:
        categories = match_data["categories"]
        for key, value in categories.items():
            if value is not None:
                return True

    return False


def check_for_element(driver, selector, click=False, xpath=False):
  try:
    if xpath: element = driver.find_element(By.XPATH, selector)
    else: element = driver.find_element(By.CSS_SELECTOR, selector)
    if click: click_button_safe(driver, element)
    return element
  except: return False


def wait_for_element(driver, selector, wait=30, click=False):
  try:
    element = WebDriverWait(driver, wait).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
    if click: click_button_safe(driver, element)
    return element
  except: return False


def click_button_safe(driver, button):
  try:
    button.click()
  except WebDriverException:
    # Scroll to the button to make it clickable
    driver.execute_script("arguments[0].scrollIntoView();", button)

    button.click()


def pass_data(driver, data, selector):
  while True:
    try:
      element = check_for_element(driver, selector, click=True)
      element.clear()
      for k in data:
          element.send_keys(k)
          time.sleep(.1)
      wait_for_element(driver, 'div[data-state="solved"]')
      contButton = driver.find_element(By.CSS_SELECTOR, '#edit-submit')
      contButton.click()
      break
    except:
      driver.refresh()
      continue


def login_page(driver, email, password):
  while True:
    # check_for_captcha_and_403(driver)
    if check_for_element(driver, 'input[name="name"]'): pass_data(driver, email, 'input[name="name"]')
    if check_for_element(driver, 'input[type="password"]'): pass_data(driver, password, 'input[type="password"]')
    if driver.current_url != 'https://tickets.rugbyworldcup.com/en/user/login?destination=/en/home': break


def get_random_email_and_password(file_path):
    emails_and_passwords = []

    # Read the file and extract emails and passwords
    with open(file_path, 'r') as file:
        for line in file:
            email, password = line.strip().split('````')
            emails_and_passwords.append((email, password))

    # Choose a random email and password
    random_email, random_password = random.choice(emails_and_passwords)
    return random_email, random_password


def main(link):
    driver = selenium_connect()
    email, password = get_random_email_and_password('./accounts.txt')
    print(email, password)
    while True:
        driver.get(link)
        # check_for_captcha_and_403(driver)
        wait_for_element(driver, '#onetrust-accept-btn-handler', wait=3, click=True)
        if check_for_element(driver, 'a[class="btn user-account-login"]', click=True): login_page(driver, email, password)


if __name__ == "__main__":
    matches_data = read_excel("./r.xlsx")
    threads = []
    for row in matches_data:
        match = row["match"]
        link = row["link"]
        categories = row["categories"]
        thread = threading.Thread(target=main, args=(link,))
        thread.start()
        threads.append(thread)

        delay = random.uniform(5, 10)
        time.sleep(delay)
    for thread in threads:
        thread.join()