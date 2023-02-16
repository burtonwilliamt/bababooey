from collections.abc import Sequence
import itertools

import discord

from bababooey import SoundEffect
from bababooey.ui import SoundEffectButton


def _split_every(group_size: int,
                 sfx_list: Sequence[SoundEffect]) -> list[list[SoundEffect]]:
    return [
        list(group) for _, group in itertools.groupby(
            sfx_list, lambda sfx: sfx.num // group_size)
    ]


def make_soundboard_views(
        sfx_list: Sequence[SoundEffect]) -> Sequence[discord.ui.View]:
    views = []
    for group in _split_every(20, sfx_list):
        view = discord.ui.View()
        views.append(view)
        for row, sfx_in_row in enumerate(_split_every(4, group)):
            for sfx in sfx_in_row:
                view.add_item(SoundEffectButton(sfx, row))
    return views
