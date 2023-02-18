import discord
import discord.ext.commands
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

    # Lightweight re-implementation of discord.ext.commands.Bot.add_cog
    # We only care about the app commands inside the cog, not any other type of
    # command/command group.
    #
    # We don't want to inherit from discord.ext.commands.Bot because that type
    # of bot requires a prefix in addition to supporting slash commands which is
    # more than we want.
    # We have to re-implement because we inherit from discord.Client instead.
    #
    # TODO: Also loop over the cog listeners and add those.
    def add_cog(self, cog: discord.ext.commands.Cog):
        for cmd in cog.get_app_commands():
            self.tree.add_command(cmd)