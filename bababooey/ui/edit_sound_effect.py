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
            label='START TIME IN SECONDS (EG. 1.5)',
            placeholder='0.0',
            default=millis_to_str(sfx.start_time))
        self.end = discord.ui.TextInput(
            label='END TIME IN SECONDS (EG. 69.420)',
            placeholder='4:20.69',
            default=millis_to_str(sfx.end_time))
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
