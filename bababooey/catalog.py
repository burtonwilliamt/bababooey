"""Catalog provides an interface to the list of all sound effects.

This module and the corresponding class represents the disk storage of
SoundEffect objects.
"""
from collections.abc import Sequence
import datetime
import shelve

import discord

from bababooey import UserSoundEffectHistory, SoundEffect, VoiceClientManager


def _score_sound_effect_name_matches(partial: str, sfx_name: str) -> int:
    """Returns a lower value for closer matches."""
    exact = sfx_name.find(partial)
    if exact != -1:
        return exact

    ignored_case = sfx_name.lower().find(partial.lower())
    if ignored_case == -1:
        return -1
    return ignored_case + 0.5


def _strip_leading_emoji(sound_effect_name: str) -> str:
    if ' ' not in sound_effect_name:
        return sound_effect_name
    return sound_effect_name.split(' ', 1)[0]


class Catalog:
    """Storage and lookup container for SoundEffect objects."""

    def __init__(self, voice_client_manager: VoiceClientManager):
        self._voice_client_manager = voice_client_manager
        self._history = UserSoundEffectHistory()
        self._all = self._read_sfx_data()
        self._by_name = {sfx.name: sfx for sfx in self._all}
        self._by_num = {sfx.num: sfx for sfx in self._all}

    def all(self) -> Sequence[SoundEffect]:
        return list(self._all)

    def _read_sfx_data(self) -> list[SoundEffect]:
        s = shelve.open('data/sfx_data')
        effects = [SoundEffect(raw, self._history, self._voice_client_manager) for raw in s['data']]
        s.close()
        return effects

    def find_partial_matches(self,
                             partial_sound_name: str) -> Sequence[SoundEffect]:
        """Return all matches to a partial sound effect name."""
        partial_sound_lower = partial_sound_name.lower()
        res = []
        for sfx in self._all:
            if partial_sound_lower in sfx.name.lower():
                res.append(sfx)

        res.sort(key=lambda sfx: _score_sound_effect_name_matches(
            partial_sound_name, sfx.name))
        return res

    def by_name(self, name: str) -> SoundEffect | None:
        """Returns the exact match sound effect, or None.
        
        Optionally, the sound effect may be prefixed with its emoji.
        """
        if name not in self._by_name:
            # Maybe the reason it isn't present is a prefixed leading emoji.
            # TODO make sure the emoji that was stripped matches the sfx we
            # eventually find.
            name = _strip_leading_emoji(name)
        return self._by_name.get(name, None)

    def by_num(self, num: int) -> SoundEffect | None:
        return self._by_num.get(num, None)

    def users_most_recent(self, user: discord.Member,
                          limit: int) -> Sequence[SoundEffect]:
        """Returns user's recent sound effects in order of recency."""
        return [
            self.by_num(sfx_num)
            for sfx_num in self._history.users_most_recent(user, limit)
        ]

    def all_history(
            self) -> Sequence[tuple[datetime.datetime, int, int, SoundEffect]]:
        """Returns sequence of (datetime, user_id, guild_id, SoundEffect)."""
        return [(dt, user_id, guild_id, self.by_num(sfx_num)) for dt, user_id,
                guild_id, sfx_num in self._history.fetch_all_history()]

    def create(self, name: str, emoji: str, youtube_url: str, file_path: str,
               author: discord.Member) -> SoundEffect:
        pass
