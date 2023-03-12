import logging

import racket

from bababooey import setup_db
from bababooey.cogs import BababooeyCog
from settings import GUILD_IDS, BOT_TOKEN

_log = logging.getLogger(__name__)


def main():
    setup_db()

    racket.run_cog(BababooeyCog, guilds=GUILD_IDS, token=BOT_TOKEN)


if __name__ == '__main__':
    main()