from dotenv import load_dotenv
from google import genai

load_dotenv()           # loads GOOGLE_API_KEY from .env
client = genai.Client() # connects to Google using that key

for m in client.models.list():
    actions = getattr(m, "supported_actions", None) or []
    if "generateContent" in actions:
        print(m.name)