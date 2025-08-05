import requests

class WeatherUpdateLogic:
    BASE_URL = "https://wttr.in/"

    @staticmethod
    def fetch_weather(city):
        if not city:
            return None, None, "no_city"
        try:
            weather_url = f"{WeatherUpdateLogic.BASE_URL}{city}?format=j1"
            weather_response = requests.get(weather_url).json()
            current_condition = weather_response["current_condition"][0]
            temp = current_condition["temp_C"]
            description = current_condition["weatherDesc"][0]["value"]
            forecast = weather_response["weather"]
            return (temp, description, forecast), None, None
        except Exception as e:
            return None, None, str(e)
