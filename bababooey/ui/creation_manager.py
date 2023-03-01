import asyncio
import copy
import logging
import os
import pathlib
import subprocess
from typing import Callable, Awaitable

import discord

from bababooey import millis_to_str, str_to_millis, SoundEffectData, VoiceClientManager, Catalog
from bababooey.ui import EditSoundEffectModal

MAX_SOUND_EFFECT_NAME_LENGTH = 12
MIN_SOUND_EFFECT_NAME_LENGTH = 1

_log = logging.getLogger(__name__)


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


class _SaveConfirmationModal(discord.ui.Modal):

    def __init__(self, confirm_callback: Callable[[discord.Interaction],
                                                  Awaitable[None]]):
        super().__init__(title='Save the sound effect?')
        self.confirm_callback = confirm_callback
        message = (
            'Make sure you\'re happy with the sound effect before you save it. '
            'It\'s a lot of work to edit it.')
        # TODO: this should allow the user to add some last minute tags.
        self.add_item(
            discord.ui.TextInput(
                label='Warning',
                style=discord.TextStyle.paragraph,
                placeholder=message,
                default=message,
            ))

    async def on_submit(self, interaction: discord.Interaction) -> None:
        await self.confirm_callback(interaction)


class _SaveSoundEffectButton(discord.ui.Button):

    def __init__(self, save_callback: Callable[[discord.Interaction],
                                               Awaitable[None]]):
        super().__init__(style=discord.ButtonStyle.grey,
                         label='Save',
                         emoji=chr(0x1f4be))
        self.save_callback = save_callback

    async def callback(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_modal(
            _SaveConfirmationModal(confirm_callback=self.save_callback))


class SoundEffectCreationManager:

    def __init__(self, *, partial_sfx_data: SoundEffectData,
                 original_interaction: discord.Interaction,
                 voice_client_manager: VoiceClientManager, catalog: Catalog):
        self.partial_sfx_data = partial_sfx_data
        self.duration = self.partial_sfx_data.end_millis
        self.original_interaction = original_interaction
        self.voice_client_manager = voice_client_manager
        self.catalog = catalog

    def create_embed(self,
                     use_attached_image: bool,
                     error: str | None = None) -> discord.Embed:
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
        e.description = (
            f'Sauce:\n[`{self.partial_sfx_data.yt_url}`]'
            f'({self.partial_sfx_data.yt_url})\n'
            f'Tags:\n```\n{self.partial_sfx_data.tags if self.partial_sfx_data.tags != "" else "No Tags Provided."}\n```'
        )
        if use_attached_image:
            e.set_image(url='attachment://image.png')
        if error is not None:
            e.description = ('```diff\n-ERROR\n-' +
                             '\n-'.join(error.splitlines()) + '\n```' +
                             e.description)
        return e

    def create_view(self) -> discord.ui.View:
        view = discord.ui.View(timeout=None)
        view.add_item(
            _PlaySoundEffectButton(self.partial_sfx_data,
                                   self.voice_client_manager))
        view.add_item(
            _EditSoundEffectButton(self.partial_sfx_data, self.edit_callback))
        view.add_item(_SaveSoundEffectButton(self.save_sound_effect))
        return view

    async def save_sound_effect(self, interaction: discord.Interaction) -> None:
        try:
            sfx = self.catalog.create_new_sfx(self.partial_sfx_data)
        except ValueError as e:
            context = ''
            if e.args:
                context = e.args[0]
            # TODO: be smarter and don't double edit on errors.
            await interaction.response.edit_message(view=self.create_view())
            await self.edit_original_response(
                error=f'Failed to create sound effect!\n{context}')
            return
        await interaction.response.edit_message(embed=discord.Embed(
            title='Success!',
            description=f'Successfully created {sfx.emoji} {sfx.name}. '
            'Go checkout the soundboard channel (or redraw it using /sync_soundboard)',
        ),
                                                attachments=[],
                                                view=None)

    async def generate_waveform(self) -> discord.File | None:
        os.makedirs('data/tmp/', exist_ok=True)
        image_path = 'data/tmp/' + pathlib.Path(
            self.partial_sfx_data.file_path).stem + '.png'
        command = f'yes | ffmpeg -i {self.partial_sfx_data.file_path} -filter_complex "compand, showwavespic=colors=#5865F2|#5865F2:split_channels=1, drawbox=x=iw*{self.partial_sfx_data.start_millis/self.duration}:y=0:w=iw*{(self.partial_sfx_data.end_millis-self.partial_sfx_data.start_millis)/self.duration}:h=ih:t=fill:color=#57f287" -frames:v 1 {image_path}'
        proc = await asyncio.create_subprocess_shell(command,
                                                     stderr=subprocess.PIPE,
                                                     stdout=subprocess.PIPE)
        # TODO: detect if this command fails and handle correctly.
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            _log.error('FFMPEG failed. Here is the stderr: %s', stderr.decode())
            return None
        return discord.File(image_path, filename='image.png')

    async def send_initial_message(self) -> None:
        waveform = await self.generate_waveform()
        if waveform is None:
            await self.original_interaction.followup.send(
                embed=self.create_embed(use_attached_image=False),
                view=self.create_view())
        else:
            await self.original_interaction.followup.send(
                embed=self.create_embed(use_attached_image=True),
                view=self.create_view(),
                file=waveform)

    def sanitize_input(self, name: str, start_str: str, end_str: str | None,
                       tags: str | None) -> SoundEffectData | str:
        """Returns updated sound effect data, or an error string."""
        errors = ''
        new_sfx_data = copy.deepcopy(self.partial_sfx_data)
        if len(name) > MAX_SOUND_EFFECT_NAME_LENGTH:
            errors += f'Name cannot exceed {MAX_SOUND_EFFECT_NAME_LENGTH} characters long, but "{name}" is {len(name)} characters long.\n'
        elif len(name) < MIN_SOUND_EFFECT_NAME_LENGTH:
            errors += f'Name must be at least {MIN_SOUND_EFFECT_NAME_LENGTH} characters long, but "{name}" is {len(name)} characters long.\n'
        if self.catalog.by_name(name) is not None:
            errors += f'Name must be unique, but another sound effect already has the name "{name}".\n'

        new_sfx_data.name = name

        if start_str is None or start_str.lower() in ('', 'none'):
            new_sfx_data.start_millis = 0
        else:
            try:
                new_sfx_data.start_millis = str_to_millis(start_str)
            except ValueError:
                errors += f'The start time "{start_str}" doesn\'t parse. Try seconds (6.2) or minutes (1:20.1) or the full format (00:00.000).\n'

        if end_str is None or end_str.lower() in ('', 'none'):
            new_sfx_data.end_millis = self.duration
        else:
            try:
                new_sfx_data.end_millis = str_to_millis(end_str)
            except ValueError:
                errors += f'The end time "{end_str}" doesn\'t parse. Try seconds (6.2) or minutes (1:20.1) or the full format (00:00.000).\n'

        new_sfx_data.tags = tags

        if errors == '':
            return new_sfx_data
        else:
            return errors

    async def edit_original_response(self, error: str = None) -> None:
        waveform = await self.generate_waveform()
        if waveform is None:
            attachments = []
        else:
            attachments = [waveform]

        embed = self.create_embed(use_attached_image=waveform is not None,
                                  error=error)
        await self.original_interaction.edit_original_response(
            embed=embed, view=self.create_view(), attachments=attachments)

    async def edit_callback(self, name: str, start_str: str,
                            end_str: str | None, tags: str | None) -> None:
        # If we are successful, we'll assign temp_sfx_data to equal
        # new_sfx_data.

        res = self.sanitize_input(name, start_str, end_str, tags)
        # If the sanitization failed, edit the message to show the error.
        if isinstance(res, str):
            await self.edit_original_response(error=res)
        elif isinstance(res, SoundEffectData):
            self.partial_sfx_data = res
            await self.edit_original_response()
            await self.voice_client_manager.play_file_for(
                user=self.original_interaction.user,
                file_path=self.partial_sfx_data.file_path,
                start_millis=self.partial_sfx_data.start_millis,
                end_millis=self.partial_sfx_data.end_millis)
        else:
            raise RuntimeError(
                'Unexpected type received from self.sanatize_input()')
