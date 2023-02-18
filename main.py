import logging

import discord

from bababooey import setup_logging, setup_db, BababooeyBot
from bababooey.cogs import AdminCog, BababooeyCog
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
    bot.add_cog(AdminCog(bot))

    _log.info('Adding sound effect commands.')
    bot.add_cog(BababooeyCog(bot))

    _log.info('Starting the bot.')
    # Set the log_handler to avoid double logging settup.
    bot.run(BOT_TOKEN, log_handler=None)


if __name__ == '__main__':
    main()