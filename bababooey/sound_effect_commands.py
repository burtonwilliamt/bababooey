import shelve

import asyncio
import datetime

import discord
from discord import app_commands

from bababooey import BababooeyBot, SoundEffect

_vc_connection_lock = asyncio.Lock()

# Amount of time to wait after connecting to voice before making noise.
CONNECTION_WAIT_TIME = 0.5


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
            app_commands.Choice(name=sfx.name, value=sfx.name)
            for sfx in res[0:25]
        ]

    @bot.tree.command()
    @app_commands.autocomplete(sound_effect_name=autocomplete_sound_effect_name)
    async def sound(interaction: discord.Interaction, sound_effect_name: str):
        if sound_effect_name not in sfx_cache:
            await interaction.response.send_message(
                'I don\'t know a sound effect by that name.')
            return
        voice_client = await ensure_voice(interaction.user)
        await play_sfx(voice_client, sfx_cache[sound_effect_name])
        await interaction.response.send_message(
            f'Played {sound_effect_name} in {voice_client.channel.name}',
            ephemeral=True)
