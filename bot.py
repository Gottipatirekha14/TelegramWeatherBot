
import os
import logging
import asyncio
import requests
from datetime import datetime

from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.error import TelegramError
from telegram.request import HTTPXRequest
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# -------------------- Configuration --------------------

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)


# -------------------- Start Command --------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    location_button = KeyboardButton(
        text="📍 Share My Location",
        request_location=True,
    )

    keyboard = ReplyKeyboardMarkup(
        [[location_button]],
        resize_keyboard=True,
        one_time_keyboard=False,
    )

    await update.message.reply_text(
        "🌦️ Hello! I'm your Weather Report Bot.\n\n"
        "Send a city or village name for current weather.\n"
        "Share your GPS location for local weather.\n\n"
        "Commands:\n"
        "/weather - Current weather for your last selected location\n"
        "/forecast - 5-day forecast\n"
        "/help - Help and instructions",
        reply_markup=keyboard,
    )


# -------------------- Find Locations --------------------

def find_locations(city):
    geo_url = "https://api.openweathermap.org/geo/1.0/direct"

    response = requests.get(
        geo_url,
        params={
            "q": city,
            "limit": 5,
            "appid": WEATHER_API_KEY,
        },
        timeout=20,
    )

    response.raise_for_status()
    return response.json()


# -------------------- Get Current Weather --------------------

def get_weather(lat, lon):
    weather_url = "https://api.openweathermap.org/data/2.5/weather"

    response = requests.get(
        weather_url,
        params={
            "lat": lat,
            "lon": lon,
            "appid": WEATHER_API_KEY,
            "units": "metric",
        },
        timeout=20,
    )

    response.raise_for_status()
    return response.json()


# -------------------- Get 5-Day Forecast --------------------

def get_forecast(lat, lon):
    forecast_url = "https://api.openweathermap.org/data/2.5/forecast"

    response = requests.get(
        forecast_url,
        params={
            "lat": lat,
            "lon": lon,
            "appid": WEATHER_API_KEY,
            "units": "metric",
        },
        timeout=20,
    )

    response.raise_for_status()
    return response.json()


# -------------------- Send Current Weather --------------------

async def send_weather(update: Update, lat, lon, location_name):
    try:
        data = await asyncio.to_thread(get_weather, lat, lon)

        if str(data.get("cod")) != "200":
            await update.message.reply_text(
                "❌ Sorry, I couldn't get the weather for that location."
            )
            return

        temperature = data["main"]["temp"]
        feels_like = data["main"]["feels_like"]
        humidity = data["main"]["humidity"]
        description = data["weather"][0]["description"]
        wind_speed = data["wind"]["speed"]

        message = (
            f"🌦️ Weather in {location_name}\n\n"
            f"🌡️ Temperature: {temperature}°C\n"
            f"🤗 Feels like: {feels_like}°C\n"
            f"💧 Humidity: {humidity}%\n"
            f"☁️ Condition: {description}\n"
            f"💨 Wind speed: {wind_speed} m/s"
        )

        await update.message.reply_text(message)

    except (requests.RequestException, ValueError, KeyError, TypeError) as error:
        logging.warning("Weather request failed: %s", error)
        await update.message.reply_text(
            "❌ Couldn't retrieve the weather right now. Please try again."
        )


# -------------------- Day 5: Weather Command --------------------

async def weather_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    location = context.user_data.get("selected_location")

    if not location:
        await update.message.reply_text(
            "📍 No location selected yet.\n\n"
            "Please send a city or village name, or share your GPS location first."
        )
        return

    await update.message.reply_text("🌦️ Fetching current weather...")

    await send_weather(
        update,
        location["lat"],
        location["lon"],
        location["name"],
    )


# -------------------- Send 5-Day Forecast --------------------

async def send_forecast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    location = context.user_data.get("selected_location")

    if not location:
        await update.message.reply_text(
            "📍 Please send a city or village name first, "
            "or share your GPS location. Then use /forecast."
        )
        return

    lat = location["lat"]
    lon = location["lon"]
    location_name = location["name"]

    try:
        data = await asyncio.to_thread(get_forecast, lat, lon)
        forecast_entries = data.get("list", [])

        if not forecast_entries:
            await update.message.reply_text(
                "❌ No forecast data is available for this location."
            )
            return

        # Group 3-hour forecast entries by date.
        daily = {}

        for entry in forecast_entries:
            forecast_date = entry["dt_txt"].split(" ")[0]

            if forecast_date not in daily:
                daily[forecast_date] = {
                    "temps": [],
                    "conditions": [],
                }

            daily[forecast_date]["temps"].append(entry["main"]["temp"])
            daily[forecast_date]["conditions"].append(
                entry["weather"][0]["description"]
            )

        message = f"🌦️ 5-Day Forecast for {location_name}\n\n"

        for forecast_date, details in list(daily.items())[:5]:
            date_obj = datetime.strptime(forecast_date, "%Y-%m-%d")
            day_name = date_obj.strftime("%a, %d %b")

            high_temp = max(details["temps"])
            low_temp = min(details["temps"])

            condition = max(
                set(details["conditions"]),
                key=details["conditions"].count,
            ).capitalize()

            message += (
                f"📅 {day_name}\n"
                f"🌡️ High: {high_temp:.1f}°C | "
                f"Low: {low_temp:.1f}°C\n"
                f"☁️ {condition}\n\n"
            )

        message += "ℹ️ Forecasts are estimates and may change."

        await update.message.reply_text(message)

    except (requests.RequestException, ValueError, KeyError, TypeError) as error:
        logging.warning("Forecast request failed: %s", error)
        await update.message.reply_text(
            "❌ Couldn't retrieve the forecast right now. Please try again."
        )


