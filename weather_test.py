import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("WEATHER_API_KEY")


# Step 1: Get coordinates from location name
location = input("Enter location: ")

geo_url = "https://api.openweathermap.org/geo/1.0/direct"

geo_params = {
    "q": location,
    "limit": 5,
    "appid": API_KEY
}

geo_response = requests.get(geo_url, params=geo_params)
geo_data = geo_response.json()

if not geo_data:
    print("❌ Location not found.")
    exit()

lat = geo_data[0]["lat"]
lon = geo_data[0]["lon"]

print("Latitude:", lat)
print("Longitude:", lon)


# Step 2: Get weather using coordinates
weather_url = "https://api.openweathermap.org/data/2.5/weather"

weather_params = {
    "lat": lat,
    "lon": lon,
    "appid": API_KEY,
    "units": "metric"
}

weather_response = requests.get(weather_url, params=weather_params)
weather_data = weather_response.json()

print("\n🌦️ Weather Report")
print("Location:", weather_data["name"])
print("Temperature:", weather_data["main"]["temp"], "°C")
print("Feels like:", weather_data["main"]["feels_like"], "°C")
print("Humidity:", weather_data["main"]["humidity"], "%")
print("Weather:", weather_data["weather"][0]["description"])
print("Wind speed:", weather_data["wind"]["speed"], "m/s")