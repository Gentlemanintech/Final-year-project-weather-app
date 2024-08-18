from flask import Flask, render_template, request, session
from datetime import datetime, timedelta
import requests
import geocoder
from flask_session import Session

app = Flask(__name__)

# Initiationg the session.
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

apiKey = "c0e609cd023a47eab7073826241808"
# Ip address of the user
userLocation = geocoder.ip('me')

# this code here sets the browser on which the user visits not to save any cache so it gets latest version of the page.
@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/", methods=["POST", "GET"])
def index():
    if request.method == "POST":
        location = request.form.get("location")
        if location:
            session['location'] = location
    location = session.get('location', None)

    if not location:
        userLocation = geocoder.ip('me')
        location = userLocation.state  # Default location if session doesn't have one

    date = datetime.now()
    date_today = date.strftime("%A, %d %b")
    current_hour = date.hour  # Current hour in 24-hour format
    current_weather_url = f"https://api.weatherapi.com/v1/forecast.json?key={apiKey}&q={location}&days=1"

    data = retrieveData(current_weather_url)
    
    # Adjust hourly forecast and filter
    if 'forecast' in data:
        filtered_hours = []
        for hour in data['forecast']['forecastday'][0]['hour']:
            hour_time = datetime.strptime(hour['time'], '%Y-%m-%d %H:%M')
            if hour_time.hour > current_hour:  # Only include hours greater than the current hour
                # Increment by 1 hour
                next_hour_time = hour_time + timedelta(hours=0)
                hour['adjusted_time'] = next_hour_time.strftime('%H:%M')
                filtered_hours.append(hour)
        
        # Update the data with filtered hours
        data['forecast']['forecastday'][0]['hour'] = filtered_hours

    
    return render_template("today.html", date=date_today, data=data, location=location)

@app.route('/tomorrow')
def tomorrow():
    location = session.get("location")
    date = datetime.now()
    tomorrow_date = date + timedelta(days=1)
    formatted_date = tomorrow_date.strftime('%Y-%m-%d')
    tomorrowForecast = f"https://api.weatherapi.com/v1/forecast.json?key={apiKey}&q={location}&dt={formatted_date}"

    data = retrieveData(tomorrowForecast)
    
    # Debugging: Print data to ensure it has the correct structure
    hourly_forecast = data.get('forecast', {}).get('forecastday', [{}])[0].get('hour', [])
    
    return render_template("tomorrow.html", data=data, hourlyForecast=hourly_forecast, location=location)


@app.route('/6days')
def sixDays():
    # Get the location from the session
    location = session.get("location")
    today = datetime.now().date()  # Get today's date

    # Construct the URL with the end date (7 days forecast to include the next 6 days)
    forecast_url = f"https://api.weatherapi.com/v1/forecast.json?key={apiKey}&q={location}&days=7"

    # Retrieve data from the API
    data = retrieveData(forecast_url)
    
    # Extract the 6-day forecast starting from the next day
    forecast_days = data.get('forecast', {}).get('forecastday', [])
    
    # Ensure there are at least 7 days in the forecast
    if len(forecast_days) > 1:
        # Skip the first day's forecast (today) and take the next 6 days
        six_days_forecast = forecast_days[1:7]
    else:
        six_days_forecast = []

    # Render the template with the 6-day forecast and location
    return render_template("sixDays.html", forecastDays=six_days_forecast, location=location)


def retrieveData(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raises an HTTPError if the response code was unsuccessful
        data = response.json()
    except requests.exceptions.HTTPError as http_err:
        data = {'error': f'HTTP error occurred: Check the Location and input a correct one'}
    except requests.exceptions.ConnectionError:
        data = {'error': f'Connection error occurred: Please check your internet connection and try again'}
    except requests.exceptions.Timeout as timeout_err:
        data = {'error': f'Timeout error occurred: Connection timeout, Please try again'}
    except requests.exceptions.RequestException as req_err:
        data = {'error': f'An error occurred: {req_err}'}

    return data


def format_date(value):
    # Parse the input date string into a datetime object
    date_obj = datetime.strptime(value, "%Y-%m-%d")
    # Format the date as "Day, YYYY-MM-DD"
    return date_obj.strftime("%A, %Y-%m-%d")

# Register the custom filter with Jinja
app.jinja_env.filters['format_date'] = format_date


if __name__ == "__main__":
    app.run(debug=True)
