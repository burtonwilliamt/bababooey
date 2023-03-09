import discord
import discord.ext.commands
from discord import app_commands

from bababooey import InteractionHistory

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
        self.extra_events = {}
        self.interaction_history = InteractionHistory()

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
    def add_cog(self, cog: discord.ext.commands.Cog):
        for cmd in cog.get_app_commands():
            self.tree.add_command(cmd)
        for name, listener in cog.get_listeners():
            if name not in self.extra_events:
                self.extra_events[name] = []
            self.extra_events[name].append(listener)

    # Client does not support extra listeners very well. This is a copy of
    # discord.ext.commands.Bot.dispatch which mostly just calls super() but will
    # also dispatch to our extra_events.
    def dispatch(self, event_name: str, *args, **kwargs):
        super().dispatch(event_name, *args, **kwargs)
        ev = 'on_' + event_name
        for event in self.extra_events.get(ev, []):
            self._schedule_event(event, ev, *args, **kwargs)

    async def on_interaction(self, interaction: discord.Interaction):
        self.interaction_history.record_usage(interaction)