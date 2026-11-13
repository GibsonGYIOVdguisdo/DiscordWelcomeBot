import discord
from discord import app_commands
import dotenv
import os
import asyncio
from time import time, sleep
from random import randint

dotenv.load_dotenv()
TOKEN = os.getenv("TOKEN")
CHANNEL = int(os.getenv("CHANNEL"))
GUILD_ID = int(os.getenv("GUILD"))
ROLE = int(os.getenv("ROLE"))


class WelcomeCountTracker:
    def __init__(self, client):
        self.client = client
        self.join_times = {} 
        self.user_welcomes = {}
        self.recent_welcomes = {}  
        self.load_user_welcomes()
    
    def load_user_welcomes(self):
        with open("welcomes.txt" ,"r") as f:
            for line in f.readlines():
                user, amount = line.split(",")
                self.user_welcomes[int(user)] = set()
                for i in range(int(amount)):
                    self.user_welcomes[int(user)].add(i)
        print(f"loaded {self.user_welcomes}")

    def save_user_welcomes(self):
        lines = []
        for user in self.user_welcomes:
            line = f"{user},{len(self.user_welcomes[user])}"
            lines.append(line)
        with open("welcomes.txt" ,"w") as f:
            f.write("\n".join(lines))

    def get_welcome(self, message: discord.Message):
        mentions = []
        for mention in message.mentions:
            if mention.id in self.join_times and time() - self.join_times[mention.id] < 600:
                mentions.append(mention)
        if message.reference and message.reference.resolved.author.id == self.client.user.id:
            for mention in message.reference.resolved.mentions:
                if mention.id in self.join_times and time() - self.join_times[mention.id] < 600:
                    mentions.append(mention)
        return list(set(mentions))

    def get_top_10(self):
        sorted_users = sorted(self.user_welcomes, key=lambda k: len(self.user_welcomes[k]))[-10:]
        return sorted_users

    def member_joined(self, member):
        if member.id not in self.join_times:
            self.join_times[member.id] = time()

    def check_for_welcomes(self, message):
        if message.channel.id == CHANNEL and message.author.id != self.client.user.id:
            welcomes = self.get_welcome(message)
            if len(welcomes) != 0:
                for welcome in welcomes:
                    self.add_user_mentions(message.author, welcome)
                self.save_user_welcomes()
                best = client.get_user(self.get_top_10()[0])
                best_role = client.get_role(ROLE)
                if best_role not in best.roles:
                    for member in best_role.members:
                        member.remove_roles([best_role])
                    best.add_roles([best_role])
                

    def add_user_mentions(self, welcomer, welcomed):
        if welcomer.id not in self.user_welcomes:
            self.user_welcomes[welcomer.id] = set()
        self.user_welcomes[welcomer.id].add(welcomed.id)


intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

tracker = WelcomeCountTracker(client)
cache = {}

@client.event
async def on_ready():
    print(f'Logged on')
    guild = discord.utils.get(client.guilds, id=GUILD_ID)
    if guild:
        await tree.sync(guild=discord.Object(id=GUILD_ID))  # Sync commands with the specific guild
        print(f"Slash commands synced with guild: {guild.name}")
    else:
        print("Guild not found")
    print(f'Synced')


@client.event
async def on_member_update(before, after):
    if len(before.roles) == 1 and len(after.roles) == 2:
        await run_welcome(before)

async def run_welcome(member):
    print("triggered")
    tracker.member_joined(member)
    embed = discord.Embed(title=f"Welcome {member.display_name}", description=f"Get some roles in the role channel", color=discord.Color.blue())
    embed.set_image(url=member.display_avatar.url)
    channel = client.get_channel(CHANNEL)
    message = await channel.send(f"<@{member.id}>", embed=embed)
    cache[member.id] = message
    await asyncio.sleep(900)
    if member.id in cache:
        await cache.pop(member.id).delete()

@client.event
async def on_message(message):
    if "Iamswag-dotestthing" in message.content:
        tracker.add_user_mentions(message.author, message.mentions[0])
        print(tracker.get_top_10())
    tracker.check_for_welcomes(message)


@client.event
async def on_member_remove(member):
    print("leave triggered")
    if member.id in cache:
        await cache.pop(member.id).delete()
    
@tree.command(
    name="leaderboard",
    description="Weekly welcome leaderboard",
    guild=discord.Object(id=GUILD_ID)
)
async def leaderboard(interaction: discord.Interaction):
    top_10 = tracker.get_top_10()[::-1]
    leaderboard_text = ""
    for i in range(min(len(top_10), 10)):
        name = ""
        try:
            name = client.get_user(top_10[i]).display_name
        except:
            name = top_10[i]
        leaderboard_text += f"\n{i}. {name} ({len(tracker.user_welcomes[top_10[i]])})"
    embed = discord.Embed(title=f"Welcome Leaderboard", description=f"{leaderboard_text}", color=discord.Color.blue())
    await interaction.response.send_message(embed=embed)
client.run(TOKEN)