import discord

from bababooey import BababooeyBot 
from settings import GUILD_IDS

def add_admin_commands(bot: BababooeyBot):

    @bot.tree.command()
    async def sync_commands(interaction: discord.Interaction) -> None:
        """Force the command definitions to to re-sync."""
        # This can take a while...
        await interaction.response.defer()

        for guild_id in GUILD_IDS:
            bot.tree.copy_global_to(guild=discord.Object(id=guild_id))
            await bot.tree.sync(guild=discord.Object(id=guild_id))
        await interaction.followup.send("Succesfully synced commands.")
