from pymongo import AsyncMongoClient, server_api
from models.guild_model import Guild
from datetime import datetime, UTC, timedelta

class GuildCollection:
    def __init__(self, mongo_uri: str):
        self.client = AsyncMongoClient(
            mongo_uri,
            server_api=server_api.ServerApi(version="1", strict=True, deprecation_errors=True
        ))

        self.database = self.client["main"]
        self.collection = self.database["guilds"]

    async def create_collection(self):
        self.collection = await self.database.create_collection("guilds")

    async def create_guild_document(self, guild_id: int):
        await self.collection.find_one_and_delete({"guild":guild_id})
        await self.collection.insert_one(
                    Guild(
                        guild= guild_id, 
                        best_welcomer_role=None,
                        welcome_channel=None,
                    )
                )



    async def close_client(self):
        await self.client.close()
