import asyncio
import datetime
import logging
import os
import re

import discord
from discord import app_commands
import discord.ext.commands
import yt_dlp as youtube_dl

from bababooey import BababooeyBot, Catalog, SoundEffectData, VoiceClientManager
from bababooey.ui import make_soundboard_views, SoundEffectButton, SoundEffectCreationManager
from settings import SOUNDBOARD_CHANNELS

_log = logging.getLogger(__name__)

CUSTOM_EMOJI_RE = re.compile(r'<:.+:\d+>')
X_MESSAGE_TTL_SECONDS = 15 * 60.0 - 5.0


async def do_youtube_dl(url: str,
                        loop: asyncio.BaseEventLoop) -> tuple[str, int]:
    """Download a youtube video

    We will return both the path to the downloaded video, as well as
    the duration in seconds.
    
    Returns:
        A tuple[str, int] of the absoloute path, duration_millis respectively.
    """
    os.makedirs('data/youtubedl', exist_ok=True)

    youtube_dl.utils.bug_reports_message = lambda: ''

    ytdl_format_options = {
        'format': 'bestaudio/best',
        # do the conversion using sox
        #'postprocessors': [{
        #'key': 'FFmpegExtractAudio',
        #'preferredcodec': 'mp3',
        #'preferredquality': '192',
        #}],
        'outtmpl': 'data/youtubedl/%(extractor)s-%(id)s-%(title)s.%(ext)s',
        'restrictfilenames': True,
        'noplaylist': True,
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'logtostderr': False,
        'quiet': False,
        'no_warnings': False,
        'default_search': 'auto',
        'source_address':
            '0.0.0.0'  # bind to ipv4 since ipv6 addresses cause issues sometimes
    }

    ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

    _log.info('Downloading song from youtube: %s', url)

    def do_download():
        res = ytdl.extract_info(url, download=True)
        return res

    data = await loop.run_in_executor(None, do_download)
    if 'entries' in data:
        # take first item from a playlist
        data = data['entries'][0]

    filename = ytdl.prepare_filename(data)
    #labeled_format = filename.rsplit('.', 1)[-1]
    #if labeled_format not in ('mp3', 'webm', 'm4a'):

    return (os.path.abspath(filename), data['duration'] * 1000)


def _unicode_safe_emoji(discord_emoji: str) -> str:
    if CUSTOM_EMOJI_RE.match(discord_emoji):
        return chr(0x1f7e6)
    return discord_emoji


