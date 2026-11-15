from pymongo import AsyncMongoClient, server_api
from welcome_model import Welcome
from datetime import datetime, UTC, timedelta

class WelcomeCountTracker:
    def __init__(self, mongo_uri: str):
        self.client = AsyncMongoClient(
            mongo_uri,
            server_api=server_api.ServerApi(version="1", strict=True, deprecation_errors=True
        ))

        self.database = self.client["main"]
        self.collection = self.database["welcomes"]

    async def create_collection(self):
        self.collection = await self.database.create_collection("welcomes")

    async def create_indexes(self):
        await self.collection.create_index([("guild", 1), ("date", -1), ("welcomer", 1)])
        await self.collection.create_index([("guild", 1), ("welcomer", 1), ("welcomed", 1)], unique=True)  
    
    async def add_welcome(self, welcomer: int, welcomed: int, guild: int) -> None:
        await self.collection.insert_one(
            Welcome(
                welcomer=welcomer,
                welcomed=welcomed,
                date=datetime.now(tz=UTC),
                guild=guild,
            )
        )

    add_user_mention = add_welcome

    async def already_welcomed(self, welcomer: int, welcomed: int, guild: int = None) -> bool:
        query = {"welcomer": welcomer, "welcomed": welcomed}
        if guild is not None:
            query["guild"] = guild
        doc = await self.collection.find_one(query)
        return doc is not None

    async def get_welcomes_count(self, welcomer: int, guild: int = None, weekly: bool = False) -> int:
        query = {"welcomer": welcomer}
        if guild is not None:
            query["guild"] = guild
        if weekly:
            query["date"] = {"$gte": datetime.now(tz=UTC) - timedelta(days=7)}
        return await self.collection.count_documents(query)

    async def get_top_10(self, guild: int = None, weekly: bool = True) -> list[list[int]]:
        match_stage = {"welcomer": {"$ne": None}}
        if guild is not None:
            match_stage["guild"] = guild
        if weekly:
            now = datetime.now(tz=UTC)
            match_stage["date"] = {"$gte": now - timedelta(
                days=now.weekday(),
                hours=now.hour,
                minutes=now.minute,
                seconds=now.second
            )}

        pipeline = [
            {"$match": match_stage},
            {"$group": {"_id": "$welcomer", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10},
        ]
        cursor = await self.collection.aggregate(pipeline)
        docs = await cursor.to_list(10)
        return [[doc["_id"], doc["count"]] for doc in docs]

    async def get_top_welcomer(self, guild: int = None, weekly: bool = True) -> list[int]:
        match_stage = {"welcomer": {"$ne": None}}
        if guild is not None:
            match_stage["guild"] = guild
        if weekly:
            now = datetime.now(tz=UTC)
            match_stage["date"] = {"$gte": now - timedelta(
                days=now.weekday(),
                hours=now.hour,
                minutes=now.minute,
                seconds=now.second
            )}

        pipeline = [
            {"$match": match_stage},
            {"$group": {"_id": "$welcomer", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 1},
        ]
        cursor = await self.collection.aggregate(pipeline)
        docs = await cursor.to_list(1)
        if not docs:
            return [None, 0]
        doc = docs[0]
        return [doc["_id"], doc["count"]]

    async def close_client(self):
        await self.client.close()
