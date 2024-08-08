from flask import Flask, render_template
from datetime import datetime
import requests

app = Flask(__name__)

url = "https://api.openweathermap.org/data/2.5/weather?q=katsina&units=metric&appid=a0c4626aa175a91bd32b76a44cc1b063"

@app.route("/")
def index():
    date = datetime.now()
    date_today = date.strftime("%A, %d %b")
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raises an HTTPError if the response code was unsuccessful
        data = response.json()
        print(data)
    except requests.exceptions.HTTPError as http_err:
        data = {'error': f'HTTP error occurred: {http_err}'}
    except requests.exceptions.ConnectionError:
        data = {'error': f'Connection error occurred: Please check your internet connection and try again'}
    except requests.exceptions.Timeout as timeout_err:
        data = {'error': f'Timeout error occurred: {timeout_err}'}
    except requests.exceptions.RequestException as req_err:
        data = {'error': f'An error occurred: {req_err}'}

    return render_template("today.html", data=data, date=date_today)

if __name__ == "__main__":
    app.run(debug=True)
