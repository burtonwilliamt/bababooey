import asyncio

import discord

from bababooey import SoundEffectData, UserSoundEffectHistory, millis_to_str, VoiceClientManager


class NextPlayerEvent:
    def __init__(self):
        self.someone_played = asyncio.Event()
        self.the_caller: discord.Member = None


class SoundEffect:

    def __init__(self, raw: SoundEffectData, history: UserSoundEffectHistory,
                 voice_client_manager: VoiceClientManager):
        self._voice_client_manager = voice_client_manager
        self._raw = raw
        self._history = history
        self._waiters: list[NextPlayerEvent] = []

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

    async def play_for_partial(self, user: discord.Member, start_millis: int, end_millis: int):
        await self._voice_client_manager.play_file_for(user,
                                                       self._raw.file_path,
                                                       start_millis,
                                                       end_millis)

    async def play_for(self, user: discord.Member):
        for event in self._waiters:
            event.the_caller = user
            event.someone_played.set()
        self._waiters.clear()

        await self._voice_client_manager.play_file_for(user,
                                                       self._raw.file_path,
                                                       self._raw.start_millis,
                                                       self._raw.end_millis)
        self._history.record_usage(user, self.num)

    async def next_player(self) -> discord.Member:
        event = NextPlayerEvent()
        self._waiters.append(event)
        await event.someone_played.wait()
        return event.the_caller

    def details_embed(self) -> discord.Embed:
        description = ''
        description += f'Start: `{millis_to_str(self.start_millis)}`\n'
        description += f'End: `{millis_to_str(self.end_millis)}`\n'
        description += f'Original link: `{self.yt_url}`\n'
        description += f'Creator: `{self._raw.author}`\n'
        description += f'Created: `{self._raw.created_at}`\n'
        return discord.Embed(title=f'{self.emoji} {self.name}',
                             description=description)
