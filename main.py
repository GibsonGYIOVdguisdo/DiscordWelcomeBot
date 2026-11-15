import os
import dotenv
from welcome_bot import WelcomeBot
from database.welcome_collection import WelcomeCollection
from database.guild_collection import GuildCollection
import asyncio

dotenv.load_dotenv()
TOKEN = os.getenv("TOKEN")
GUILD_ID = int(os.getenv("GUILD"))
MONGO_URI = os.getenv("MONGO_URI")


async def main():
    welcome_collection = WelcomeCollection(MONGO_URI)
    guild_collection = GuildCollection(MONGO_URI)
    bot_client = WelcomeBot(guild_id=GUILD_ID, welcome_collection=welcome_collection, guild_collection=guild_collection)
    await bot_client.start(TOKEN)


if __name__ == "__main__":
    asyncio.run(main())