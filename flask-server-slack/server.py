from flask import Flask, request
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import re
app = Flask(__name__)
counter = 0
# Set up Slack API client
slack_token = "xoxb-773919780944-5889840114549-radxEjeifjtJwFJi4rfECvKm"
slack_client = WebClient(token=slack_token)
# Create a new book
@app.route('/book', methods=['POST'])
def create_book():
    global counter
    pattern = r'(.+)( v )(.+)'
    if request.json:
        for el in request.json:
            # Find matches and groups
            matches = re.match(pattern, el["title"])
            if matches:
                country1 = matches.group(1)
                group2 = matches.group(2)
                country2 = matches.group(3)
                title = country1 + group2 + country2
            else:
                print("No match found.")
            
            counter += 1
            formatted_data = f'*Матч:* _{title}_\n*категорія:* _{el["category"]}_\n*ціна за квиток:* _{el["price"]}_\n*кількість квитків:* _{el["quantity"]}_\n*місця:* _{el["seat-content"]}_\n*користувач:* _{el["user"]}_\n*login:* _{el["account_name"]}_\n*password:* _{el["account_password"]}_'
            send_to_slack_channel(formatted_data)
    return ''
def send_to_slack_channel(data):
    try:
        slack_client.chat_postMessage(
            channel="#rugby-bot",
            text=data,
            parse="mrkdwn"
        )
    except Exception as e:
        print(f"Error: {e}")
if __name__ == '__main__':
    app.run(debug=True, port=500)