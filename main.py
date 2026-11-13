import os
import dotenv
from welcome_bot import WelcomeBot
from welcome_tracker import WelcomeCountTracker
import asyncio

dotenv.load_dotenv()
TOKEN = os.getenv("TOKEN")
CHANNEL = int(os.getenv("CHANNEL"))
GUILD_ID = int(os.getenv("GUILD"))
ROLE = int(os.getenv("ROLE"))
MONGO_URI = os.getenv("MONGO_URI")


async def main():
    tracker = WelcomeCountTracker(MONGO_URI)
    bot_client = WelcomeBot(channel=CHANNEL, guild_id=GUILD_ID, role=ROLE, tracker=tracker)
    await bot_client.start(TOKEN)


if __name__ == "__main__":
    asyncio.run(main())