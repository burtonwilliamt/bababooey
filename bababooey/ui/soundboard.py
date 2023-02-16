from itertools import islice

import discord

from bababooey import SoundEffect
from bababooey.ui import SoundEffectButton


def _split_every(n, iterable):
    i = iter(iterable)
    piece = list(islice(i, n))
    while piece:
        yield piece
        piece = list(islice(i, n))


def make_soundboard_views(sfx_list: list[SoundEffect]) -> list[discord.ui.View]:
    views = []
    for group in _split_every(20, sfx_list):
        view = discord.ui.View()
        views.append(view)
        for row in range(len(group) // 4):
            for sfx in islice(group, 4 * row, 4 * (row + 1)):
                view.add_item(SoundEffectButton(sfx, row))
    return views
