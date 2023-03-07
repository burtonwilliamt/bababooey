import discord

from bababooey import SoundEffect


def num_to_subscript(num: int) -> str:
    assert num >= 0
    if num == 0:
        return chr(0x2080)
    digits = []
    while num > 0:
        digits.insert(0, chr(0x2080 + (num % 10)))
        num = num // 10
    return ''.join(digits)


class SoundEffectButton(discord.ui.Button):

    def __init__(self, sfx: SoundEffect, row: int, custom_id: str | None = None):
        super().__init__(style=discord.ButtonStyle.grey,
                         label=sfx.name, # + ' ' + num_to_subscript(sfx.num),
                         emoji=sfx.emoji,
                         row=row,
                         custom_id=custom_id)
        self.sfx = sfx

    async def callback(self, interaction: discord.Interaction):
        assert self.view is not None
        await self.sfx.play_for(interaction.user)
        await interaction.response.edit_message(view=self.view)


