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
                        guild=guild_id
                    )
                )

    async def get_top_welcomer_role(self, guild_id):
        guild_document: Guild = await self.collection.find_one({"guild":guild_id})
        if not guild_document: return None
        return guild_document.get("top_welcomer_role", None)

    async def set_top_welcomer_role(self, guild_id: int, role_id: int):
        guild_document: Guild = await self.collection.find_one({"guild":guild_id})
        guild_document["top_welcomer_role"] = role_id
        await self.collection.find_one_and_replace({"guild":guild_id}, guild_document)

    async def get_welcome_channel(self, guild_id: int):
        guild_document: Guild = await self.collection.find_one({"guild":guild_id})
        if not guild_document: return None
        return guild_document.get("welcome_channel", None)

    async def set_welcome_channel(self, guild_id: int, channel_id: int):
        guild_document: Guild = await self.collection.find_one({"guild": guild_id})
        guild_document["welcome_channel"] = channel_id
        await self.collection.find_one_and_replace({"guild":guild_id}, guild_document)

    async def add_customisable_role(self, guild_id: int, role_id: int, default_name: str):
        guild_document: Guild = await self.collection.find_one({"guild": guild_id})
        if "customisable_roles" not in guild_document: guild_document["customisable_roles"] = {}
        guild_document["customisable_roles"][str(role_id)] = default_name
        await self.collection.find_one_and_replace({"guild":guild_id}, guild_document)

    async def remove_customisable_role(self, guild_id: int, role_id: int):
        guild_document: Guild = await self.collection.find_one({"guild": guild_id})
        if role_id in guild_document["customisable_roles"]:
            del guild_document["customisable_roles"][str(role_id)]
        await self.collection.find_one_and_replace({"guild":guild_id}, guild_document)

    async def get_customisable_roles(self, guild_id: int):
        guild_document: Guild = await self.collection.find_one({"guild": guild_id})
        customisable_roles = {}
        for k, v in guild_document.get("customisable_roles", {}).items():
            customisable_roles[int(k)] = v
        return customisable_roles

    async def close_client(self):
        await self.client.close()
