import discord

from bababooey import SoundEffect, millis_to_str


class EditSoundEffectModal(discord.ui.Modal):

    def __init__(self, sfx: SoundEffect, original_view: discord.ui.View):
        super().__init__(title=f'Editing {sfx.name}.')
        self.sfx = sfx
        self.original_view = original_view
        self.name = discord.ui.TextInput(label='Name',
                                         placeholder='Bababooey',
                                         max_length=12,
                                         default=sfx.name)
        self.start = discord.ui.TextInput(
            label='Start Time',
            placeholder='00:00.0000',
            default=millis_to_str(sfx.start_millis))
        self.end = discord.ui.TextInput(
            label='End Time (use none to play until the end)',
            placeholder='None',
            default=millis_to_str(sfx.end_millis))
        self.tags = discord.ui.TextInput(
            label='TAGS TO HELP SEARCH FOR THIS SOUND',
            style=discord.TextStyle.paragraph,
            placeholder='card, now, lets, see, paul, allen, american, psycho')
        self.add_item(self.name)
        self.add_item(self.start)
        self.add_item(self.end)
        self.add_item(self.tags)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.edit_message(view=self.original_view)
