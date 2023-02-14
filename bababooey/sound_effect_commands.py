import re
import shelve

import discord
from discord import app_commands

from bababooey import BababooeyBot, SoundEffect
from bababooey.ui import make_soundboard_views, SoundEffectDetailButtons

CUSTOM_EMOJI_RE = re.compile(r'<:.+:\d+>')


def _read_sfx_data() -> list[SoundEffect]:
    s = shelve.open('data/sfx_data')
    effects = [SoundEffect(raw) for raw in s['data']]
    s.close()
    return effects


def _unicode_safe_emoji(discord_emoji: str) -> str:
    if CUSTOM_EMOJI_RE.match(discord_emoji):
        return chr(0x1f7e6)
    return discord_emoji


def _sort_sound_effect_name_matches(partial: str, sfx_name: str) -> int:
    """Returns a lower value for closer matches."""
    exact = sfx_name.find(partial)
    if exact != -1:
        return exact

    ignored_case = sfx_name.lower().find(partial.lower())
    if ignored_case == -1:
        return -1
    return ignored_case + 0.5


def _strip_leading_emoji(sound_effect_name: str) -> str:
    if ' ' not in sound_effect_name:
        return sound_effect_name
    return sound_effect_name.split(' ', 1)[0]


class BasicSoundEffectButton(discord.ui.Button):

    def __init__(self, sfx: SoundEffect):
        super().__init__(style=discord.ButtonStyle.grey,
                         label=sfx.name,
                         emoji=sfx.emoji)
        self.sfx = sfx

    async def callback(self, interaction: discord.Interaction):
        assert self.view is not None
        await self.sfx.play_for(interaction.user)
        await interaction.response.edit_message(view=self.view)


def add_sound_effect_commands(bot: BababooeyBot):

    sfx_cache = {sfx.name: sfx for sfx in _read_sfx_data()}

    def _locate_sfx(mangled_name: str) -> SoundEffect | None:
        name = mangled_name
        if name not in sfx_cache:
            # Sometimes the leading emoji comes through sometimes it doesn't.
            name = _strip_leading_emoji(mangled_name)
            # If it's still not a valid name give up.
            if name not in sfx_cache:
                return None
        return sfx_cache[name]

    async def _autocomplete_sound_effect_name(
            interaction: discord.Interaction,
            partial_sound: str) -> list[app_commands.Choice[str]]:
        partial_sound_lower = partial_sound.lower()
        res = []
        for name, sfx in sfx_cache.items():
            if partial_sound_lower in name.lower():
                res.append(sfx)

        res.sort(key=lambda sfx: _sort_sound_effect_name_matches(
            partial_sound, sfx.name))
        return [
            app_commands.Choice(
                name=f'{_unicode_safe_emoji(sfx.emoji)} {sfx.name}',
                value=sfx.name) for sfx in res[0:25]
        ]

    # user.id -> discord.Interaction
    previous_x_interaction = {}

    @bot.tree.command()
    @app_commands.describe(search='Look for a sound effect by name or tags.')
    @app_commands.autocomplete(search=_autocomplete_sound_effect_name)
    async def x(interaction: discord.Interaction, search: str):
        """Quick alias for the sound/ command."""
        sfx = _locate_sfx(search)
        if sfx is None:
            await interaction.response.send_message(
                f'I don\'t know a sound effect by the name of `{search}`.')
            return

        await sfx.play_for(interaction.user)
        view = discord.ui.View()
        view.add_item(BasicSoundEffectButton(sfx))
        await interaction.response.send_message(view=view, ephemeral=True)
        if interaction.user.id in previous_x_interaction:
            await previous_x_interaction[interaction.user.id
                                        ].delete_original_response()
        previous_x_interaction[interaction.user.id] = interaction

    @bot.tree.command()
    @app_commands.describe(search='Look for a sound effect by name or tags.')
    @app_commands.autocomplete(search=_autocomplete_sound_effect_name)
    async def edit_sound(
        interaction: discord.Interaction,
        search: str,
    ):
        """Edit a sound effect."""
        sfx = _locate_sfx(search)
        if sfx is None:
            await interaction.response.send_message(
                f'I don\'t know a sound effect by the name of `{search}`.')
            return
        await interaction.response.send_message(
            embed=sfx.details_embed(), view=SoundEffectDetailButtons(sfx))

    @bot.tree.command()
    async def soundboard(interaction: discord.Interaction):
        views = make_soundboard_views(list(sfx_cache.values()))
        first_view = views.pop(0)
        # Respond to the interaciton with the first message.
        await interaction.response.send_message(view=first_view)

        # Send the rest of the messages.
        for view in views:
            await interaction.channel.send(view=view)
