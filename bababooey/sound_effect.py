import datetime

import discord

from bababooey import SoundEffectData, UserSoundEffectHistory, ensure_voice, millis_to_str


class SoundEffect:

    def __init__(self, raw: SoundEffectData, history: UserSoundEffectHistory):
        self._raw = raw
        self._history = history

    @property
    def name(self) -> str:
        return self._raw.name

    @property
    def emoji(self) -> str:
        return self._raw.emoji

    @property
    def yt_url(self) -> str:
        return self._raw.yt_url

    @property
    def start_millis(self) -> int:
        return self._raw.start_millis

    @property
    def end_millis(self) -> int:
        return self._raw.end_millis

    @property
    def num(self) -> int:
        return self._raw.num
    
    @property
    def tags(self) -> str:
        return self._raw.tags

    async def play_for(self, user: discord.Member):
        voice_client = await ensure_voice(user)

        ffmpeg_options = ''
        if self._raw.start_millis is not None and self._raw.start_millis > 0:
            ffmpeg_options += ' -ss {}'.format(
                datetime.timedelta(milliseconds=self._raw.start_millis))

        if self._raw.end_millis is not None:
            # Note: ffmpeg doesn't do end_time, instead it uses duration, time after start.
            if self._raw.start_millis is not None:
                ffmpeg_options += ' -t {}'.format(
                    datetime.timedelta(milliseconds=self._raw.end_millis -
                                       self._raw.start_millis))
            else:
                ffmpeg_options += ' -t {}'.format(
                    datetime.timedelta(milliseconds=self._raw.end_millis))

        # Use FFmpegOpusAudio instead of FFmpegPCMAudio
        # This is in case the file we are loading is already opus encoded, preventing double-encoding
        # Consider trying to store audio files in Opus format to decrease load

        # Use before_options to seek to start_time and not read beyond duration
        # if we instead just use options, it will process the whole file but
        # drop the unecessary audio on output
        track = discord.FFmpegOpusAudio(self._raw.file_path,
                                        before_options=ffmpeg_options,
                                        options='-filter:a loudnorm')

        if voice_client.is_playing():
            voice_client.stop()

        voice_client.play(track)
        self._history.record_usage(user, self.num)
        # TODO: handle disconnect after everyone leaves.
        # await dc_bomb.burn_for_at_least(60)  # stay connected for 60 seconds

    def details_embed(self) -> discord.Embed:
        description = ''
        description += f'Start: `{millis_to_str(self.start_millis)}`\n'
        description += f'End: `{millis_to_str(self.end_millis)}`\n'
        description += f'Original link: `{self.yt_url}`\n'
        description += f'Creator: `{self._raw.author}`\n'
        description += f'Created: `{self._raw.created_at}`\n'
        return discord.Embed(title=f'{self.emoji} {self.name}',
                             description=description)
