import undetected_chromedriver as webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException
import pandas as pd
import json
import soundfile as sf
import sounddevice as sd
import threading
import time
import random
import shutil
import tempfile
from pprint import pprint
import requests
import re
import sys, os

PROXY = ('proxy.soax.com', 9000, 'mZ7COGLGDP04INBs', 'wifi;;;;')


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


def read_proxy_file(file_path):
    with open(file_path, 'r') as file:
        proxy_lines = file.readlines()
    return proxy_lines

def choose_random_proxy(proxy_lines):
    random_proxy = random.choice(proxy_lines).strip()
    domain, port, login, password = random_proxy.split(':')
    return (domain, int(port), login, password)


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
    # proxy = choose_random_proxy(read_proxy_file('./proxies.txt'))
    # proxy_extension = ProxyExtension(*proxy)
    options.add_argument(f"--load-extension=D:\\projects\\rugby-bot-resale\\NopeCHA")

    prefs = {"credentials_enable_service": False,
        "profile.password_manager_enabled": False}
    options.add_experimental_option("prefs", prefs)

    # Create the WebDriver with the configured ChromeOptions
    driver = webdriver.Chrome(
        options=options,
        enable_cdp_events=True,
    )

    screen_width, screen_height = driver.execute_script(
        "return [window.screen.width, window.screen.height];")
    
    desired_width = int(screen_width / 2)
    driver.set_window_position(0, 0)
    driver.set_window_size(desired_width, screen_height)
    driver.get('https://nopecha.com/setup#sub_1NnGb4CRwBwvt6ptDqqrDlul|enabled=true|disabled_hosts=%5B%5D|hcaptcha_auto_open=true|hcaptcha_auto_solve=true|hcaptcha_solve_delay=true|hcaptcha_solve_delay_time=3000|recaptcha_auto_open=true|recaptcha_auto_solve=true|recaptcha_solve_delay=true|recaptcha_solve_delay_time=1000|recaptcha_solve_method=Image|funcaptcha_auto_open=true|funcaptcha_auto_solve=true|funcaptcha_solve_delay=true|funcaptcha_solve_delay_time=0|awscaptcha_auto_open=true|awscaptcha_auto_solve=true|awscaptcha_solve_delay=true|awscaptcha_solve_delay_time=0|textcaptcha_auto_solve=true|textcaptcha_solve_delay=true|textcaptcha_solve_delay_time=0|textcaptcha_image_selector=|textcaptcha_input_selector=')
    return driver


def read_excel(file_path):
    df = pd.read_excel(file_path)
    matches_data = []

    for i in range(len(df)):
        match_info = df.iloc[i, :].tolist()
        match_data = {
            "match": match_info[1],
            "categories": {
                1: match_info[2],
                2: match_info[3],
                3: match_info[4],
                4: match_info[5]
            },
            "link": match_info[6]
        }
        matches_data.append(match_data)

    return matches_data


def check_categories(data):
    for match_data in data:
        categories = match_data["categories"]
        for key, value in categories.items():
            if pd.notna(value):
                return True

    return False


def check_for_element(driver, selector, click=False, xpath=False):
  try:
    if xpath: element = driver.find_element(By.XPATH, selector)
    else: element = driver.find_element(By.CSS_SELECTOR, selector)
    if click: click_button_safe(driver, element)
    return element
  except: return False


def wait_for_cart(driver, email, password):
    data = []
    try:
        try:
            info_head = driver.find_elements(By.CSS_SELECTOR, '#cart-summary-form > ul > li')
        except: pass
        for info in info_head:
            try: 
                price = info.find_element(By.CSS_SELECTOR, 'div.product-unit-price.d-none.d-lg-flex')
                print("price ", price.text)
            except:pass
            try:
                quantity = info.find_element(By.CSS_SELECTOR, 'div.product-qty.d-none.d-lg-flex')
                print("quantity ", quantity.text)
            except: pass
            try: 
                title = info.find_element(By.CLASS_NAME, 'product-title-wrapper')
                print("title ", title.text)
            except: pass
            try:
                seats = info.find_element(By.CSS_SELECTOR, '.seat-content')
                print('seat', seats.text)
            except: pass
            try:
                category = info.find_element(By.CSS_SELECTOR, '.product-category')
                print('category', category.text)
            except: pass
            cookies = driver.get_cookies()
            cookies_json = json.dumps(cookies)
            data.append({"title": title.text, 'price': price.text,
                    "quantity": quantity.text, 'seat-content': seats.text, 'user': 'general',
                    'category': category.text, "account_name": email, "account_password": password})
        return data
    except:
        return False

