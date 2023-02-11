from itertools import islice
import shelve

import asyncio
import datetime

import discord
from discord import app_commands

from bababooey import BababooeyBot, SoundEffect

_vc_connection_lock = asyncio.Lock()

# Amount of time to wait after connecting to voice before making noise.
CONNECTION_WAIT_TIME = 0.5


def split_every(n, iterable):
    i = iter(iterable)
    piece = list(islice(i, n))
    while piece:
        yield piece
        piece = list(islice(i, n))


def find_correct_voice_channel(member: discord.Member) -> discord.VoiceChannel:
    """Find the most fitting voice channel to connect to.

    IF calling member is connected:
        Go there
    ELIF already connected:
        Stay where you are
    ELIF People are connected:
        Find the voice channel with the most people
    ELSE:
        Connect to the top channel

    If the bot doesn't have permission for one channel, it moves on to the
    next most preferred channel.

    Args:
        member (discord.Member): Who requested this sound effect.
    """
    voice_channels_by_preference = []
    if member.voice is not None and member.voice.channel is not None:
        voice_channels_by_preference.append(member.voice.channel)

    guild = member.guild
    if guild.voice_client is not None \
            and guild.voice_client.is_connected():
        voice_channels_by_preference.append(guild.voice_client.channel)

    # For whatever dumb reason, sfx_guild.voice_channels isn't populated
    #   sometimes, so we have to force a fetch of the channels. Then that
    #   doesn't even update the guild.voice_channels cache so we have to
    #   filter the results for voice channels manually
    voice_channels = list(guild.voice_channels)
    voice_channels.sort(key=lambda vc: len(vc.members))
    for vc in voice_channels:
        voice_channels_by_preference.append(vc)

    if len(voice_channels_by_preference) == 0:
        raise ValueError(
            'I can\'t actually see any voice channels to connect to.')

    for vc in voice_channels_by_preference:
        permissions = vc.permissions_for(guild.me)
        if permissions.connect and permissions.speak:
            return vc

    raise ValueError('The SFX bot needs the `CONNECT` and `SPEAK` permissions.')


async def ensure_voice(member: discord.Member) -> discord.VoiceClient:
    guild = member.guild

    if _vc_connection_lock.locked():
        return
    async with _vc_connection_lock:
        dest_channel = find_correct_voice_channel(member)

        # If we're already connected somewhere, re-use that voice_client.
        if guild.voice_client is not None and guild.voice_client.is_connected():
            voice_client = guild.voice_client

            # If we're already in the correct voice_channel just return that.
            if voice_client.channel.id == dest_channel.id:
                return voice_client
            await voice_client.move_to(dest_channel)
            await asyncio.sleep(CONNECTION_WAIT_TIME)
            return voice_client
        else:
            # Not yet connected anywhere.
            voice_client = await dest_channel.connect()
            await asyncio.sleep(CONNECTION_WAIT_TIME)
            return voice_client


async def play_sfx(voice_client: discord.VoiceClient, sfx: SoundEffect):
    ffmpeg_options = ''
    if sfx.start_time is not None:
        ffmpeg_options += ' -ss {}'.format(
            datetime.timedelta(milliseconds=sfx.start_time))

    if sfx.end_time is not None:
        # Note: ffmpeg doesn't do end_time, instead it uses duration, time after start.
        if sfx.start_time is not None:
            ffmpeg_options += ' -t {}'.format(
                datetime.timedelta(milliseconds=sfx.end_time - sfx.start_time))
        else:
            ffmpeg_options += ' -t {}'.format(
                datetime.timedelta(milliseconds=sfx.end_time))

    # Use FFmpegOpusAudio instead of FFmpegPCMAudio
    # This is in case the file we are loading is already opus encoded, preventing double-encoding
    # Consider trying to store audio files in Opus format to decrease load

    # Use before_options to seek to start_time and not read beyond duration
    # if we instead just use options, it will process the whole file but
    # drop the unecessary audio on output
    track = discord.FFmpegOpusAudio(sfx.local_path,
                                    before_options=ffmpeg_options,
                                    options='-filter:a loudnorm')

    if voice_client.is_playing():
        voice_client.stop()

    voice_client.play(track)
    # TODO: handle disconnect after everyone leaves.
    # await dc_bomb.burn_for_at_least(60)  # stay connected for 60 seconds


