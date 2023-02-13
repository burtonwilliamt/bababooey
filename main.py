import logging

import discord

from bababooey import setup_logging, setup_db, BababooeyBot, add_admin_commands, add_sound_effect_commands
from settings import GUILD_IDS, BOT_TOKEN

_log = logging.getLogger(__name__)


def main():
    setup_logging()
    setup_db()

    intents = discord.Intents.default()
    intents.typing = False  # pylint: disable=assigning-non-slot
    intents.presences = False  # pylint: disable=assigning-non-slot
    intents.message_content = False  # pylint: disable=assigning-non-slot

    _log.info('Creating bot object.')
    bot = BababooeyBot(intents=intents, guild_ids=GUILD_IDS)

    _log.info('Adding admin commands.')
    add_admin_commands(bot)

    _log.info('Adding sound effect commands.')
    add_sound_effect_commands(bot)

    _log.info('Starting the bot.')
    # Set the log_handler to avoid double logging settup.
    bot.run(BOT_TOKEN, log_handler=None)


if __name__ == '__main__':
    main()