def change_iframe(driver, selector):
    try:
        iframe = driver.find_element(By.CSS_SELECTOR, selector)
        driver.switch_to.frame(iframe)
        return driver, True
    except: return driver, False


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
    driver.execute_script("document.body.style.zoom='50%'")
    driver.execute_script("arguments[0].scrollIntoView();", button)

    button.click()


def click_button_safe_scrolling(driver, button):
    try:
        button.click()
    except WebDriverException:
        # Scroll to the button to make it clickable
        driver.execute_script("arguments[0].scrollIntoView();", button)
        driver.execute_script("window.scrollBy(0, 100);")
        button.click()


def bypass_captcha(driver, data, selector):
    element = check_for_element(driver, selector, click=True)
    if not element: return
    element.clear()
    for k in data:
        element.send_keys(k)
        time.sleep(.1)
    contButton = driver.find_element(By.CSS_SELECTOR, '#edit-submit')
    contButton.click()


def pass_data(driver, data, selector):
  while True:
    try:
      iframe = driver.find_element(By.CSS_SELECTOR, 'iframe[title=reCAPTCHA]')
      driver.switch_to.frame(iframe)
      if not wait_for_element(driver, '#rc-anchor-container', wait=5):
          driver.switch_to.default_content()
          element = check_for_element(driver, selector, click=True)
          if not element: break
          element.clear()
          for k in data:
            element.send_keys(k)
            time.sleep(.1)
          contButton = driver.find_element(By.CSS_SELECTOR, '#edit-submit')
          contButton.click()
          break
      else:
          if not wait_for_element(driver, 'span[id="recaptcha-anchor"][aria-checked="true"]', wait=60): raise Exception
          driver.switch_to.default_content()
          element = check_for_element(driver, selector, click=True)
          if not element: break
          element.clear()
          for k in data:
            element.send_keys(k)
            time.sleep(.1)
          contButton = driver.find_element(By.CSS_SELECTOR, '#edit-submit')
          contButton.click()
          break
    except:
      driver.switch_to.default_content()
      driver.refresh()
      continue


def login_page(driver, email, password):
  while True:
    # check_for_captcha_and_403(driver)
    if check_for_element(driver, 'input[name="name"]'): pass_data(driver, email, 'input[name="name"]')
    if check_for_element(driver, 'input[type="password"]'): pass_data(driver, password, 'input[type="password"]')
    if not 'https://tickets.rugbyworldcup.com/en/user/login' in driver.current_url: break


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


