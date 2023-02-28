import discord

from bababooey import SoundEffectData, UserSoundEffectHistory, millis_to_str, VoiceClientManager


class SoundEffect:

    def __init__(self, raw: SoundEffectData, history: UserSoundEffectHistory,
                 voice_client_manager: VoiceClientManager):
        self._voice_client_manager = voice_client_manager
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
        await self._voice_client_manager.play_file_for(user,
                                                       self._raw.file_path,
                                                       self._raw.start_millis,
                                                       self._raw.end_millis)
        self._history.record_usage(user, self.num)

    def details_embed(self) -> discord.Embed:
        description = ''
        description += f'Start: `{millis_to_str(self.start_millis)}`\n'
        description += f'End: `{millis_to_str(self.end_millis)}`\n'
        description += f'Original link: `{self.yt_url}`\n'
        description += f'Creator: `{self._raw.author}`\n'
        description += f'Created: `{self._raw.created_at}`\n'
        return discord.Embed(title=f'{self.emoji} {self.name}',
                             description=description)
