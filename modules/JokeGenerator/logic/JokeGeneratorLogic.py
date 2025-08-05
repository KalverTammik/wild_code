"""
JokeGeneratorLogic: Handles joke fetching and business logic for Joke Generator module.
"""
import requests

class JokeGeneratorLogic:
    API_URL = "https://icanhazdadjoke.com/"

    def fetch_joke(self):
        """Fetch a random joke from the API."""
        try:
            headers = {"Accept": "application/json"}
            response = requests.get(self.API_URL, headers=headers)
            if response.status_code == 200:
                return response.json().get("joke", "No joke found.")
            else:
                return f"Error: Unable to fetch joke (Status {response.status_code})"
        except Exception as e:
            return f"Error: {str(e)}"
