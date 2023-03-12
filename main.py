import logging

import discord
from racket import RacketBot

from bababooey import setup_logging, setup_db
from bababooey.cogs import BababooeyCog
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
    bot = RacketBot(intents=intents, guild_ids=GUILD_IDS)

    _log.info('Adding sound effect commands.')
    bot.add_cog(BababooeyCog(bot))

    _log.info('Starting the bot.')
    # Set the log_handler to avoid double logging settup.
    bot.run(BOT_TOKEN, log_handler=None)


if __name__ == '__main__':
    main()