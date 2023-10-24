import requests
import time

url = input('change ip link:\n')


def send_request():
    try:
        response = requests.get(url)
        if response.status_code == 200:
            print("HTTP request sent successfully.")
        else:
            print(f"Failed to send HTTP request. Status code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    while True:
        send_request()
        time.sleep(120) 