import os
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
	raise ValueError("OPENROUTER_API_KEY не установлен")

API_KEY_TRELLO = os.getenv("API_KEY_TRELLO")
if not API_KEY_TRELLO:
	raise ValueError("API_KEY_TRELLO не установлен")

API_TOKEN_TRELLO = os.getenv("API_TOKEN_TRELLO")
if not API_TOKEN_TRELLO:
	raise ValueError("API_TOKEN_TRELLO не установлен")