import os
import logging

import discord

# TODO: Filter the "ffmpeg process %s succefully terminated" messages.
# TODO: Figure out why there are format strings in the text log, and remove them.


def check_or_create_logs_dir():
    if not os.path.exists('logs/'):
        os.makedirs('logs/')


def setup_cli_logs():
    # Default logging to the CLI with color.
    cli_handler = logging.StreamHandler()
    cli_handler.setLevel(logging.INFO)
    # Need to set level=logging.DEBUG because that's the logger setting.
    # The cli_handler will filter out those LogRecords below logging.INFO
    discord.utils.setup_logging(handler=cli_handler, level=logging.DEBUG)


def setup_file_logs():
    # Add some file logging at a higher verbosity.
    file_handler = logging.FileHandler(filename='logs/discord.log',
                                       encoding='utf-8',
                                       mode='a')
    file_handler.setLevel(logging.INFO)
    discord.utils.setup_logging(handler=file_handler, level=logging.DEBUG)


def setup_logging():
    check_or_create_logs_dir()
    setup_cli_logs()
    setup_file_logs()