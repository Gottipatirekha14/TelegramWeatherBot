# Telegram Weather Report Bot

A Python-based Telegram bot that provides current weather information and a five-day forecast using the OpenWeatherMap API.

## Features

- **Current Weather:** View temperature, feels-like temperature, humidity, wind speed, and weather conditions.
- **City and Village Search:** Find weather information using a place name.
- **Location Disambiguation:** Choose the correct location when multiple places have the same name.
- **GPS Weather:** Share your Telegram location to get local weather information.
- **Five-Day Forecast:** View daily high and low temperatures and the most common weather conditions.
- **Bot Commands:** Use `/start`, `/help`, `/weather`, and `/forecast`.
- **Error Handling:** Handles invalid locations and API or network errors with user-friendly messages.
- **Secure Configuration:** Loads API credentials from environment variables stored in a `.env` file.

## Tech Stack

- Python
- Telegram Bot API
- `python-telegram-bot`
- OpenWeatherMap API
- Requests
- `asyncio`
- `python-dotenv`

## Setup and Installation

1. Clone or download this repository.
2. Create and activate a Python virtual environment.
3. Install the required dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project root and add your credentials:

   ```env
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token
   WEATHER_API_KEY=your_openweathermap_api_key
   ```

5. Run the bot:

   ```bash
   python bot.py
   ```

## Available Commands

| Command | Description |
|---|---|
| `/start` | Start the bot and view its welcome message |
| `/help` | Display usage instructions |
| `/weather` | Retrieve weather for the selected location |
| `/forecast` | Retrieve the five-day forecast |

## Security

Never commit your `.env` file or expose your API credentials publicly.

## Future Improvements

- Add weather alerts and severe-weather notifications.
- Improve forecast presentation.
- Add persistent storage for user preferences.
