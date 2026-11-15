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
        await self.collection.delete_one({"guild":guild_id})
        await self.collection.insert_one(
                    Guild(
                        guild=guild_id, 
                        best_welcomer_role=None,
                        welcome_channel=None,
                    )
                )

    async def get_top_welcomer_role(self, guild_id):
        guild_document: Guild = await self.collection.find_one({"guild":guild_id})
        if not guild_document: return None
        return guild_document.get("top_welcomer_role", None)

    async def set_top_welcomer_role(self, guild_id, role_id):
        guild_document: Guild = await self.collection.find_one({"guild":guild_id})
        guild_document["top_welcomer_role"] = role_id
        await self.collection.update_one({"guild":guild_id}, guild_document)

    async def close_client(self):
        await self.client.close()