def read_copied_sfx() -> list[SoundEffect]:
    s = shelve.open('data/copied_sfx')
    effects = s['sfx']
    s.close()
    return effects


def sort_sound_effect_name_matches(partial: str, sfx_name: str) -> int:
    """Returns a lower value for closer matches."""
    exact = sfx_name.find(partial)
    if exact != -1:
        return exact

    ignored_case = sfx_name.lower().find(partial.lower())
    if ignored_case == -1:
        return -1
    return ignored_case + 0.5


def strip_leading_emoji(sound_effect_name: str) -> str:
    if ' ' not in sound_effect_name:
        return sound_effect_name
    return sound_effect_name.split(' ', 1)[0]


class SoundEffectButton(discord.ui.Button):

    def __init__(self, sfx: SoundEffect, row: int = None):
        super().__init__(style=discord.ButtonStyle.grey,
                         label=sfx.name,
                         emoji=sfx.emoji,
                         row=row)
        self.sfx = sfx

    async def callback(self, interaction: discord.Interaction):
        assert self.view is not None
        voice_client = await ensure_voice(interaction.user)
        await play_sfx(voice_client, self.sfx)
        await interaction.response.edit_message(view=self.view)


def make_sound_pallets(sfx_list: list[SoundEffect]) -> list[discord.ui.View]:
    views = []
    for group in split_every(20, sfx_list):
        view = discord.ui.View()
        views.append(view)
        for row in range(len(group) // 4):
            for sfx in islice(group, 4 * row, 4 * (row + 1)):
                view.add_item(SoundEffectButton(sfx, row))
    return views


def add_sound_effect_commands(bot: BababooeyBot):

    sfx_cache = {sfx.name: sfx for sfx in read_copied_sfx()}

    async def autocomplete_sound_effect_name(
            interaction: discord.Interaction,
            partial_sound: str) -> list[app_commands.Choice[str]]:
        partial_sound_lower = partial_sound.lower()
        res = []
        for name, sfx in sfx_cache.items():
            if partial_sound_lower in name.lower():
                res.append(sfx)

        res.sort(key=lambda sfx: sort_sound_effect_name_matches(
            partial_sound, sfx.name))
        return [
            app_commands.Choice(name=sfx.emoji + ' ' + sfx.name, value=sfx.name)
            for sfx in res[0:25]
        ]

    @bot.tree.command()
    @app_commands.autocomplete(sound_effect_name=autocomplete_sound_effect_name)
    async def sound(interaction: discord.Interaction, sound_effect_name: str):
        if sound_effect_name not in sfx_cache:
            # Sometimes the leading emoji comes through sometimes it doesn't.
            sound_effect_name = strip_leading_emoji(sound_effect_name)
            # If it's still not a valid name.
            if sound_effect_name not in sfx_cache:
                await interaction.response.send_message(
                    f'I don\'t know a sound effect by the name of `{sound_effect_name}`.'
                )
                return
        the_sfx = sfx_cache[sound_effect_name]
        voice_client = await ensure_voice(interaction.user)
        await play_sfx(voice_client, the_sfx)
        view = discord.ui.View()
        view.add_item(SoundEffectButton(sfx=the_sfx))
        view.add_item(
            discord.ui.Button(style=discord.ButtonStyle.link,
                              label='sauce',
                              url=the_sfx.yt_url,
                              emoji=chr(0x1f517)))
        await interaction.response.send_message(view=view)

    @bot.tree.command()
    async def soundboard(interaction: discord.Interaction):
        views = make_sound_pallets(list(sfx_cache.values()))
        first_view = views.pop(0)
        # Respond to the interaciton with the first pallet.
        await interaction.response.send_message(view=first_view)

        # Send the rest of the pallets.
        for view in views:
            await interaction.channel.send(view=view)
