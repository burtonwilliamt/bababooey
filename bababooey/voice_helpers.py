import asyncio
import datetime

import discord

# Amount of time to wait after connecting to voice before making noise.
CONNECTION_WAIT_TIME = 0.5
DISCONNECT_POLL_SECONDS = 10


def _find_correct_voice_channel(member: discord.Member) -> discord.VoiceChannel:
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

    # For whatever dumb reason, guild.voice_channels isn't populated
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


class VoiceClientManager:

    def __init__(self):
        # guild_id -> discord.VoiceClient
        self.clients: dict[int, discord.VoiceClient] = {}
        self.garbage_collection_task: asyncio.Task | None = None
        self._vc_connection_lock = asyncio.Lock()

    async def _maybe_garbage_collect_client(self, guild_id: int) -> None:
        """If necessary, disconnects and deletes a guild's voice client."""
        if guild_id not in self.clients:
            return
        voice_client = self.clients[guild_id]
        if not voice_client.is_connected():
            del self.clients[guild_id]
            return
        if voice_client.channel is None or all(
            [member.bot for member in voice_client.channel.members]):
            await voice_client.disconnect()
            del self.clients[guild_id]

    async def _garbage_collection_loop(self) -> None:
        while True:
            await asyncio.sleep(DISCONNECT_POLL_SECONDS)
            async with self._vc_connection_lock:
                for guild_id in self.clients:
                    await self._maybe_garbage_collect_client(guild_id)

    async def _ensure_voice(self,
                            member: discord.Member) -> discord.VoiceClient:
        async with self._vc_connection_lock:
            if self.garbage_collection_task is None:
                self.garbage_collection_task = asyncio.create_task(
                    self._garbage_collection_loop())
            guild = member.guild
            dest_channel = _find_correct_voice_channel(member)

            # If we're already connected somewhere, re-use that voice_client.
            if guild.voice_client is not None and guild.voice_client.is_connected(
            ):
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
                self.clients[guild.id] = voice_client
                await asyncio.sleep(CONNECTION_WAIT_TIME)
                return voice_client

    async def play_file_for(self, user: discord.Member, file_path: str,
                            start_millis: int, end_millis: int | None) -> None:
        voice_client = await self._ensure_voice(user)

        ffmpeg_options = ''
        if start_millis is not None and start_millis > 0:
            ffmpeg_options += ' -ss {}'.format(
                datetime.timedelta(milliseconds=start_millis))

        if end_millis is not None:
            # Note: ffmpeg doesn't do end_time, instead it uses duration, time after start.
            if start_millis is not None:
                ffmpeg_options += ' -t {}'.format(
                    datetime.timedelta(milliseconds=end_millis - start_millis))
            else:
                ffmpeg_options += ' -t {}'.format(
                    datetime.timedelta(milliseconds=end_millis))

        # Use FFmpegOpusAudio instead of FFmpegPCMAudio
        # This is in case the file we are loading is already opus encoded, preventing double-encoding
        # Consider trying to store audio files in Opus format to decrease load

        # Use before_options to seek to start_time and not read beyond duration
        # if we instead just use options, it will process the whole file but
        # drop the unecessary audio on output
        track = discord.FFmpegOpusAudio(file_path,
                                        before_options=ffmpeg_options,
                                        options='-filter:a loudnorm')

        if voice_client.is_playing():
            voice_client.stop()

        voice_client.play(track)
