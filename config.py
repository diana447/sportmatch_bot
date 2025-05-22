import os
from dotenv import load_dotenv
from dataclasses import dataclass

load_dotenv()

@dataclass
class Config:
    bot_token: str
    database_url: str

def load_config():
    return Config(
        bot_token=os.getenv("BOT_TOKEN"),
        database_url=os.getenv("DATABASE_URL"),
    )