# -------------------- Forecast Command --------------------

async def forecast_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await send_forecast(update, context)


# -------------------- Handle GPS Location --------------------

async def handle_location(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    shared_location = update.message.location
    lat = shared_location.latitude
    lon = shared_location.longitude

    context.user_data.pop("locations", None)

    context.user_data["selected_location"] = {
        "lat": lat,
        "lon": lon,
        "name": "your shared location",
    }

    await update.message.reply_text(
        "📍 Location received! Fetching current weather..."
    )

    await send_weather(update, lat, lon, "your shared location")


# -------------------- Handle Text Messages --------------------

async def handle_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    user_input = update.message.text.strip()

    # Handle numbered location selection.
    if user_input.isdigit() and "locations" in context.user_data:
        locations = context.user_data["locations"]
        choice = int(user_input)

        if choice < 1 or choice > len(locations):
            await update.message.reply_text(
                f"❌ Please choose a number between 1 and {len(locations)}."
            )
            return

        selected = locations[choice - 1]
        context.user_data.pop("locations", None)

        location_name = selected.get("name", "your selected location")

        context.user_data["selected_location"] = {
            "lat": selected["lat"],
            "lon": selected["lon"],
            "name": location_name,
        }

        await send_weather(
            update,
            selected["lat"],
            selected["lon"],
            location_name,
        )
        return

    # Search for the city or village without blocking the bot.
    try:
        locations = await asyncio.to_thread(find_locations, user_input)

    except (requests.RequestException, ValueError) as error:
        logging.warning("Location search failed: %s", error)
        await update.message.reply_text(
            "❌ Couldn't search for that location right now. Please try again."
        )
        return

    if not locations:
        context.user_data.pop("locations", None)
        await update.message.reply_text(
            f"❌ Sorry, I couldn't find '{user_input}'. "
            "Please check the spelling and try again."
        )
        return

    if len(locations) == 1:
        selected = locations[0]
        context.user_data.pop("locations", None)

        location_name = selected.get("name", user_input)

        context.user_data["selected_location"] = {
            "lat": selected["lat"],
            "lon": selected["lon"],
            "name": location_name,
        }

        await send_weather(
            update,
            selected["lat"],
            selected["lon"],
            location_name,
        )
        return

    # Multiple matches: save them for numbered selection.
    context.user_data["locations"] = locations

    message = f"📍 I found {len(locations)} locations for '{user_input}'.\n\n"

    for i, place in enumerate(locations):
        details = ", ".join(
            part
            for part in [
                place.get("name", ""),
                place.get("state", ""),
                place.get("country", ""),
            ]
            if part
        )

        message += (
            f"{i + 1}️⃣ {details}\n"
            f"📍 Coordinates: {place.get('lat', 0):.2f}, "
            f"{place.get('lon', 0):.2f}\n\n"
        )

    message += (
        "👉 Reply with a number to select a location.\n"
        "📍 Or share your GPS location."
    )

    await update.message.reply_text(message)


# -------------------- Help Command --------------------

async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await update.message.reply_text(
        "🌦️ Weather Bot Help\n\n"
        "• Send a city or village name for current weather.\n"
        "• Share your GPS location for current weather.\n"
        "• Use /weather to refresh weather for your last selected location.\n"
        "• Use /forecast for the 5-day forecast of your last selected location.\n"
        "• If multiple locations match, reply with the desired number.\n"
        "• Use /start to see the welcome message."
    )


# -------------------- Error Handler --------------------

async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE,
):
    error = context.error

    if isinstance(error, TelegramError):
        logging.warning("Telegram communication issue: %s", error)
    else:
        logging.error("Unexpected bot error", exc_info=error)


# -------------------- Create Application --------------------

if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN is missing. Check your .env file.")

if not WEATHER_API_KEY:
    raise ValueError("WEATHER_API_KEY is missing. Check your .env file.")

telegram_request = HTTPXRequest(
    connect_timeout=30,
    read_timeout=30,
    write_timeout=30,
    pool_timeout=30,
)

app = (
    Application.builder()
    .token(TELEGRAM_BOT_TOKEN)
    .request(telegram_request)
    .build()
)

# Register handlers
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("weather", weather_command))
app.add_handler(CommandHandler("forecast", forecast_command))
app.add_handler(CommandHandler("help", help_command))

app.add_handler(MessageHandler(filters.LOCATION, handle_location))
app.add_handler(
    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
)

app.add_error_handler(error_handler)


# -------------------- Run Bot --------------------

if __name__ == "__main__":
    print("🌦️ Weather Bot is running!")
    app.run_polling()
