import discord.ext.commands
from discord import app_commands

from bababooey import BababooeyBot


class AdminCog(discord.ext.commands.Cog):
    """A collection of administrative commands for the bot."""

    def __init__(self, bot: BababooeyBot):
        self.bot = bot

    @app_commands.command()
    async def sync_commands(self, interaction: discord.Interaction) -> None:
        """Force the command definitions to to re-sync."""
        # This can take a while...
        await interaction.response.defer()
        await self.bot.sync_command_definitions()
        await interaction.followup.send("Succesfully synced commands.")
