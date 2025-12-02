import requests
from tools.base import BaseTool

class HttpGET(BaseTool):
    """Tool to perform an HTTP GET request."""

    def __init__(self):
        super().__init__(
            name="http_get", 
            description="Perform an HTTP GET request to a specified URL.", 
            parameters={
                "url": {
                    "type": "string",
                    "required": True
                }
            }
        )

    def run(self, url: str) -> dict:
        response = requests.get(url)
        if response.status_code == 200:
            return {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "body": response.json() if 'application/json' in response.headers.get('Content-Type', '') else response.text
            }
        else:
            raise ValueError(f"HTTP GET request to {url} failed with status code {response.status_code}.")