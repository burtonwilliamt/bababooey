from typing import Callable, Awaitable

import discord

from bababooey import SoundEffectData, VoiceClientManager
from bababooey.ui import EditSoundEffectModal


class _PlaySoundEffectButton(discord.ui.Button):

    def __init__(self, sfx_data: SoundEffectData,
                 voice_client_manager: VoiceClientManager):
        super().__init__(style=discord.ButtonStyle.green,
                         label='Play',
                         emoji=chr(0x25b6) + chr(0xfe0f))
        self.sfx_data = sfx_data
        self.voice_client_manager = voice_client_manager

    async def callback(self, interaction: discord.Interaction):
        await self.voice_client_manager.play_file_for(
            user=interaction.user,
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


class SoundEffectDetailButtons(discord.ui.View):

    def __init__(self, sfx_data: SoundEffectData,
                 voice_client_manager: VoiceClientManager,
                 edit_callback: Callable[[], Awaitable[None]]):
        super().__init__()
        self.add_item(_PlaySoundEffectButton(sfx_data, voice_client_manager))
        self.add_item(_SoundEffectSauceButton(sfx_data))
        self.add_item(_EditSoundEffectButton(sfx_data, edit_callback))
