import os
from dotenv import load_dotenv
from backend.database import update_database

def load_environment():
    """Load environment variables from .env file"""
    load_dotenv()

def setup_database():
    """Initialize and update the database"""
    update_database()

def get_discord_token():
    """Get Discord bot token from environment"""
    return os.getenv("DISCORD_TOKEN") 