def main(link, categories):
    driver = selenium_connect()
    email, password = get_random_email_and_password('./accounts.txt')
    while True:
        driver.get(link)
        while True:
            if check_for_element(driver, '#captcha-container'): time.sleep(5)
            else: break
        while True:
            if check_for_element(driver, "//*[contains(text(), '403 ERROR')]", xpath=True): 
                time.sleep(30)
                continue
            else: break
        wait_for_element(driver, '#onetrust-accept-btn-handler', wait=10, click=True)
        if check_for_element(driver, 'a[class="btn user-account-login"]', click=True): login_page(driver, email, password)
        check_for_element(driver, '//*[@data-filter="category"]', click=True, xpath=True)
        check_for_element(driver, '//*[@class="filter-wrapper info-category"]//label[contains(text(),"Select all")]|//*[@class="filter-wrapper info-category"]//label[contains(text(),"Unselect all")]', click=True, xpath=True)
        avctg = [int(re.compile('\d').findall(c.text)[-1]) for c in driver.find_elements(By.XPATH,
                                                                                  '//*[@class="filter-wrapper info-category"]//*[@class="first-letter-cap"]')]
        wanted = []
        for key in categories.keys():
           if key in avctg:
              check_for_element(driver, f'//*[@class="filter-wrapper info-category"]//*[@class="first-letter-cap"][contains(text(),"Y {key}")]', click=True, xpath=True)
              wanted.append(key)
        if wanted == []: continue
        check_for_element(driver, '//*[@class="filter-wrapper info-category"]//button[contains(text(),"Apply")][not(@disabled)]', click=True, xpath=True)
        try:
            tickets = driver.find_elements(By.CSS_SELECTOR, 'tr[role="row"]')
            for ticket in tickets:
                ticket.click()
                raw_category = ticket.find_element(By.CSS_SELECTOR, 'td > div.pack-row-left > span.category-info').text
                formatted_category = int(raw_category.split(' ')[1])
                raw_ticket = ticket.find_element(By.CSS_SELECTOR, 'td > div.pack-row-left > span.tickets-info').text
                formatted_ticket = int(raw_ticket.split(' ')[0])
                yn = []
                for key in categories.keys():
                    if formatted_category == key: yn.append(formatted_category)
                if yn == []: continue 
                if formatted_ticket >= int(categories[formatted_category]):
                    try:
                        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@class="resale-listing-details"]//*[@type="submit"]')))
                        button = driver.find_element(By.XPATH, '//*[@class="resale-listing-details"]//*[@type="submit"]')
                        click_button_safe_scrolling(driver, button)
                    except: print("didn't find ticket")
                    try:
                        WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[class="ui-dialog-titlebar-close"]')))
                        av = driver.find_element(
                            By.XPATH, '//div[./div/span[@class="ui-dialog-title"]]/div[2]').text
                        print(av)
                        driver.get(link)
                        break
                    except: print("didn't find error")
                    try:
                        av = driver.find_element(By.CSS_SELECTOR, 'button[class="btn-remove button js-form-submit form-submit btn js-remove-pack-btn"]')
                        check_for_element(driver, '//a[@href="/en/cart"]', click=True, xpath=True)
                        driver.get('https://tickets.rugbyworldcup.com/en/cart')
                        data, fs = sf.read('noti.wav', dtype='float32')  
                        sd.play(data, fs)
                        status = sd.wait()
                        data = wait_for_cart(driver, email, password)
                        try:
                            json_data = json.dumps(data)
                            
                        except Exception as e:
                            print(e)
                        # Set the headers to specify the content type as JSON
                        headers = {
                            "Content-Type": "application/json"
                        }

                        # Send the POST request
                        try:
                            response = requests.post("http://localhost:8080/book", data=json_data, headers=headers)
                            print(response)
                        except Exception as e:
                            print(e)
                        # Check the response status code
                        if response.status_code == 200:
                            print("POST request successful!")
                        else:
                            print("POST request failed.")
                        print('waiting for 20 min')
                        time.sleep(1200)
                        driver.get(link)
                        continue
                    except Exception as e:
                        print(e)
                        driver.get(link)
                        continue

        except Exception as e: 
            print(e)
        

if __name__ == "__main__":
    matches_data = read_excel("./r.xlsx")
    threads = []
    option = input('Choose one option [ONE|ALL]: ')
    if option in ["all", "ALL"]: 
        for row in matches_data:
            link = row["link"]
            if not pd.notna(link): continue
            categories = row["categories"]
            types = []
            for value in categories.values():
                if pd.notna(value): types.append(value)
            if types == []: continue
            match = row["match"]
            thread = threading.Thread(target=main, args=(link, categories))
            thread.start()
            threads.append(thread)


            delay = random.uniform(5, 10)
            time.sleep(delay)
        for thread in threads:
            thread.join()
    elif option in ['one', 'ONE']:
        for row_index in range(len(matches_data)):
            link = matches_data[row_index]["link"]
            if not pd.notna(link): continue
            categories = matches_data[row_index]["categories"]
            types = []
            for value in categories.values():
                if pd.notna(value): types.append(value)
            if types == []: continue
            match = matches_data[row_index]["match"]
            print(row_index, match)
        row_index = input('Index: ')
        link = matches_data[int(row_index)]['link']
        categories = matches_data[int(row_index)]['categories']
        thread = threading.Thread(target=main, args=(link,categories))
        thread.start()
        threads.append(thread)