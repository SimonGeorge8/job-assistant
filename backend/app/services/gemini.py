from google import genai
import os
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()


# Access the variables
gemini_api_key = os.getenv("GEMINI_API_KEY")

client = genai.Client()

response = client.models.generate_content(
    model="gemini-2.5-flash", contents="Explain how AI works in a few words"
)
print(response.text)