class BababooeyCog(discord.ext.commands.Cog):
    """Collection of sound effects and the commands to use them."""

    def __init__(self, bot: BababooeyBot):
        self.bot = bot
        self.voice_client_manager = VoiceClientManager()
        self.catalog = Catalog(self.voice_client_manager)
        # user.id -> discord.Message
        self._previous_x_messages: dict[int, discord.Message] = {}

    @discord.ext.commands.Cog.listener()
    async def on_ready(self):
        for guild_id in SOUNDBOARD_CHANNELS:
            for view in make_soundboard_views(self.catalog.all(), guild_id):
                self.bot.add_view(view)

    async def _autocomplete_sound_effect_name(
            self, interaction: discord.Interaction,
            partial_sound: str) -> list[app_commands.Choice[str]]:
        if partial_sound == '':
            matches = self.catalog.users_most_recent(interaction.user, 25)
        else:
            matches = self.catalog.find_partial_matches(partial_sound)
        return [
            app_commands.Choice(
                name=f'{_unicode_safe_emoji(sfx.emoji)} {sfx.name}',
                value=sfx.name) for sfx in matches[0:25]
        ]

    @app_commands.command()
    @app_commands.describe(search='Look for a sound effect by name or tags.')
    @app_commands.autocomplete(search=_autocomplete_sound_effect_name)
    async def x(self, interaction: discord.Interaction, search: str):
        """Play a sound effect."""
        sfx = self.catalog.by_name(search)
        if sfx is None:
            await interaction.response.send_message(
                f'I don\'t know a sound effect by the name of `{search}`.')
            return

        # Play the requested sound effect.
        await sfx.play_for(interaction.user)

        # Collect the recent sounds to display.
        recent_sfx = self.catalog.users_most_recent(interaction.user, 5)
        view = discord.ui.View(timeout=X_MESSAGE_TTL_SECONDS)
        for i, sfx in enumerate(reversed(recent_sfx)):
            view.add_item(SoundEffectButton(sfx, row=i))
        # Create the /x interface.
        await interaction.response.send_message(
            view=view, ephemeral=True, delete_after=X_MESSAGE_TTL_SECONDS)

        # Handle message cleanup code.
        x_message = await interaction.original_response()
        user_id = interaction.user.id

        # NOTE: If one of the above `await` calls takes a long time, a more
        # recent x/ command might have made it into _previous_x_messages. In
        # that case we don't want to delete it, rather we want to delete our
        # x/ message.
        if user_id in self._previous_x_messages and self._previous_x_messages[
                user_id].created_at > x_message.created_at:
            await x_message.delete()
            return

        # Pop previous message from the dict before doing an async operation on
        # it. This avoids two threads both calling .delete() simultaneously.
        previous_msg = self._previous_x_messages.pop(user_id, None)
        # Assign previous x messages before doing async operation so we're sure
        # we aren't overwriting an assignment from another thread.
        # (Ensuring this is atomic with the above line.)
        self._previous_x_messages[user_id] = x_message
        if previous_msg is not None:
            # If it already passed the ttl, don't bother trying to delete it.
            if previous_msg.created_at < datetime.datetime.now(
                    tz=datetime.timezone.utc) - datetime.timedelta(
                        seconds=X_MESSAGE_TTL_SECONDS):
                return
            await previous_msg.delete()

    @app_commands.command()
    @app_commands.describe(search='Look for a sound effect by name or tags.')
    @app_commands.autocomplete(search=_autocomplete_sound_effect_name)
    async def edit_sound(
        self,
        interaction: discord.Interaction,
        search: str,
    ):
        """Edit a sound effect."""
        sfx = self.catalog.by_name(search)
        if sfx is None:
            await interaction.response.send_message(
                f'I don\'t know a sound effect by the name of `{search}`.')
            return
        await interaction.response.send_message(embed=sfx.details_embed())

    @app_commands.command()
    async def sync_soundboard(self, interaction: discord.Interaction):
        """Redraw the soundboard channel."""
        if interaction.guild.id not in SOUNDBOARD_CHANNELS:
            await interaction.response.send_message(
                'This server does not have a soundboard channel configured.')
        soundboard_channel = await self.bot.fetch_channel(
            SOUNDBOARD_CHANNELS[interaction.guild.id])
        await interaction.response.defer()
        views = make_soundboard_views(self.catalog.all(), interaction.guild_id)

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
                'just to be safe I don\'t want to delete the history.')
            return

        # Similarly, if there are some messages sent by someone other than the
        # bot, we know it's something we didn't create so preserve it.
        for msg in messages:
            if msg.author.id != self.bot.user.id:
                await interaction.followup.send(
                    f'Someone else sent messages in {soundboard_channel}, '
                    'just to be safe I don\'t want to delete the history.')
                return

        for msg in messages:
            await msg.delete()

        for view in views:
            await soundboard_channel.send(view=view)

        await interaction.followup.send(
            f'Sent a fresh soundboard in {soundboard_channel}')

    @app_commands.command()
    async def history(self, interaction: discord.Interaction):
        """See the global sound effect history."""
        await interaction.response.defer()
        lines = []
        for dt, user_id, _, sfx in self.catalog.all_history()[0:20]:
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

    @app_commands.command()
    async def add_sound(self, interaction: discord.Interaction,
                        youtube_url: str, name: str, emoji: str):
        """Create a new sound effect.
        
        Args:
            youtube_url: The youtube video you want to make into a sound effect.
            name: Must be unique and under 12 char.
            emoji: Must be unique. Select using the emoji picker on the right.
        """
        for sfx in self.catalog.all():
            if sfx.name == name:
                await interaction.response.send_message(
                    f'Sound effect name must be unique. `{name}` is already a sound effect.'
                )
                return
            if sfx.emoji == emoji:
                await interaction.response.send_message(
                    f'Sound effect emoji must be unique. {emoji} is already a sound effect.'
                )
                return

        await interaction.response.defer()

        # TODO: prevent downloading if it's larger than a limit.
        file_path, duration_millis = await do_youtube_dl(
            youtube_url, self.bot.loop)

        partial_sfx_data = SoundEffectData(
            num=-1,
            name=name,
            emoji=emoji,
            yt_url=youtube_url,
            file_path=file_path,
            author=interaction.user.id,
            guild=interaction.guild.id,
            created_at=datetime.datetime.now(tz=datetime.timezone.utc),
            start_millis=0,
            end_millis=duration_millis,
            tags=f'{name},')

        creation_manager = SoundEffectCreationManager(
            partial_sfx_data=partial_sfx_data,
            original_interaction=interaction,
            voice_client_manager=self.voice_client_manager)
        await creation_manager.send_initial_message()
