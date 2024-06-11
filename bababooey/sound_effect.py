import asyncio
import re
from urllib.parse import parse_qs, urlencode, urlparse

import discord

from bababooey import (
    SoundEffectData,
    UserSoundEffectHistory,
    VoiceClientManager,
    millis_to_str,
)


class NextPlayerEvent:
    def __init__(self):
        self.someone_played = asyncio.Event()
        self.the_caller: discord.Member = None


class SoundEffect:

    def __init__(
        self,
        raw: SoundEffectData,
        history: UserSoundEffectHistory,
        voice_client_manager: VoiceClientManager,
    ):
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

    def youtube_id(self) -> str | None:
        parsed_url = urlparse(self._raw.yt_url)
        captured_params = parse_qs(parsed_url.query)
        if (
            "v" in captured_params
            and isinstance(captured_params["v"], list)
            and len(captured_params["v"]) == 1
        ):
            return captured_params["v"][0]
        m = re.match(r"(https?://)(www\.)?youtu\.be/([a-zA-Z0-9\-_]{11}).*", self._raw.yt_url)
        if m:
            return m.groups()[2]
        return None

    @property
    def clean_yt_url(self) -> str:
        yt_id = self.youtube_id()
        if yt_id is not None:
            return "https://www.youtube.com/watch?" + urlencode(
                {"v": yt_id, "t": str(int(self.start_millis // 1000))}
            )
        else:
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

    async def play_for_partial(
        self, user: discord.Member, start_millis: int, end_millis: int
    ):
        await self._voice_client_manager.play_file_for(
            user, self._raw.file_path, start_millis, end_millis
        )

    async def play_for(self, user: discord.Member):
        for event in self._waiters:
            event.the_caller = user
            event.someone_played.set()
        self._waiters.clear()

        await self._voice_client_manager.play_file_for(
            user, self._raw.file_path, self._raw.start_millis, self._raw.end_millis
        )
        self._history.record_usage(user, self.num)

    async def next_player(self) -> discord.Member:
        event = NextPlayerEvent()
        self._waiters.append(event)
        await event.someone_played.wait()
        return event.the_caller

    async def details_embed(self, guild: discord.Guild) -> discord.Embed:
        author = await guild.fetch_member(self._raw.author)

        e = discord.Embed(title=f"{self.emoji} {self.name}")
        e.add_field(name="Start", value=f'`{millis_to_str(self.start_millis)}`')
        e.add_field(name="End", value=f'`{millis_to_str(self.end_millis)}`')
        e.add_field(name="Original link", value=f'`{self.yt_url}`')
        e.add_field(name="Created", value=f"`{self._raw.created_at.strftime("%Y-%m-%dT%H:%M:%S")}` (<t:{int(self._raw.created_at.timestamp())}:R>)\n")
        if author:
            e.set_footer(text=author.nick, icon_url=author.avatar.url)
        else:
            e.add_field(name="Creator", value=self._raw.author)
        return e
