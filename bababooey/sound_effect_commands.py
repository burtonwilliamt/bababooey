import shelve

import discord
from discord import app_commands

from bababooey import BababooeyBot, SoundEffect, play_sfx
from bababooey.ui import make_soundboard_views, SoundEffectDetailButtons, sound_effect_detail_embed


def _read_copied_sfx() -> list[SoundEffect]:
    s = shelve.open('data/copied_sfx')
    effects = s['sfx']
    s.close()
    return effects


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


def add_sound_effect_commands(bot: BababooeyBot):

    sfx_cache = {sfx.name: sfx for sfx in _read_copied_sfx()}

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
            app_commands.Choice(name=sfx.emoji + ' ' + sfx.name, value=sfx.name)
            for sfx in res[0:25]
        ]

    @bot.tree.command()
    @app_commands.autocomplete(sound_effect_name=_autocomplete_sound_effect_name)
    async def sound(interaction: discord.Interaction, sound_effect_name: str):
        sfx = _locate_sfx(sound_effect_name)
        if sfx is None:
            await interaction.response.send_message(
                f'I don\'t know a sound effect by the name of `{sound_effect_name}`.'
            )
            return
        await play_sfx(sfx, requester=interaction.user)
        await interaction.response.send_message(embed=sound_effect_detail_embed(sfx), view=SoundEffectDetailButtons(sfx))

    @bot.tree.command()
    async def soundboard(interaction: discord.Interaction):
        views = make_soundboard_views(list(sfx_cache.values()))
        first_view = views.pop(0)
        # Respond to the interaciton with the first message.
        await interaction.response.send_message(view=first_view)

        # Send the rest of the messages.
        for view in views:
            await interaction.channel.send(view=view)
