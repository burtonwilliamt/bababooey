import discord
from discord import app_commands

class BababooeyBot(discord.Client):

    def __init__(self,
                 *,
                 intents: discord.Intents,
                 guild_ids: list[int] = None,
                 force_command_sync: bool = False):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.guild_ids = guild_ids
        self.force_command_sync = force_command_sync

    async def setup_hook(self):
        if self.force_command_sync:
            await self.sync_command_definitions()

    async def sync_command_definitions(self):
        if self.guild_ids is not None:
            for guild_id in self.guild_ids:
                self.tree.copy_global_to(guild=discord.Object(id=guild_id))
                await self.tree.sync(guild=discord.Object(id=guild_id))
        else:
            pass