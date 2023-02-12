import discord

from bababooey import play_sfx, SoundEffect, millis_to_str
from bababooey.ui import EditSoundEffectModal


class _PlaySoundEffectButton(discord.ui.Button):

    def __init__(self, sfx: SoundEffect):
        super().__init__(style=discord.ButtonStyle.green,
                         label='Play',
                         emoji=chr(0x25b6) + chr(0xfe0f))
        self.sfx = sfx

    async def callback(self, interaction: discord.Interaction):
        assert self.view is not None
        await play_sfx(self.sfx, interaction.user)
        await interaction.response.edit_message(view=self.view)


class _SoundEffectSauceButton(discord.ui.Button):

    def __init__(self, sfx: SoundEffect):
        super().__init__(style=discord.ButtonStyle.link,
                         label='Sauce',
                         url=sfx.yt_url,
                         emoji=chr(0x1f517))


class _EditSoundEffectButton(discord.ui.Button):

    def __init__(self, sfx: SoundEffect):
        super().__init__(style=discord.ButtonStyle.grey,
                         label='Edit',
                         emoji=chr(0x270f) + chr(0xfe0f))
        self.sfx = sfx

    async def callback(self, interaction: discord.Interaction):
        assert self.view is not None
        await interaction.response.send_modal(
            EditSoundEffectModal(self.sfx, original_view=self.view))


class SoundEffectDetailButtons(discord.ui.View):

    def __init__(self, sfx: SoundEffect):
        super().__init__()
        self.add_item(_PlaySoundEffectButton(sfx))
        self.add_item(_SoundEffectSauceButton(sfx))
        self.add_item(_EditSoundEffectButton(sfx))


def sound_effect_detail_embed(sfx: SoundEffect) -> discord.Embed:
    description = ''
    description += f'Start: `{millis_to_str(sfx.start_time)}`\n'
    description += f'End: `{millis_to_str(sfx.end_time)}`\n'
    description += f'Original link: `{sfx.yt_url}`\n'
    return discord.Embed(
        title=f'{sfx.emoji} {sfx.name}',
        description=description)
