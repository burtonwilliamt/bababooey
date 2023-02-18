import re

import discord
from discord import app_commands

from bababooey import BababooeyBot, Catalog
from bababooey.ui import make_soundboard_views, SoundEffectDetailButtons, SoundEffectButton
from settings import SOUNDBOARD_CHANNELS

CUSTOM_EMOJI_RE = re.compile(r'<:.+:\d+>')


def _unicode_safe_emoji(discord_emoji: str) -> str:
    if CUSTOM_EMOJI_RE.match(discord_emoji):
        return chr(0x1f7e6)
    return discord_emoji


def add_sound_effect_commands(bot: BababooeyBot):

    catalog = Catalog()

    async def _autocomplete_sound_effect_name(
            interaction: discord.Interaction,
            partial_sound: str) -> list[app_commands.Choice[str]]:
        if partial_sound == '':
            matches = catalog.users_most_recent(interaction.user, 25)
        else:
            matches = catalog.find_partial_matches(partial_sound)
        return [
            app_commands.Choice(
                name=f'{_unicode_safe_emoji(sfx.emoji)} {sfx.name}',
                value=sfx.name) for sfx in matches[0:25]
        ]

    # user.id -> discord.Interaction
    previous_x_interaction = {}

    @bot.tree.command()
    @app_commands.describe(search='Look for a sound effect by name or tags.')
    @app_commands.autocomplete(search=_autocomplete_sound_effect_name)
    async def x(interaction: discord.Interaction, search: str):
        """Play a sound effect."""
        sfx = catalog.by_name(search)
        if sfx is None:
            await interaction.response.send_message(
                f'I don\'t know a sound effect by the name of `{search}`.')
            return

        # Play the requested sound effect.
        await sfx.play_for(interaction.user)

        # Collect the recent sounds to display.
        recent_sfx = catalog.users_most_recent(interaction.user, 5)
        view = discord.ui.View()
        for i, sfx in enumerate(reversed(recent_sfx)):
            view.add_item(SoundEffectButton(sfx, row=i))
        await interaction.response.send_message(view=view, ephemeral=True)

        # Delete the previous /x message to keep chat clean.
        if interaction.user.id in previous_x_interaction:
            await previous_x_interaction[interaction.user.id
                                        ].delete_original_response()
        previous_x_interaction[interaction.user.id] = interaction

    @bot.tree.command()
    @app_commands.describe(search='Look for a sound effect by name or tags.')
    @app_commands.autocomplete(search=_autocomplete_sound_effect_name)
    async def edit_sound(
        interaction: discord.Interaction,
        search: str,
    ):
        """Edit a sound effect."""
        sfx = catalog.by_name(search)
        if sfx is None:
            await interaction.response.send_message(
                f'I don\'t know a sound effect by the name of `{search}`.')
            return
        await interaction.response.send_message(
            embed=sfx.details_embed(), view=SoundEffectDetailButtons(sfx))

    @bot.tree.command()
    async def sync_soundboard(interaction: discord.Interaction):
        """Redraw the soundboard channel."""
        if interaction.guild.id not in SOUNDBOARD_CHANNELS:
            await interaction.response.send_message(
                'This server does not have a soundboard channel configured.')
        soundboard_channel = await bot.fetch_channel(
            SOUNDBOARD_CHANNELS[interaction.guild.id])
        await interaction.response.defer()
        views = make_soundboard_views(catalog.all(), interaction.guild_id)
        
        # Check the history in that channel.
        expected_number_of_messages = len(views)
        messages = [
            msg async for msg in soundboard_channel.history(
                limit=expected_number_of_messages + 1)
        ]
        # If there is a lot of messages (more than a soundboard), then maybe the
        # channel was used by something else first. Avoid deleting all the
        # messages to preserve people's history.
        if len(messages) > expected_number_of_messages:
            await interaction.followup.send(
                'There are more than the expected number of messages '
                f'({expected_number_of_messages}) in {soundboard_channel}, '
                'just to be safe I don\'t want to delete the history.'
            )
            return

        # Similarly, if there are some messages sent by someone other than the
        # bot, we know it's something we didn't create so preserve it.
        for msg in messages:
            if msg.author.id != bot.user.id:
                await interaction.followup.send(
                    f'Someone else sent messages in {soundboard_channel}, '
                    'just to be safe I don\'t want to delete the history.'
                )
                return

        for msg in messages:
            await msg.delete()

        for view in views:
            await soundboard_channel.send(view=view)

        await interaction.followup.send(
            f'Sent a fresh soundboard in {soundboard_channel}')

    @bot.tree.command()
    async def history(interaction: discord.Interaction):
        """See the global sound effect history."""
        await interaction.response.defer()
        lines = []
        for dt, user_id, _, sfx in catalog.all_history()[0:20]:
            # Try to use the cache first.
            user = interaction.guild.get_member(user_id)
            if user is None:
                # This can be slow, hopefully we only have to do this once per
                # user_id.
                user = await interaction.guild.fetch_member(user_id)
            lines.append(
                f'`{dt:%H:%M:%S}` {sfx.emoji}`{sfx.name:>12}` {user.display_name}'
            )

        await interaction.followup.send('\n'.join(lines))
