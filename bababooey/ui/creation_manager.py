import copy
from typing import Callable, Awaitable

import discord

from bababooey import millis_to_str, str_to_millis, SoundEffectData, play_file_for
from bababooey.ui import EditSoundEffectModal


class _PlaySoundEffectButton(discord.ui.Button):

    def __init__(self, sfx_data: SoundEffectData):
        super().__init__(style=discord.ButtonStyle.green,
                         label='Play',
                         emoji=chr(0x25b6) + chr(0xfe0f))
        self.sfx_data = sfx_data

    async def callback(self, interaction: discord.Interaction):
        await play_file_for(user=interaction.user,
                            file_path=self.sfx_data.file_path,
                            start_millis=self.sfx_data.start_millis,
                            end_millis=self.sfx_data.end_millis)
        await interaction.response.edit_message(view=self.view)


class _SoundEffectSauceButton(discord.ui.Button):

    def __init__(self, sfx_data: SoundEffectData):
        super().__init__(
            style=discord.ButtonStyle.link,
            label='Sauce',
            # TODO: Include the ?t=123 url argument for exact sound effect timestamp.
            url=sfx_data.yt_url,
            emoji=chr(0x1f517))


class _EditSoundEffectButton(discord.ui.Button):

    def __init__(self, sfx_data: SoundEffectData,
                 edit_callback: Callable[[], Awaitable[None]]):
        super().__init__(style=discord.ButtonStyle.grey,
                         label='Edit',
                         emoji=chr(0x270f) + chr(0xfe0f))
        self.sfx_data = sfx_data
        self.edit_callback = edit_callback

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(
            EditSoundEffectModal(self.sfx_data,
                                 original_view=self.view,
                                 edit_callback=self.edit_callback))


class SoundEffectCreationManager:

    def __init__(self, partial_sfx_data: SoundEffectData,
                 original_interaction: discord.Interaction):
        self.partial_sfx_data = partial_sfx_data
        self.original_interaction = original_interaction

    def create_embed(self, error: str | None = None) -> discord.Embed:
        e = discord.Embed(
            title=f'{self.partial_sfx_data.emoji} {self.partial_sfx_data.name}')
        e.add_field(
            name='Start',
            value=f'`{millis_to_str(self.partial_sfx_data.start_millis)}`',
            inline=True)
        e.add_field(
            name='End',
            value=f'`{millis_to_str(self.partial_sfx_data.end_millis)}`',
            inline=True)
        e.description = f'Tags:\n```\n{self.partial_sfx_data.tags if self.partial_sfx_data.tags != "" else "No Tags Provided."}\n```'
        if error is not None:
            e.description = f'```diff\n-{error}\n```' + e.description
        return e

    def create_view(self) -> discord.ui.View:
        view = discord.ui.View()
        view.add_item(_PlaySoundEffectButton(self.partial_sfx_data))
        view.add_item(_SoundEffectSauceButton(self.partial_sfx_data))
        view.add_item(
            _EditSoundEffectButton(self.partial_sfx_data, self.edit_callback))
        return view

    async def send_initial_message(self) -> None:
        await self.original_interaction.followup.send(embed=self.create_embed(),
                                                      view=self.create_view())

    async def edit_callback(self, name: str, start_str: str,
                            end_str: str | None, tags: str | None) -> None:
        # If we are successful, we'll assign temp_sfx_data to equal
        # new_sfx_data.
        new_sfx_data = copy.deepcopy(self.partial_sfx_data)
        new_sfx_data.name = name

        if start_str is None or start_str.lower() in ('', 'none'):
            new_sfx_data.start_millis = 0
        else:
            new_sfx_data.start_millis = str_to_millis(start_str)

        if end_str is None or end_str.lower() in ('', 'none'):
            new_sfx_data.end_millis = None
        else:
            new_sfx_data.end_millis = str_to_millis(end_str)

        new_sfx_data.tags = tags

        self.partial_sfx_data = new_sfx_data

        await self.original_interaction.edit_original_response(
            embed=self.create_embed(), view=self.create_view())
        await play_file_for(user=self.original_interaction.user,
                            file_path=self.partial_sfx_data.file_path,
                            start_millis=self.partial_sfx_data.start_millis,
                            end_millis=self.partial_sfx_data.end_millis)