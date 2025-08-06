import requests

class ImageOfTheDayLogic:
    NASA_URL = "https://api.nasa.gov/planetary/apod"
    API_KEY = "DEMO_KEY"  # Replace with your NASA API key if needed

    @staticmethod
    def fetch_image(date=None):
        params = {"api_key": ImageOfTheDayLogic.API_KEY}
        if date:
            params["date"] = date
        try:
            response = requests.get(ImageOfTheDayLogic.NASA_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data.get("url"), data.get("title"), data.get("explanation"), None
        except Exception as e:
            return None, None, None, str(e)
