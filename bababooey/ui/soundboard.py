from itertools import islice

import discord

from bababooey import SoundEffect


def _split_every(n, iterable):
    i = iter(iterable)
    piece = list(islice(i, n))
    while piece:
        yield piece
        piece = list(islice(i, n))


def _num_to_subscript(num: int) -> str:
    assert num >= 0
    if num == 0:
        return chr(0x2080)
    digits = []
    while num > 0:
        digits.insert(0, chr(0x2080 + (num % 10)))
        num = num // 10
    return ''.join(digits)


class _SimpleSoundEffectButton(discord.ui.Button):

    def __init__(self, sfx: SoundEffect, row: int):
        super().__init__(style=discord.ButtonStyle.grey,
                         label=sfx.name + ' ' + _num_to_subscript(sfx.num),
                         emoji=sfx.emoji,
                         row=row)
        self.sfx = sfx

    async def callback(self, interaction: discord.Interaction):
        assert self.view is not None
        await self.sfx.play_for(interaction.user)
        await interaction.response.edit_message(view=self.view)


def make_soundboard_views(sfx_list: list[SoundEffect]) -> list[discord.ui.View]:
    views = []
    for group in _split_every(20, sfx_list):
        view = discord.ui.View()
        views.append(view)
        for row in range(len(group) // 4):
            for sfx in islice(group, 4 * row, 4 * (row + 1)):
                view.add_item(_SimpleSoundEffectButton(sfx, row))
    return views
