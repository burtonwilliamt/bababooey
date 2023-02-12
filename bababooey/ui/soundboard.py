from itertools import islice

import discord

from bababooey import SoundEffect, play_sfx

def _split_every(n, iterable):
    i = iter(iterable)
    piece = list(islice(i, n))
    while piece:
        yield piece
        piece = list(islice(i, n))


class _SimpleSoundEffectButton(discord.ui.Button):

    def __init__(self, sfx: SoundEffect, row: int):
        super().__init__(style=discord.ButtonStyle.grey,
                         label=sfx.name,
                         emoji=sfx.emoji,
                         row=row)
        self.sfx = sfx

    async def callback(self, interaction: discord.Interaction):
        assert self.view is not None
        await play_sfx(self.sfx, interaction.user)
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

