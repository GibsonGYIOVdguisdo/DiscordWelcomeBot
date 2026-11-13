import os
from datetime import datetime, timedelta
import discord
from discord import app_commands
from welcome_tracker import WelcomeCountTracker

class WelcomeBot(discord.Client):
    def __init__(
        self,
        channel: int = None,
        guild_id: int = None,
        role: int = None,
        tracker: WelcomeCountTracker = None,
        intents: discord.Intents = None,
        **kwargs
    ):
        if intents is None:
            intents = discord.Intents.default()
            intents.message_content = True
            intents.members = True

        super().__init__(intents=intents, **kwargs)

        self.channel = channel
        self.guild_id = guild_id
        self.role = role

        self.tree = app_commands.CommandTree(self)
        self.tracker = tracker
        self._setup_commands()

    def _setup_commands(self):
        @self.tree.command(
            name="leaderboard",
            description="Weekly welcome leaderboard",
            guild=discord.Object(id=self.guild_id) if self.guild_id else None
        )
        @app_commands.default_permissions(administrator=True)
        async def leaderboard(interaction: discord.Interaction, all_time: bool = False):
            guild_id = interaction.guild_id or self.guild_id
            top_10 = await self.tracker.get_top_10(guild=guild_id, weekly=not all_time)
            leaderboard_text = ""
            for i, (user_id, count) in enumerate(top_10, 1):
                member = interaction.guild.get_member(user_id) if interaction.guild else None
                name = member.display_name if member else user_id
                leaderboard_text += f"\n{i}. {name} ({count})"
            embed = discord.Embed(title=f"Welcome Leaderboard", description=f"{leaderboard_text}", color=discord.Color.blue())
            await interaction.response.send_message(embed=embed)

        @self.tree.command(
            name="welcomes",
            description="Check how many welcomes you have this week",
            guild=discord.Object(id=self.guild_id) if self.guild_id else None
        )
        @app_commands.default_permissions(administrator=True)
        async def welcomes(interaction: discord.Interaction):
            guild_id = interaction.guild_id or self.guild_id
            count = await self.tracker.get_welcomes_count(interaction.user.id, guild=guild_id, weekly=True)
            await interaction.response.send_message(f"You have welcomed {count} people", ephemeral=True)

        @self.tree.command(
            name="add_welcome",
            description="test",
            guild=discord.Object(id=self.guild_id) if self.guild_id else None,
        )
        @app_commands.default_permissions(administrator=True)
        async def add(interaction: discord.Interaction, fake_member: int):
            guild_id = interaction.guild_id or self.guild_id
            await self.tracker.add_welcome(interaction.user.id, fake_member, guild=guild_id)

            await interaction.response.send_message(f"done", ephemeral=True)

        @self.tree.command(
            name="welcome_message",
            description="test",
            guild=discord.Object(id=self.guild_id) if self.guild_id else None,
        )
        @app_commands.default_permissions(administrator=True)
        async def welcome_message(interaction: discord.Interaction):
            await self.send_welcome_message(interaction.user)
            await interaction.response.send_message(f"done", ephemeral=True)

        @self.tree.command(
            name="update_best_role",
            description="test",
            guild=discord.Object(id=self.guild_id) if self.guild_id else None,
        )
        @app_commands.default_permissions(administrator=True)
        async def update_best_role_cmd(interaction: discord.Interaction):
            if interaction.guild:
                await self.update_best_role(interaction.guild)
            await interaction.response.send_message(f"done", ephemeral=True)

    async def on_ready(self):
        print(f'Logged on')
        guild = discord.utils.get(self.guilds, id=self.guild_id)
        if guild:
            await self.tree.sync(guild=discord.Object(id=self.guild_id))
            print(f"Slash commands synced with guild: {guild.name}")
        else:
            print("Guild not found ")
        print(f'Synced')

    async def on_member_join(self, member: discord.Member):
        await self.send_welcome_message(member)

    async def on_member_leave(self, member: discord.Member):
        message: discord.Message = await self.get_channel(self.channel).history().find(lambda m: m.author.id == self.user.id and member in m.mentions)
        if message:
            await message.delete()

    async def send_welcome_message(self, member: discord.Member):
        embed = discord.Embed(title=f"Welcome {member.display_name}", description=f"Get some roles in the role channel", color=discord.Color.blue())
        embed.set_image(url=member.display_avatar.url)
        channel = self.get_channel(self.channel)
        await channel.send(f"<@{member.id}>", embed=embed, delete_after=300)

    async def on_message(self, message: discord.Message):
        if message.author.id != self.user.id and message.guild:
            welcomes = self.get_welcomes_in_message(message)
            for member in welcomes:
                if not await self.tracker.already_welcomed(message.author.id, member.id, guild=message.guild.id):
                    await self.tracker.add_welcome(message.author.id, member.id, guild=message.guild.id)
            if welcomes:
                await self.update_best_role(message.guild)

    def get_welcomes_in_message(self, message: discord.Message) -> list[discord.Member]:
        mentions = []
        for mention in message.mentions:
            if mention.joined_at > datetime.now() - timedelta(minutes=5):
                mentions.append(mention)
        if message.reference:
            for mention in message.reference.resolved.mentions:
                if message.author.joined_at > datetime.now() - timedelta(minutes=5):
                    mentions.append(mention)
        return list(set(mentions))

    async def update_best_role(self, guild: discord.Guild):
        role = guild.get_role(self.role)
        top_welcomer_id, welcomes = await self.tracker.get_top_welcomer(guild=guild.id)
        if not top_welcomer_id or not role:
            return
        top_has_role = False
        for member in role.members:
            if member.id != top_welcomer_id:
                await member.remove_roles(role)
            elif role in member.roles:
                top_has_role = True
        if not top_has_role: 
            member = guild.get_member(top_welcomer_id)
            if member:
                await member.add_roles(role)
