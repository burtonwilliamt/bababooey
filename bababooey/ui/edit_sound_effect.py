from typing import Callable, Awaitable
import discord

from bababooey import SoundEffectData, millis_to_str


class EditSoundEffectModal(discord.ui.Modal):

    def __init__(self, sfx: SoundEffectData, original_view: discord.ui.View,
                 edit_callback: Callable[[str, str, str, str], Awaitable[None]]):
        super().__init__(title=f'Editing {sfx.name}.')
        self.sfx = sfx
        self.original_view = original_view
        self.edit_callback = edit_callback
        self.name = discord.ui.TextInput(label='Name',
                                         placeholder='Bababooey',
                                         max_length=12,
                                         min_length=1,
                                         default=sfx.name)
        self.start = discord.ui.TextInput(label='Start Time',
                                          placeholder='00:00.000',
                                          max_length=len('00:00.000'),
                                          default=millis_to_str(
                                              sfx.start_millis),
                                          required=False)
        self.end = discord.ui.TextInput(
            label='End Time (use none to play until the end)',
            placeholder='None',
            max_length=len('00:00.000'),
            default=millis_to_str(sfx.end_millis),
            required=False)
        self.tags = discord.ui.TextInput(
            label='TAGS TO HELP SEARCH FOR THIS SOUND',
            style=discord.TextStyle.paragraph,
            placeholder='card, now, lets, see, paul, allen, american, psycho',
            default=sfx.tags,
            required=False)
        self.add_item(self.name)
        self.add_item(self.start)
        self.add_item(self.end)
        self.add_item(self.tags)

    async def on_submit(self, interaction: discord.Interaction):
        # First response to the interaction so we don't need to worry about it.
        await interaction.response.edit_message(view=self.original_view)
        await self.edit_callback(name=self.name.value,
                                 start_str=self.start.value,
                                 end_str=self.end.value,
                                 tags=self.tags.value)
